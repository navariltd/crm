import frappe
from frappe import _
import requests
from dataclasses import dataclass
from crm.integrations.yeastar.yeaster_utils import handle_error, headers


@frappe.whitelist(allow_guest=True)
def handle_incoming_call():
    data: dict[str, any] = frappe.request.get_json()
    if not data:
        frappe.log_error(
            "No data received in the incoming call webhook.",
            "Yeastar Incoming Call Error",
        )
        frappe.throw(_("No data received in the request."))

    members: list[dict[str, str]] = data.get("members", [])
    if not members or not isinstance(members, list):
        frappe.log_error(
            "Invalid or missing 'members' data in the incoming call webhook.",
            "Yeastar Incoming Call Error",
        )
        frappe.throw(_("Invalid data received in the request."))

    handle_request(members[0].get("inbound"))


def handle_request(member: dict[str, str]):

    payload = frappe._dict(
        {
            "channel_id": member.get("channel_id"),
            "from": member.get("from"),
            "to": member.get("to"),
        }
    )

    try:
        frappe.publish_realtime(
            "yeaster_incoming_call",
            message=payload,
            user=frappe.session.user,
        )
    except Exception as e:
        handle_error(
            _("Error publishing incoming call event: ") + str(e),
            "Yeastar Incoming Call Error",
        )


@frappe.whitelist()
def respond_to_call(channel_id: str, action: str) -> dict[str, str | int]:

    request_url = "/call/{}_inbound?access_token={}".format(
        action,
        get_yeastar_settings().access_token,
    )
    url = url_generator(request_url)

    payload = {"channel_id": channel_id}

    try:
        response = requests.post(
            url=url,
            json=payload,
            headers=headers(),
        )

        response.raise_for_status()

        response = response.json()

        return response
    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(),
            f"{str(e)}",
        )
        frappe.throw(_("An error occurred while responding to the call."))


@dataclass
class CallPayload:
    caller: str | int
    callee: str | int
    auto_answer: str = "yes"


@frappe.whitelist(allow_guest=True)
def make_outgoing_call(
    callee: str | int, auto_answer: str = "yes"
) -> dict[str, str | int]:
    if not is_integration_enabled():
        frappe.throw(_("Please enable Yeastar integration settings to make calls."))
    endpoint = url_generator(
        f"/call/dial?access_token={get_yeastar_settings().access_token}"
    )

    frappe.set_user("Administrator")

    caller = frappe.db.get_value(
        "CRM Telephony Agent", {"user": frappe.session.user}, "yeastar_caller_id"
    )

    if not caller:
        frappe.throw(
            _("Please set Yeastar Caller ID in your CRM Telephony Agent settings.")
        )

    payload: CallPayload = CallPayload(
        caller=caller, callee=callee, auto_answer=auto_answer
    )
    return trigger_call(payload, endpoint)


def trigger_call(call_payload: CallPayload, endpoint: str) -> dict[str, str | int]:

    try:
        response = requests.post(
            url=endpoint,
            json=call_payload.__dict__,
            headers=headers(),
        )

        response.raise_for_status()

        response = response.json()

        error_code = response.get("errcode")

        if error_code != 0:
            if error_code == 10004:
                access_token = refresh_access_token()

                new_endpoint = url_generator(f"/call/dial?access_token={access_token}")

                return trigger_call(call_payload, new_endpoint)
            frappe.throw(_(f"Error triggering call: {response.get('errmsg')}"))

        return response
    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(),
            f"{str(e)}",
        )
        frappe.throw(_("An error occurred while triggering the call."))


def is_integration_enabled() -> bool:
    return frappe.db.get_single_value("CRM Yeastar Settings", "enabled", True)


def get_yeastar_settings() -> dict:
    return frappe.get_single("CRM Yeastar Settings")


def refresh_access_token() -> str:

    request_url = url_generator("/refresh_token")
    refresh_token = get_yeastar_settings().refresh_token
    if not refresh_token:
        frappe.throw(_("Refresh token is missing. Please re-authenticate."))

    payload = {"refresh_token": refresh_token}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url=request_url, json=payload, headers=headers)

        response.raise_for_status()

        response = response.json()

        if response and response.get("access_token"):
            settings = get_yeastar_settings()
            settings.access_token = response.get("access_token")
            settings.refresh_token = response.get("refresh_token")
            settings.save()
            frappe.db.commit()

            return settings.access_token

    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(),
            f"Yeastar CRM: Access Token Refresh Error: {str(e)}",
        )
        return False


def url_generator(path: str) -> str:
    base_url = get_yeastar_settings().request_url
    if not base_url:
        frappe.throw(_("Yeastar base URL is not configured."))

    return f"{base_url}{path}"

import frappe
from frappe import _


def headers() -> dict[str, str]:
    return {"Content-Type": "application/json", "User-Agent": "OpenAPI"}


def handle_error(error_message: str) -> None:
    frappe.log_error(
        frappe.get_traceback(),
        f"{error_message}",
    )
    frappe.throw(_("An error occurred while handling the incoming call."))

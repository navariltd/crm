# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json
from frappe import _
from crm.integrations.yeastar.yeaster_utils import handle_error, headers


class CRMYeastarSettings(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        access_token: DF.Data | None
        enabled: DF.Check
        password: DF.Data | None
        refresh_token: DF.Data | None
        request_url: DF.Data | None
        username: DF.Data | None
    # end: auto-generated types
    pass

    def validate(self):
        self.get_access_token()

    def get_access_token(self) -> None:

        payload = {"username": self.username, "password": self.password}
        url = f"{self.request_url}/get_token"

        if self.enabled:
            try:

                response = requests.post(
                    url,
                    data=json.dumps(payload),
                    headers=headers(),
                )

                response = response.json()

                if response.get("errcode") != 0:
                    handle_error(f"Error fetching access token: {response}")

                self.access_token = response.get("access_token")
                self.refresh_token = response.get("refresh_token")
                frappe.msgprint(_("Access token fetched successfully."))

            except Exception as e:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Yeastar CRM: Access Token Fetch Error: {str(e)}",
                )
                frappe.throw(f"Error while fetching access token: {str(e)}")

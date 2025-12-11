# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json
from frappe import _


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
        headers = {"Content-Type": "application/json", "User-Agent": "OpenAPI"}

        if self.enabled:
            try:

                response = requests.post(
                    url,
                    data=json.dumps(payload),
                    headers=headers,
                )

                response = response.json()

                if response.get("errcode") != 0:
                    frappe.log_error(
                        frappe.get_traceback(),
                        f"Yeastar CRM: Access Token Fetch Error {response}",
                    )
                    frappe.throw(_("An error occured while fetching access token."))

                self.access_token = response.get("access_token")
                self.refresh_token = response.get("refresh_token")
                frappe.msgprint(_("Access token fetched successfully."))

            except Exception as e:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Yeastar CRM: Access Token Fetch Error: {str(e)}",
                )
                frappe.throw(f"Error while fetching access token: {str(e)}")

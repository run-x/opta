import os
import platform
import random
import string
import sys
import time
from typing import Optional

import requests
from getmac import get_mac_address
from git.config import GitConfigParser

from opta.constants import VERSION
from opta.utils import safe_run


class AmplitudeClient:
    UPDATE_SECRET_EVENT = "UPDATE_SECRET"
    VIEW_SECRET_EVENT = "VIEW_SECRET"
    START_GEN_EVENT = "START_GEN"
    PLAN_EVENT = "PLAN"
    APPLY_EVENT = "APPLY"
    DEBUGGER_EVENT = "DEBUGGER_START"
    VALID_EVENTS = [
        UPDATE_SECRET_EVENT,
        START_GEN_EVENT,
        APPLY_EVENT,
        PLAN_EVENT,
        DEBUGGER_EVENT,
    ]

    def __init__(self) -> None:
        self.api_key = "751db5fc75ff34f08a83381f4d54ead6"
        self.user_id = GitConfigParser().get_value("user", "email", "no_user")
        self.device_id = get_mac_address()
        self.session_id = int(time.time() * 1000)
        self.os_name = os.name
        self.platform = platform.system()
        self.os_version = platform.version()

    @safe_run
    def send_event(
        self,
        event_type: str,
        event_properties: Optional[dict] = None,
        user_properties: Optional[dict] = None,
    ) -> None:
        if hasattr(sys, "_called_from_test"):
            print("Not sending amplitude cause we think we're in a pytest")
            return
        event_properties = event_properties or {}
        user_properties = user_properties or {}
        insert_id = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        if event_type not in self.VALID_EVENTS:
            raise Exception(f"Invalid event type: {event_type}")
        body = {
            "api_key": self.api_key,
            "events": [
                {
                    "user_id": self.user_id,
                    "device_id": self.device_id,
                    "event_type": event_type,
                    "event_properties": event_properties,
                    "user_properties": user_properties,
                    "app_version": VERSION,
                    "platform": self.platform,
                    "os_name": self.os_name,
                    "os_version": self.os_version,
                    "insert_id": insert_id,
                    "session_id": self.session_id,
                }
            ],
        }
        headers = {"Content-Type": "application/json", "Accept": "*/*"}
        r = requests.post(
            "https://api2.amplitude.com/2/httpapi", params={}, headers=headers, json=body
        )
        if r.status_code != requests.codes.ok:
            raise Exception(
                "Hey, we're trying to send some analytics over to our devs for the "
                f"product usage and we got a {r.status_code} response back. Could "
                "you pls email over to our dev team about this and tell them of the "
                f"failure with the aforementioned code and this response body: {r.text}"
            )


amplitude_client = AmplitudeClient()

# new-module-api

from __future__ import annotations

from typing import List, Optional

from opta.exceptions import UserErrors

from ..provider import ProviderConfig


class AWSProviderConfig(ProviderConfig):
    def __init__(self, region: str) -> None:
        self.region = region
        self.account_ids: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, raw: dict) -> AWSProviderConfig:
        try:
            region = raw["region"]
        except KeyError:
            raise UserErrors("AWS region must be provided when using the AWS provider")

        p = cls(region)

        account_ids = raw.get("account_id")
        if isinstance(account_ids, list):
            p.account_ids = [str(id) for id in account_ids]
        elif account_ids:
            p.account_ids = [str(account_ids)]

        return p

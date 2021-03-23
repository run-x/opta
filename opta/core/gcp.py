from typing import Optional, Tuple

from google.auth import default
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError

from opta.exceptions import UserErrors


class GCP:
    project_id: Optional[str] = None
    credentials: Optional[Credentials] = None

    @classmethod
    def get_credentials(cls) -> Tuple[Credentials, str]:
        if cls.project_id is None or cls.credentials is None:
            try:
                cls.credentials, cls.project_id = default()
            except DefaultCredentialsError:
                raise UserErrors(
                    "Couldn't find default google credentials to use, pls run "
                    "`https://googleapis.dev/python/google-api-core/latest/auth.html#overview`"
                )
            except GoogleAuthError as e:
                raise UserErrors(*e.args)
        return cls.credentials, cls.project_id  # type: ignore

class UserErrors(Exception):
    """These are errors caused by improper usage or configuration and thus not surfaced to sentry"""


class MissingState(UserErrors):
    """These are errors caused by trying to fetch a terraform state which did not exist remotely."""

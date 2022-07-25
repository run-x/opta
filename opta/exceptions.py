class UserErrors(Exception):
    """These are errors caused by improper usage or configuration"""


class AzureNotImplemented(UserErrors):
    """These are errors where we have common features which are not developed for Azure"""


class LocalNotImplemented(UserErrors):
    """These are errors where we have common features which are not supported/developed for Local."""


class MissingState(UserErrors):
    """These are errors caused by trying to fetch a terraform state which did not exist remotely."""

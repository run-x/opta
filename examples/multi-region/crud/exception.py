from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data["status_code"] = response.status_code
        respomce.data["detail"] = "Write call happened on Read only Instance of the DB"

    return response

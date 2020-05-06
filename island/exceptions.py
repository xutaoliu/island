from rest_framework.views import exception_handler
from rest_framework.exceptions import *
from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'


def island_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, Http404):
        exc = NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = PermissionDenied()

    if response is not None:
        response.data['code'] = exc.get_codes()

    return response

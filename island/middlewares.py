import pytz
from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.headers.get('TZ', None)
        try:
            tz = pytz.timezone(tzname)
        except pytz.UnknownTimeZoneError:
            tz = None
        with timezone.override(tz):
            return self.get_response(request)

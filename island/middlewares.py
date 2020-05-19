import pytz
from django.utils import timezone
from django.core.cache import cache
from island import settings
from system.models import BlockedAddress
from django.views.defaults import permission_denied
import logging

suslogger = logging.getLogger('middleware.suspicious')


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


class SuspiciousExceptionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        for ip in BlockedAddress.objects.all().values_list('ip', flat=True):
            cache.set(f'island/blocked/{ip}', True)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def __call__(self, request):
        ip = self.get_client_ip(request)
        if not settings.DEBUG and cache.get(f'island/blocked/{ip}'):
            return permission_denied(request, Exception('You are blocked due to suspicious operations.'))
        response = self.get_response(request)
        if 400 <= response.status_code < 500:
            key = f'island/suspicious/{ip}'
            cache.set(key, 0, nx=True)
            cache.incr(key)
            cache.expire(key, timeout=settings.SUSPICIOUS_BLOCK_TIMEOUT)
            if cache.get(key, 0) >= settings.SUSPICIOUS_BLOCK_FREQUENCY:
                BlockedAddress.objects.get_or_create(ip=ip)
                cache.set(f'island/blocked/{ip}', True)
                cache.delete(key)
        return response

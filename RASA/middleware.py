from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import redis

from RASA.views import session_storage

User = get_user_model()


session_storage = redis.from_url(getattr(settings, "REDIS_URL", "redis://localhost:6379"), decode_responses=True)

class SessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ssid = request.COOKIES.get("session_id")
        if not ssid:
            return  # гость

        username = session_storage.get(ssid)

        # Если decode_responses=False — username может быть bytes
        if isinstance(username, bytes):
            try:
                username = username.decode("utf-8")
            except Exception:
                username = None

        if not username:
            request.user = AnonymousUser()
            return

        user = User.objects.filter(username=username).first()
        if user:
            request.user = user
        else:
            request.user = AnonymousUser()

class DisableCSRFMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)
        response = self.get_response(request)
        return response

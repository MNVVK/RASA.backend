from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

from RASA.views import session_storage

User = get_user_model()


class SessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ssid = request.COOKIES.get("session_id")
        if ssid:
            username = session_storage.get(ssid)
            if username:
                username = username.decode('utf-8')
                request.user = User.objects.filter(username=username).first()
            else:
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()

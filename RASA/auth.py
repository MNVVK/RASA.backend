# RASA/auth.py
from __future__ import annotations

from typing import Optional, Tuple

import redis
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


def _get_redis():
    """
    Создаём клиент по URL из ENV.
    decode_responses=True — чтобы получать str, а не bytes.
    """
    url = getattr(settings, "REDIS_URL", None)
    if not url:
        # Нет Redis — считаем, что аутентификации по cookie нет.
        # Возвращаем None, чтобы DRF попробовал следующие authenticators.
        return None
    return redis.from_url(url, decode_responses=True)


class RedisCookieAuthentication(BaseAuthentication):
    """
    DRF-аутентификатор, который берёт cookie `session_id`,
    смотрит username в Redis и подставляет request.user.

    Используется совместно с IsAuthenticated/IsAuthenticatedOrReadOnly.
    Если cookie нет или ключ в Redis не найден — возвращаем None,
    тогда DRF перейдёт к следующим authenticators (Session/Basic).
    """

    cookie_name = "session_id"

    def authenticate(self, request) -> Optional[Tuple[User, None]]:
        # 1) достаём cookie
        ssid = request.COOKIES.get(self.cookie_name)
        if not ssid:
            return None  # гость — пусть решают другие authenticators

        # 2) коннект к Redis
        r = _get_redis()
        if r is None:
            return None

        # 3) вытаскиваем username
        try:
            username = r.get(ssid)
        except Exception:
            # Redis недоступен — не валим запрос 500, а просто пропускаем
            return None

        if not username:
            # нет записи в Redis — не аутентифицируем
            return None

        # 4) ищем пользователя в БД
        user = User.objects.filter(username=username).first()
        if not user:
            # в редисе был мусор/устаревшая сессия
            # можно вернуть None, но явная ошибка понятнее при ручном дебаге
            raise AuthenticationFailed("User for this session not found")

        # 5) успех
        return (user, None)

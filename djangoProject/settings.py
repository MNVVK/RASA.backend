"""
Django settings for djangoProject project.
"""

import os
from pathlib import Path

# ---------- Base ----------
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------- Helpers ----------
def env(name: str, default=None, cast=str):
    """
    Простая обёртка для чтения переменных окружения.
    Пример: env("DEBUG", "False", cast=bool)
    """
    v = os.getenv(name, default)
    if v is None:
        return None
    if cast is bool:
        return str(v).lower() in ("1", "true", "yes", "on")
    return cast(v)


# ---------- Security ----------
SECRET_KEY = env("DJANGO_SECRET_KEY", "change-me")  # берём из ENV
DEBUG = env("DJANGO_DEBUG", "False", cast=bool)     # False по умолчанию на проде

ALLOWED_HOSTS = [h.strip() for h in env("ALLOWED_HOSTS", "*").split(",")]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in env("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]


# ---------- Apps ----------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "RASA.apps.RasaConfig",
    "rest_framework",
    "drf_yasg",
]

# ---------- Middleware ----------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "RASA.middleware.SessionMiddleware",
]

ROOT_URLCONF = "djangoProject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "RASA", "templates", "RASA")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ]
}

WSGI_APPLICATION = "djangoProject.wsgi.application"


# ---------- Database (Postgres on Render) ----------
# Значения берём из переменных окружения:
# POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_HOST / POSTGRES_PORT
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "rasa"),
        "USER": env("POSTGRES_USER", "postgres"),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        # Если вдруг используешь External Database URL с требованием TLS:
        # "OPTIONS": {"sslmode": "require"},
    }
}


# ---------- Password validation ----------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------- i18n ----------
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True


# ---------- Static ----------
STATIC_URL = "/static/"
# Если будешь собирать статику на проде, раскомментируй и укажи путь:
# STATIC_ROOT = BASE_DIR / "staticfiles"


# ---------- Default PK ----------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------- MinIO / S3 (берём из ENV) ----------
MINIO_ENDPOINT = env("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = env("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = env("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_NAME = env("MINIO_BUCKET_NAME", "rasa")
MINIO_SECURE = env("MINIO_SECURE", "False", cast=bool)
MINIO_BASE_URL = env("MINIO_BASE_URL", f"http://{MINIO_ENDPOINT}")


# ---------- Redis ----------
REDIS_HOST = env("REDIS_HOST", "localhost")
REDIS_PORT = int(env("REDIS_PORT", "6379"))
# Если у Redis есть пароль:
REDIS_PASSWORD = env("REDIS_PASSWORD", "")


# ---------- Custom User ----------
AUTH_USER_MODEL = "RASA.CustomUser"

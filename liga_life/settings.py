import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")


# ==========================
# Core
# ==========================
SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esta-clave-en-produccion")
DEBUG = env_bool("DEBUG", default=True)

# En Render normalmente conviene pasar esto como env:
# ALLOWED_HOSTS="liga-life.onrender.com,localhost,127.0.0.1"
_allowed = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,.onrender.com")
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]

# CSRF (para forms en Render)
# CSRF_TRUSTED_ORIGINS="https://liga-life.onrender.com"
_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000,https://*.onrender.com")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(",") if o.strip()]

# Render/Reverse proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# ==========================
# Apps
# ==========================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "inscripciones",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "liga_life.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "liga_life.wsgi.application"


# ==========================
# Database
# ==========================
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True


# ==========================
# Static / Media
# ==========================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = []
static_dir = BASE_DIR / "static"
if static_dir.exists():
    STATICFILES_DIRS.append(static_dir)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# ==========================
# Security (solo prod)
# ==========================
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Tema admin
DJANGO_ADMIN_FORCE_THEME = "light"

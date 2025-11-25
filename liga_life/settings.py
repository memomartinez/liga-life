import os
from pathlib import Path

import dj_database_url  # 👈 IMPORTANTE

BASE_DIR = Path(__file__).resolve().parent.parent

# En local, si no hay variable de entorno, usa esta clave.
SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esta-clave-en-produccion")

# En local seguirá True. En Render pondremos DEBUG=False.
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://*.onrender.com",
]

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
    "whitenoise.middleware.WhiteNoiseMiddleware",  # para servir estáticos
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


# ================== BASE DE DATOS ==================

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


# ================== STATIC / MEDIA ==================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Solo agregar STATICFILES_DIRS si la carpeta existe (para evitar error en Render)
STATICFILES_DIRS = []
static_dir = BASE_DIR / "static"
if static_dir.exists():
    STATICFILES_DIRS.append(static_dir)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# WhiteNoise: compresión + hash para producción
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# 👇 Forzamos tema claro en el admin para evitar el bug de Render
DJANGO_ADMIN_FORCE_THEME = "light"

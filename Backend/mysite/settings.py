import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or "dev-insecure-troque-em-producao"
DEBUG = os.environ.get("DEBUG", "False") == "True"


def _lista(nome, padrao=""):
    return [v.strip() for v in os.environ.get(nome, padrao).split(",") if v.strip()]


ALLOWED_HOSTS = _lista("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "acoes",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mysite.urls"
WSGI_APPLICATION = "mysite.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],  # base.html e os templates do admin
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# PostgreSQL se DATABASE_URL existir (Render), senão SQLite
DATABASES = {"default": dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600)}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]  # static/css/tema.css
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Origens do front (separadas por vírgula), ex.: https://meufront.onrender.com
CORS_ALLOWED_ORIGINS = _lista("CORS_ALLOWED_ORIGINS", "http://localhost:3000", "https://hackathon-frontend-production-3958bdc8.up.railway.app")
CSRF_TRUSTED_ORIGINS = _lista("CSRF_TRUSTED_ORIGINS")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": []
}

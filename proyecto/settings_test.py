"""Configuración exclusiva para pruebas locales; nunca usar para desplegar."""

from .settings import *  # noqa: F403

# Reemplaza la conexión completa, incluso si existe DATABASE_URL en el entorno.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
SECRET_KEY = "test-only-key-for-blogrecetapy-isolated-local-tests"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
STORAGES = {
    **STORAGES,  # noqa: F405
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEBUG = False
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

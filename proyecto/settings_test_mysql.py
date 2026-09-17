"""Configuración de pruebas de integración contra un MySQL desechable."""

import os

from .settings_test import *  # noqa: F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("MYSQL_DATABASE", "blogrecetapy_ci"),
        "USER": os.environ.get("MYSQL_USER", "root"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD", "test-password"),
        "HOST": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "PORT": os.environ.get("MYSQL_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
        "TEST": {
            "NAME": os.environ.get("MYSQL_TEST_DATABASE", "test_blogrecetapy_ci"),
        },
    }
}

"""Configuración de desarrollo."""
from .base import *  # noqa: F403

DEBUG = True

# En desarrollo no hay HTTPS: las cookies viajan sin flag Secure
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

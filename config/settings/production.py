"""Configuración de producción."""
from .base import *  # noqa: F403
from .base import env

DEBUG = False

# Solo HTTPS en producción
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Confía en el header del proxy/balanceador para detectar HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ------------------------------------------------------------------
# Archivos estáticos: WhiteNoise con compresión + hash en el nombre
# (cache-busting real; reemplaza al tag de desarrollo static_v).
# ------------------------------------------------------------------
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# ------------------------------------------------------------------
# Correo (SMTP). Configurable por variables de entorno.
# ------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
SERVER_EMAIL = DEFAULT_FROM_EMAIL  # noqa: F405

# Quién recibe los errores 500 por correo
ADMINS = [('Soporte', email) for email in env.list('ADMIN_EMAILS', default=[])]
MANAGERS = ADMINS

# ------------------------------------------------------------------
# Logging: consola + archivo rotativo; errores 500 al correo de admins.
# Nunca registres datos sensibles (ver SENSITIVE_FIELDS en base.py).
# ------------------------------------------------------------------
LOG_DIR = BASE_DIR / 'logs'  # noqa: F405
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'archivo': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'app.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'level': 'ERROR',
        },
    },
    'root': {'handlers': ['console', 'archivo'], 'level': 'INFO'},
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'archivo'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Intentos de login y bloqueos por fuerza bruta
        'axes': {'handlers': ['console', 'archivo'], 'level': 'WARNING', 'propagate': False},
    },
}

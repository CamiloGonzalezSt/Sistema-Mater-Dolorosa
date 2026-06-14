"""
Configuración base del proyecto Mater Dolorosa.
Compartida por todos los entornos (development / production).
"""
from datetime import timedelta
from pathlib import Path

import environ

# BASE_DIR = raíz del proyecto (contiene manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# ------------------------------------------------------------------
# Aplicaciones
# ------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'simple_history',
    'axes',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.web_publica',
    'apps.academico',
    'apps.alumnos',
    'apps.profesores',
    'apps.asistencia',
    'apps.calificaciones',
    'apps.convivencia',
    'apps.contabilidad',
    'apps.comunicaciones',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Sirve archivos estáticos comprimidos y cacheables en producción
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Registra qué usuario hizo cada cambio en los modelos auditados (Calificacion)
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.notificaciones',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ------------------------------------------------------------------
# Base de datos: MySQL 8.x (InnoDB · utf8mb4)
# ------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='127.0.0.1'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        # Reutiliza conexiones a la BD (perf en producción)
        'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=60),
    }
}

# Límite de tamaño de peticiones/subidas (defensa básica)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------------------------------------------
# Autenticación y RBAC
# ------------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.CustomUser'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/panel/'
LOGOUT_REDIRECT_URL = '/'

DEFAULT_FROM_EMAIL = 'no-responder@materdolorosa.cl'
CONTACT_EMAIL = 'contacto@materdolorosa.cl'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ------------------------------------------------------------------
# django-axes: protección contra fuerza bruta en login
# ------------------------------------------------------------------
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_CALLABLE = None

# ------------------------------------------------------------------
# Internacionalización
# ------------------------------------------------------------------
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------
# Archivos estáticos y media
# ------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ------------------------------------------------------------------
# Seguridad (Ley 19.628 Chile + estándares COPPA)
# Los flags que exigen HTTPS se activan en production.py
# ------------------------------------------------------------------
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600          # 1 hora — expiración agresiva
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# Campos sensibles — nunca en logs
SENSITIVE_FIELDS = ['rut', 'fecha_nacimiento', 'direccion', 'password']

"""
Django settings for misitio project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# --- CONFIGURACIÓN DE SEGURIDAD ---
SECRET_KEY = 'django-insecure-pwh^#i06-b9xu=2-9g_dcnvl$fzp+a93t6c4zc&wa3qbzcrfb*'

DEBUG = True

# Permitimos hosts locales y externos para las pruebas
ALLOWED_HOSTS = ['bibliotecajosue', '127.0.0.1', 'localhost', '*']


# --- DEFINICIÓN DE APLICACIONES ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Tus aplicaciones
    'gestion',
    # Librerías extra
    'rest_framework',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'misitio.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Aseguramos que busque en la carpeta 'templates' en la raíz
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'misitio.wsgi.application'


# --- BASE DE DATOS ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- VALIDACIÓN DE CONTRASEÑAS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- ARCHIVOS ESTÁTICOS (CSS, JS, IMÁGENES) ---
STATIC_URL = 'static/'
# Esto ayuda a que Django encuentre tu CSS neón en la raíz
STATICFILES_DIRS = [BASE_DIR / 'static']
# Carpeta donde se recolectarán los estáticos en producción
STATIC_ROOT = BASE_DIR / 'staticfiles'


# --- CONFIGURACIÓN DE CAMPOS ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- CONFIGURACIONES DE LOGIN / REDIRECCIÓN ---
# Solución al error NoReverseMatch: usamos el namespace 'gestion'
LOGIN_URL = 'gestion:ingresar'  
LOGIN_REDIRECT_URL = 'gestion:inicio'
LOGOUT_REDIRECT_URL = 'gestion:ingresar'


# --- REST FRAMEWORK (Para el Bodeguero y API) ---
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

# Mensajes de Bootstrap (opcional, mejora la visualización de alertas)
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}
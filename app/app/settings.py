"""
Django settings for app project.

Generated by 'django-admin startproject' using Django 4.2.13.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
from celery import Celery

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-5h5t!a&ffgr&(4hpi^bv-6jpg1qfwl1x6%p!(hrf3-)#+j+pte'

# Celery stuff
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
celery_app = Celery("app")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()


# Schedule a Bear
# app/settings.py
CELERY_BEAT_SCHEDULE = {
    "run-collect-metrics-every-minute": {
        "task": "dashboard.tasks.run_collect_metrics",
        "schedule": 60.0,  # Run every 60 seconds
    },
    "cache-docker-stats-every-10-seconds": {
        "task": "dashboard.tasks.update_docker_stats",
        "schedule": 30.0, 
    },
    "run-collect-nodes-every-10-seconds": {
        "task": "dashboard.tasks.collect_node_data",
        "schedule": 10.0, 
    },
    "check-nodes-status-every-8-seconds": {
        "task": "dashboard.tasks.ping_nodes",
        "schedule": 8.0,
    },
    "run-collect-logs-every-30-seconds": {
        "task": "dashboard.tasks.run_collect_logs",
        "schedule": 30.0,
    },
    "check-alert-rules-every-minute": {
        "task": "dashboard.tasks.check_alert_rules",
        "schedule": 10.0,  # every 60 seconds
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
CELERY_BROKER_URL = "redis://localhost:6379/0"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'dashboard',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app.middleware.LoginRequiredMiddleware',
    # 'django.contrib.auth.middleware.LoginRequiredMiddlewares',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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


ASGI_APPLICATION = 'app.asgi.application'
WSGI_APPLICATION = 'app.wsgi.application'

# AUTH/LOGIN

LOGIN_URL = '/login/'  # Redirect users to login if they're not authenticated
LOGIN_REDIRECT_URL = '/'  # Redirect after successful login
LOGOUT_REDIRECT_URL = '/login/'  # Redirect after logging out
# Session settings for "Stay Logged In" functionality
SESSION_COOKIE_AGE = 1209600  # Two weeks in seconds
SESSION_SAVE_EVERY_REQUEST = True  # Extend session with every request

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rpj',
        'USER': 'admin',
        'PASSWORD': 'admin',
        'HOST': 'localhost',  # or the IP address if it's a remote server
        'PORT': '5432',       # default PostgreSQL port
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'CET'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'

# STATICFILES_DIRS = [
#     BASE_DIR / "static",  # Create a 'static' folder at the root of your project
# ]
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Optional: Set session cache to use Redis
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

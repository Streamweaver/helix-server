"""
Django settings for HELIX server project.

Generated by 'django-admin startproject' using Django 3.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import json
import socket
import logging
import environ

from . import sentry
from helix.aws.secrets_manager import fetch_db_credentials_from_secret_arn

logger = logging.getLogger(__name__)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIRNAME = 'apps'
APPS_DIR = os.path.join(BASE_DIR, APPS_DIRNAME)

DEVELOPMENT_ENV = 'development'

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    ENABLE_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOST=list,
    DJANGO_SECRET_KEY=str,
    # S3 Optional Credentials
    AWS_S3_ACCESS_KEY_ID=(str, None),
    AWS_S3_SECRET_ACCESS_KEY=(str, None),
    AWS_S3_REGION=str,
    S3_BUCKET_NAME=str,
    # Redis URL
    DJANGO_CACHE_REDIS_URL=str,  # redis://redis:6379/1
    CELERY_BROKER_URL=str,  # redis://redis:6379/0
    CELERY_RESULT_BACKEND_URL=str,  # redis://redis:6379/1
    # -- Single Redis url (For copilot)
    ELASTI_CACHE_ADDRESS=str,
    ELASTI_CACHE_PORT=str,
    # DJANGO cookie conf
    SESSION_COOKIE_DOMAIN=str,  # .tools.idmdb.org
    CSRF_COOKIE_DOMAIN=str,   # .tools.idmdb.org
    CSRF_USE_SESSIONS=(bool, False),
    CSRF_TRUSTED_ORIGINS=(list, [  # TODO: CHECK IF THIS IS USED
        'media-monitoring.idmcdb.org',
        'https://media-monitoring.idmcdb.org',
        'http://media-monitoring.idmcdb.org',
        'https://idumap.idmcdb.org',
        'https://dev-idmc.datafriendlyspace.org',
        'https://idmc-website.dev.datafriendlyspace.org',
        'https://internal-displacement.org',
        'https://idmc-website-components.idmcdb.org',
    ]),
    # MISC
    DEFAULT_FROM_EMAIL=(str, 'contact@idmcdb.org'),
    FRONTEND_BASE_URL=str,
    HCAPTCHA_SECRET=str,
    HELIXDBCLUSTER_SECRET=(str, None),
    HELIXDBCLUSTER_SECRET_ARN=(str, None),
    HELIX_ENVIRONMENT=(str, DEVELOPMENT_ENV),
    POSTGRES_DB=str,
    POSTGRES_HOST=str,
    POSTGRES_PASSWORD=str,
    POSTGRES_PORT=(int, 5432),
    POSTGRES_USER=str,
    SEND_ACTIVATION_EMAIL=(bool, True),
    SENTRY_DSN=(str, None),
    SENTRY_SAMPLE_RATE=(float, 0.2),
    # Copilot
    COPILOT_ENVIRONMENT_NAME=(str, None),
    COPILOT_SERVICE_NAME=(str, None),
)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')
HELIX_ENVIRONMENT = env('COPILOT_ENVIRONMENT_NAME') or env('HELIX_ENVIRONMENT')
DEBUG = env('DJANGO_DEBUG')
logger.debug(f'\nServer running in {DEBUG=} mode.\n')

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOST')

IN_AWS_COPILOT_ECS = not not env('COPILOT_SERVICE_NAME')

# Application definition

LOCAL_APPS = [
    'contrib',
    'country',
    'users',
    'organization',
    'contact',
    'crisis',
    'event',
    'entry',
    'resource',
    'review',
    'extraction',
    'parking_lot',
    'contextualupdate',
    'report',
]

THIRD_PARTY_APPS = [
    'graphene_django',
    'rest_framework.authtoken',  # required by djoser
    'djoser',
    'corsheaders',
    'django_filters',
    'debug_toolbar',
    'graphene_graphiql_explorer',
    'graphiql_debug_toolbar',
    'rest_framework',
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_email',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_hotp',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
] + THIRD_PARTY_APPS + [
    # apps.users.apps.UsersConfig
    f'{APPS_DIRNAME}.{app}.apps.{"".join([word.title() for word in app.split("_")])}Config' for app in LOCAL_APPS
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'utils.middleware.HealthCheckMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ENABLE_DEBUG = env('ENABLE_DEBUG')
if ENABLE_DEBUG:
    MIDDLEWARE.append(
        # NOTE: DebugToolbarMiddleware will cause mutation to execute twice for the client, works fine with graphiql
        'utils.middleware.DebugToolbarMiddleware',
    )

if HELIX_ENVIRONMENT not in (DEVELOPMENT_ENV,):
    MIDDLEWARE.append('django.middleware.clickjacking.XFrameOptionsMiddleware')


if IN_AWS_COPILOT_ECS:
    _COPILOT_ELASTI_CACHE_URL = f"redis://{env('ELASTI_CACHE_ADDRESS')}:{env('ELASTI_CACHE_PORT')}"
    DJANGO_CACHE_REDIS_URL = f'{_COPILOT_ELASTI_CACHE_URL}/1'
    CELERY_BROKER_URL = f'{_COPILOT_ELASTI_CACHE_URL}/0'
    CELERY_RESULT_BACKEND = f'{_COPILOT_ELASTI_CACHE_URL}/2'
else:
    DJANGO_CACHE_REDIS_URL = env('DJANGO_CACHE_REDIS_URL')
    CELERY_BROKER_URL = env('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND_URL')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': DJANGO_CACHE_REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20
}

ROOT_URLCONF = 'helix.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'helix.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

if IN_AWS_COPILOT_ECS:
    DBCLUSTER_SECRET = (
        json.loads(env('HELIXDBCLUSTER_SECRET') or '{}') or
        fetch_db_credentials_from_secret_arn(env('HELIXDBCLUSTER_SECRET_ARN'))
    )
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            # in the workflow environment
            'NAME': DBCLUSTER_SECRET['dbname'],
            'USER': DBCLUSTER_SECRET['username'],
            'PASSWORD': DBCLUSTER_SECRET['password'],
            'HOST': DBCLUSTER_SECRET['host'],
            'PORT': DBCLUSTER_SECRET['port'],
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': env('POSTGRES_DB'),
            'USER': env('POSTGRES_USER'),
            'PASSWORD': env('POSTGRES_PASSWORD'),
            'HOST': env('POSTGRES_HOST'),
            'PORT': env('POSTGRES_PORT'),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
    {
        'NAME': 'apps.users.password_validation.MaximumLengthValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


AUTH_USER_MODEL = 'users.User'

# https://docs.graphene-python.org/projects/django/en/latest/settings/
GRAPHENE = {
    'ATOMIC_MUTATIONS': True,
    'SCHEMA': 'helix.schema.schema',
    'SCHEMA_OUTPUT': 'schema.json',  # defaults to schema.json,
    'SCHEMA_INDENT': 2,  # Defaults to None (displays all data on a single line)
    'MIDDLEWARE': [
        'helix.sentry.SentryMiddleware',
        'helix.auth.WhiteListMiddleware',
    ],
}

GRAPHENE_DJANGO_EXTRAS = {
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.PageGraphqlPaginationWithoutCount',
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 50,
    # 'CACHE_ACTIVE': True,
    # 'CACHE_TIMEOUT': 300    # seconds
}
if not DEBUG:
    GRAPHENE['MIDDLEWARE'].append('utils.middleware.DisableIntrospectionSchemaMiddleware')

AUTHENTICATION_BACKEND = [
    'django.contrib.auth.backends.ModelBackend',
]

DJOSER = {
    'ACTIVATION_URL': '#/activate/{uid}/{token}',
    'SEND_ACTIVATION_EMAIL': env('SEND_ACTIVATION_EMAIL'),
}
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django_ses.SESBackend'

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# https://docs.djangoproject.com/en/3.1/ref/settings/#std:setting-APPEND_SLASH
APPEND_SLASH = False

#################
# DEBUG TOOLBAR #
#################

INTERNAL_IPS = [
    '127.0.0.1',
]

# https://github.com/flavors/django-graphiql-debug-toolbar/#installation
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS += [ip[:-1] + '1' for ip in ips]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_LOCATION = 'static'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
MEDIAFILES_LOCATION = 'media'

# Django storage
if 'S3_BUCKET_NAME' in os.environ:
    DEFAULT_FILE_STORAGE = 'helix.s3_storages.MediaStorage'
    STATICFILES_STORAGE = 'helix.s3_storages.StaticStorage'

    AWS_STORAGE_BUCKET_NAME = env('S3_BUCKET_NAME')
    AWS_S3_ACCESS_KEY_ID = env('AWS_S3_ACCESS_KEY_ID')
    if AWS_S3_ACCESS_KEY_ID:
        AWS_S3_SECRET_ACCESS_KEY = env('AWS_S3_SECRET_ACCESS_KEY')
        AWS_S3_REGION_NAME = env('AWS_S3_REGION')

    # NOTE: s3 bucket is public
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    AWS_IS_GZIPPED = True
    GZIP_CONTENT_TYPES = [
        'text/css',
        'text/javascript',
        'application/javascript',
        'application/x-javascript',
        'image/svg+xml',
        'application/json',
        'application/pdf',
    ]

# Sentry Config
SENTRY_DSN = env('SENTRY_DSN')

if SENTRY_DSN:
    SENTRY_CONFIG = {
        'dsn': SENTRY_DSN,
        'send_default_pii': True,
        # TODO: Move server to root directory to get access to .git
        # 'release': sentry.fetch_git_sha(os.path.dirname(BASE_DIR)),
        'environment': HELIX_ENVIRONMENT,
        'traces_sample_rate': env('SENTRY_SAMPLE_RATE'),
        'debug': DEBUG,
        'tags': {
            'site': ALLOWED_HOSTS[0],
        },
    }
    sentry.init_sentry(
        app_type='server',
        **SENTRY_CONFIG,
    )

RESOURCE_NUMBER = GRAPHENE_DJANGO_EXTRAS['MAX_PAGE_SIZE']
RESOURCEGROUP_NUMBER = GRAPHENE_DJANGO_EXTRAS['MAX_PAGE_SIZE']
FIGURE_NUMBER = GRAPHENE_DJANGO_EXTRAS['MAX_PAGE_SIZE']

# CELERY

# NOTE: These queue names must match the worker container command
# CELERY_DEFAULT_QUEUE = LOW_PRIO_QUEUE = env('LOW_PRIO_QUEUE_NAME', 'celery_low')
# HIGH_PRIO_QUEUE = env('HIGH_PRIO_QUEUE_NAME', 'celery_high')

# CELERY ROUTES
# CELERY_ROUTES = {
#     'apps.users.tasks.send_email': {'queue': HIGH_PRIO_QUEUE},
#     'apps.entry.tasks.generate_pdf': {'queue': HIGH_PRIO_QUEUE},
#     # LOW
#     'apps.contrib.tasks.kill_all_old_excel_exports': {'queue': LOW_PRIO_QUEUE},
#     'apps.contrib.tasks.kill_all_long_running_previews': {'queue': LOW_PRIO_QUEUE},
#     'apps.contrib.tasks.kill_all_long_running_report_generations': {'queue': LOW_PRIO_QUEUE},
#     'apps.report.tasks.trigger_report_generation': {'queue': LOW_PRIO_QUEUE},
#     'apps.contrib.tasks.generate_excel_file': {'queue': LOW_PRIO_QUEUE},
# }

# end CELERY

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# WHITELIST following nodes from authentication checks
GRAPHENE_NODES_WHITELIST = (
    'login',
    'logout',
    'activate',
    'register',
    'me',
    'generateResetPasswordToken',
    'resetPassword',
    # __ double underscore nodes
    '__schema',
    '__type',
    '__typename',
)

# CAPTCHA
HCAPTCHA_SECRET = env('HCAPTCHA_SECRET')

# It login attempts exceed MAX_LOGIN_ATTEMPTS, users will need to enter captcha
# to login
MAX_LOGIN_ATTEMPTS = 3

# If login attempts exceed MAX_CAPTCHA_LOGIN_ATTEMPTS , users will need to wait LOGIN_TIMEOUT seconds

MAX_CAPTCHA_LOGIN_ATTEMPTS = 10
LOGIN_TIMEOUT = 10 * 60  # seconds

# Frontend base url for email button link
FRONTEND_BASE_URL = env('FRONTEND_BASE_URL')

# https://docs.djangoproject.com/en/3.2/ref/settings/#password-reset-timeout
PASSWORD_RESET_TIMEOUT = 15 * 60  # seconds
PASSWORD_RESET_CLIENT_URL = "{FRONTEND_BASE_URL}/reset-password/{{uid}}/{{token}}".format(
    FRONTEND_BASE_URL=FRONTEND_BASE_URL
)

# TASKS TIMEOUTS
OLD_JOB_EXECUTION_TTL = 72 * 60 * 60  # seconds
# staying in pending for too long will be moved to killed
EXCEL_EXPORT_PENDING_STATE_TIMEOUT = 5 * 60 * 60  # seconds
# staying in progress for too long will be moved to killed
EXCEL_EXPORT_PROGRESS_STATE_TIMEOUT = 10 * 60  # seconds

EXCEL_EXPORT_CONCURRENT_DOWNLOAD_LIMIT = 10

OTP_TOTP_ISSUER = 'IDMC'
OTP_HOTP_ISSUER = 'IDMC'
OTP_EMAIL_SENDER = DEFAULT_FROM_EMAIL
OTP_EMAIL_SUBJECT = 'IDMC OTP Token'
OTP_EMAIL_BODY_TEMPLATE_PATH = 'emails/otp.html'

TEMP_FILE_DIRECTORY = '/tmp/'

# Security Header configuration
SESSION_COOKIE_NAME = f'helix-{HELIX_ENVIRONMENT}-sessionid'
CSRF_COOKIE_NAME = f'helix-{HELIX_ENVIRONMENT}-csrftoken'
# # SECURE_BROWSER_XSS_FILTER = True
# # SECURE_CONTENT_TYPE_NOSNIFF = True
# # X_FRAME_OPTIONS = 'DENY'
# # CSP_DEFAULT_SRC = ["'self'"]
# # SECURE_REFERRER_POLICY = 'same-origin'
# if HELIX_ENVIRONMENT != DEVELOPMENT_ENV:
#     SESSION_COOKIE_NAME = f'__Secure-{SESSION_COOKIE_NAME}'
#     # SESSION_COOKIE_SECURE = True
#     # SESSION_COOKIE_HTTPONLY = True
#     # SECURE_HSTS_SECONDS = 30  # TODO: Increase this slowly
#     # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     # SECURE_HSTS_PRELOAD = True
#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#     # NOTE: Client needs to read CSRF COOKIE.
#     # CSRF_COOKIE_NAME = f'__Secure-{CSRF_COOKIE_NAME}'
#     # CSRF_COOKIE_SECURE = True
#     # CSRF_COOKIE_HTTPONLY = True


# https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-CSRF_USE_SESSIONS
CSRF_USE_SESSIONS = env('CSRF_USE_SESSIONS', 'False')
# https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-SESSION_COOKIE_DOMAIN
SESSION_COOKIE_DOMAIN = env('SESSION_COOKIE_DOMAIN')
# https://docs.djangoproject.com/en/3.2/ref/settings/#csrf-cookie-domain
CSRF_COOKIE_DOMAIN = env('CSRF_COOKIE_DOMAIN')

CSRF_TRUSTED_ORIGINS = [
    FRONTEND_BASE_URL,
    *env('CSRF_TRUSTED_ORIGINS'),
]

########
# CORS #
########

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    # LOCAL
    "http://localhost:3080",
    "http://127.0.0.1:3080",
    # OUTSIDE
    FRONTEND_BASE_URL,
    "https://media-monitoring.idmcdb.org/",
]

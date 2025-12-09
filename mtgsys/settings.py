from pathlib import Path
from decouple import config



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='your-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
# .env.prodのDEBUG値を読み込む
DEBUG = config('DEBUG', default=True, cast=bool)
BBB_FRONTEND_URL = config("BBB_FRONTEND_URL", default="http://example.com")
DJANGO_ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="example.com")
if not DEBUG:
    ALLOWED_HOSTS = [DJANGO_ALLOWED_HOSTS]
    CSRF_TRUSTED_ORIGINS = [BBB_FRONTEND_URL]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mtgsys',
    'django_celery_beat',
    'source.apps.SourceConfig',  # apps.py の AppConfig クラスを明示的に指定
    'debug_toolbar',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# セッションエンジンをデータベースに設定
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# セッションの有効期限を1時間に設定
SESSION_COOKIE_AGE = 3600
# ブラウザを閉じるとセッションが無効になるように設定
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

ROOT_URLCONF = 'mtgsys.urls'

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

WSGI_APPLICATION = 'mtgsys.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config("MYSQL_DATABASE", default="django-db"),  # db名
            'USER': config("MYSQL_USER", default="django"),
            'PASSWORD': config("MYSQL_PASSWORD", default="django-prod"),
            'HOST': 'db',
            'PORT': '3306',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config("MYSQL_DATABASE", default="django-db"),  # db名
            'USER': config("MYSQL_USER", default="django"),
            'PASSWORD': config("MYSQL_PASSWORD", default="django-prod"),
            'HOST': '127.0.0.1',
            'PORT': '3306',
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

LANGUAGE_CODE = 'ja'   ### en-us から ja に変更
# タイムゾーン
TIME_ZONE = 'Asia/Tokyo' 

USE_I18N = True

USE_TZ = True




# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# BBBサーバー情報
BBB_SERVER_URL = config("BBB_SERVER_URL", default="https://default-url.com/bigbluebutton/api")
BBB_SHARED_SECRET = config("BBB_SHARED_SECRET", default="default-shared-secret")
BBB_LOGOUT_URL = config("BBB_FRONTEND_URL", default="http://example.com") + "/tab-close/"
BBB_FRONTEND_URL = config("BBB_FRONTEND_URL", default="http://example.com")

AUTH_USER_MODEL = 'source.CustomUser'
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="http://example.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)

# celeryの設定 
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379'
    }
}
# Celery configurations
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZZER = 'json'

# 'amqp://guest:guest@localhost//'
# celeryを動かすための設定ファイル
if DEBUG:
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
else:
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0' 
CELERY_CACHE_BACKEND = "django-cache"
CELERY_RESULT_EXTENDED = True
CELERY_TASK_DEFAULT_QUEUE = 'celery'

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

INTERNAL_IPS = ['localhost',]
DEBUG_TOOLBAR_CONFIG = {
    # ツールバーを表示させる
    "SHOW_TOOLBAR_CALLBACK" : lambda request: True,
}

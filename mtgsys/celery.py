import os
from celery import Celery
from django.conf import settings

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mtgsys.settings")

# app: Celery = Celery("app")

# app.config_from_object("django.conf:settings", namespace="CELERY")  # type: ignore
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)  # type: ignore

import os
from celery import Celery

# Django の設定をロード
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mtgsys.settings')

app = Celery('mtgsys')

# 設定を Django から読み込む
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django のすべてのアプリケーションのタスクを自動的にロード
app.autodiscover_tasks()
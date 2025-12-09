from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError



class SourceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'source'
    def ready(self):
        from .tasks import setup_periodic_task
        try:
            setup_periodic_task()  # Celeryスケジュールタスクをセットアップ
        except (OperationalError, ProgrammingError):
            # 初回実行時にデータベースが準備できていない可能性があるのでスルー
            pass   



class BbbappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bbbapp'

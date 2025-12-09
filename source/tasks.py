# celeryのタスクを定義するファイル
from . import bbb_api_functions
from celery import shared_task
from datetime import timedelta
from django.utils.timezone import now
from django.core.mail import send_mail
from .models import *
from .send_html_bcc_email import send_html_bcc_email
from django.apps import apps
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.db import transaction
from django.utils import timezone
import json
from django.utils import timezone
from datetime import timezone as dt_timezone, timedelta

BEFORE_MINITE = 15  # メール送信の時間

@shared_task
def send_email_task(meeting_instance_id, participant_emails, kind):
    """
    Celery タスクとしてメール送信を実行
    """
    from .models import Meeting  # 遅延インポート（循環参照防止）
    meeting_instance = Meeting.objects.get(id=meeting_instance_id)
    send_html_bcc_email(meeting_instance, participant_emails, kind)

@shared_task
def send_meeting_reminder(meeting_id):
    Meeting = apps.get_model('source', 'Meeting')  # 遅延インポート
    Participant = apps.get_model('source', 'Participant')  # 遅延インポート
    try:
        meeting = Meeting.objects.get(id=meeting_id)

    except Meeting.DoesNotExist:
        print("meeting not found, id=", meeting_id)
        return    
    if meeting.date - now() > timedelta(minutes=BEFORE_MINITE):
        print("meeting not soon, id=", meeting_id)
        return  # すでにメールが送信済み
    participants = Participant.objects.filter(meeting=meeting)
    participants_emails = [participant.email for participant in participants]
    send_html_bcc_email(meeting, participants_emails, kind="remind")

@shared_task
# 会議室情報取得し、実施済みフラグを判定する
def organize_meetings():
    print("organize_meetings task started")
    # response = bbb_api_functions.get_meetings(request=None)
    # # Meeting.objectsの会議情報からresponseに含まれていない会議を抽出。会議情報のis_doneをTrueに更新。
    # meeting = Meeting.objects.exclude(meeting_id__in=[m['meetingID'] for m in response])
    # meeting.update(is_done=True)
    # for m in meeting:
    #     # 繰り返しフラグがtrueの場合に、次の会議予定を作成する。
    #     if m.is_recurring and not m.is_recurring_done:
    #         m.is_recurring_done = True
    #         m.save()
    #         # 会議作成APIを呼び出す
    #         mtg_id = str(uuid.uuid4())
    #         response = bbb_api_functions.create_meeting(
    #             mtg_id,
    #             m.meeting_name,
    #             m.guest,
    #             m.participants.all(),
    #             m.attendee_pw,
    #             m.moderator_pw,
    #             m.is_record,
    #             m.is_recurring,
    #             m.recurrence_days
    #         )
    #         createTime = response["createTime"]
    #         # DBに会議を登録
    #         next_meeting = Meeting(
    #             meeting_name = m.meeting_name,
    #             date = m.date + timedelta(days=m.recurrence_days),
    #             created_date = now(),
    #             creator = m.creator,
    #             meeting_id = mtg_id,
    #             attendee_pw = m.attendee_pw,
    #             moderator_pw = m.moderator_pw,
    #             is_record = m.is_record,
    #             guest = m.guest,
    #             full_name = m.creator,
    #             is_recurring = m.is_recurring,
    #             recurrence_days = m.recurrence_days,
    #             create_time = createTime
    #         )
    #         next_meeting.save()
    #         # DBに参加者を登録
    #         for participant in m.participants.all():
    #             Participant_instance = Participant(
    #                 meeting = next_meeting,
    #                 email = participant.email
    #             )
    #             Participant_instance.save()
    #         participant_emails = [participant.email for participant in m.participants.all()]
    #         # メール送信関数を非同期で実行(tasks.py)   
    #         celery_task(next_meeting,participant_emails, kind="recurrence")    


def celery_task(meeting_instance, participant_emails, kind):
    # メール通知を Celery タスクとして非同期処理
    
    # クライアント側ではタイムゾーンが設定されていないので、タイムゾーンを設定
    if timezone.is_naive(meeting_instance.date):
        date = timezone.make_aware(meeting_instance.date)
    else:
        date = meeting_instance.date

    # 10分前の時間を取得
    reminder_time = date - timedelta(minutes=BEFORE_MINITE)
    jst = dt_timezone(timedelta(hours=9))
    
    # 会議作成から開始までが10分以内であれば、参加通知を即時送信
    if reminder_time < timezone.now().astimezone(jst):
        
        kind = "immediately"
        transaction.on_commit(lambda: send_email_task.delay(str(meeting_instance.id), participant_emails, kind))
        return 
    transaction.on_commit(lambda: send_email_task.delay(str(meeting_instance.id), participant_emails, kind))
    PeriodicTask.objects.filter(name=f"meeting_reminder_{meeting_instance.id}").delete()

    # `CrontabSchedule` にスケジュールを登録
    schedule, created = CrontabSchedule.objects.get_or_create(
        minute=reminder_time.minute,
        hour=reminder_time.hour,
        day_of_month=reminder_time.day,
        month_of_year=reminder_time.month,
        timezone="Asia/Tokyo",
    )

    # `PeriodicTask` にタスクを登録
    PeriodicTask.objects.create(
        crontab=schedule,
        name=f"meeting_reminder_{meeting_instance.id}",
        task="source.tasks.send_meeting_reminder",
        args=json.dumps([meeting_instance.id]),
        queue="celery",
        enabled=True,
        one_off=True,  # 1回だけ実行
    )



def edit_celery_task(meeting):
    if timezone.is_naive(meeting.date):
        date = timezone.make_aware(meeting.date)

    # 10分前の時間を取得
    reminder_time = date - timedelta(minutes=BEFORE_MINITE)
    # 既存のタスクを取得（なければ None）
    task = PeriodicTask.objects.filter(name=f"meeting_reminder_{meeting.id}").first()

    # Crontab スケジュールを作成または取得
    schedule, created = CrontabSchedule.objects.get_or_create(
        minute=reminder_time.minute,
        hour=reminder_time.hour,
        day_of_month=reminder_time.day,
        month_of_year=reminder_time.month,
        timezone="Asia/Tokyo",
    )

    if task:
        # 既存の `PeriodicTask` を更新
        task.crontab = schedule
        task.args = json.dumps([meeting.id]) 
        task.enabled = True  # タスクが無効化されていた場合は有効化
        task.one_off = True  # 1回のみ実行
        task.save()
    else:
        # 新規作成
        task = PeriodicTask.objects.create(
            crontab=schedule,
            name=f"meeting_reminder_{meeting.id}",
            task="source.tasks.send_meeting_reminder",
            args=json.dumps([meeting.id]),
            queue="celery",
            enabled=True,
            one_off=True,  # 1回だけ実行
        )
        
def setup_periodic_task():
    schedule, created = CrontabSchedule.objects.get_or_create(hour=22, minute=0)
    # 既存のタスクをチェックし、なければ作成
    if not PeriodicTask.objects.filter(name="run_organize_meetings_daily").exists():
        PeriodicTask.objects.create(
            crontab=schedule,
            name="run_organize_meetings_daily",
            task="source.tasks.organize_meetings",
            args=json.dumps([]),  # 引数なし
        )                    
import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    # オリジナルの列を追加
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # 電話番号の列
    address = models.TextField(blank=True, null=True)  # 住所の列
    last_login = models.DateTimeField(blank=True, null=True)  # 最終ログイン日時の列
    readonly_fields = ("last_login",)
    def __str__(self):
        return self.username



class Meeting(models.Model):
    # 開催日時
    date = models.DateTimeField(verbose_name="開催日時")

    # 作成日時
    created_date = models.DateTimeField(verbose_name="作成日時")
    
    # 会議作成者
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="会議作成者")
    
    # 繰り返しON/OFF
    is_recurring = models.BooleanField(default=False, verbose_name="繰り返しON/OFF")
    
    # 繰り返し日数
    recurrence_days = models.PositiveIntegerField(default=0, null=True, blank=True, verbose_name="繰り返し日数")
    
    # 録画可否
    is_record = models.BooleanField(default=False, verbose_name="録画可否")
    
    # 会議名
    meeting_name = models.CharField(max_length=255, verbose_name="会議名", default="random-" + str(uuid.uuid4()))
    
    # 会議ID
    meeting_id = models.CharField(max_length=255, verbose_name="会議ID", default="random-" + str(uuid.uuid4()))
    
    # パスワード（参加者用）
    attendee_pw = models.CharField(max_length=255, verbose_name="参加者パスワード", default="ap")
    
    # パスワード（モデレーター用）
    moderator_pw = models.CharField(max_length=255, verbose_name="モデレーターパスワード", default="mopa2025")
    
    # ウェルカムメッセージ
    welcome = models.TextField(verbose_name="ウェルカムメッセージ", default="welcome!!")
    
    # ゲストポリシー
    guest_policy = models.CharField(max_length=50, verbose_name="ゲストポリシー", default="ASK_MODERATOR")
    
    # 録画中通知
    notify_record_is_on = models.BooleanField(verbose_name="録画中通知", default=True)
    
    # フルネーム
    full_name = models.CharField(max_length=255, verbose_name="フルネーム", default="John Doe")
    
    # ゲストフラグ
    guest = models.BooleanField(verbose_name="ゲスト", default=True)
    
    # 録画ID
    record_id = models.CharField(max_length=255, verbose_name="録画ID", default="12345")
    
    # 公開フラグ
    publish = models.BooleanField(verbose_name="公開フラグ", default=True)
    
    # 作成時間
    create_time = models.BigIntegerField(verbose_name="作成時間", default=10)

    # 実施済みフラグ
    is_done = models.BooleanField(verbose_name="実施済みフラグ", default=False)

    # 削除済みフラグ
    is_deleted = models.BooleanField(verbose_name="削除済みフラグ", default=False)

    # 繰り返し済みフラグ
    is_recurring_done = models.BooleanField(verbose_name="繰り返し済みフラグ", default=False)
    
    mail_title = models.CharField(max_length=255, verbose_name="メールタイトル", default="会議情報通知 TerakoyaOnline")
    
    mail_text = models.TextField(verbose_name="メールテンプレート", default="", blank=True, null=True)


    class Meta:
        # 複合インデックスを追加
        indexes = [
            # host_meetingsクエリ用
            models.Index(fields=['creator', 'date', 'is_deleted', 'is_done']),
        ]
    
    def __str__(self):
        return f"{self.id}-{self.meeting_name} ({self.meeting_id})"

        

    



class Participant(models.Model):
    meeting = models.ForeignKey(
        'Meeting', 
        on_delete=models.CASCADE, 
        related_name='participants', 
        verbose_name="会議"
    )
    email = models.EmailField(verbose_name="メールアドレス")
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="関連ユーザー"
    )
    
    class Meta:
        # 複合インデックスを追加
        indexes = [
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.user.username if self.user else '未登録'}) ({self.meeting.meeting_name})"
    
    def save(self, *args, **kwargs):
        # email に該当するユーザーを検索して user フィールドに設定
        try:
            self.user = CustomUser.objects.get(email=self.email)
        except CustomUser.DoesNotExist:
            self.user = None
        super().save(*args, **kwargs)

class Notification_Now(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="ユーザー")
    message = models.TextField(verbose_name="メッセージ")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    is_error = models.BooleanField(default=False, verbose_name="エラー")

from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings
from .check_guest import check_guest
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from django.core.mail import send_mail, send_mass_mail



def split_bcc_list_fast(bcc_list, guest_emails):
    if bcc_list is None:
        bcc_list = []
    if guest_emails is None:
        guest_emails = []

    guest_set = set(guest_emails)  # リストをセットに変換 (検索を高速化)
    
    guest_emails = [email for email in bcc_list if email in guest_set]
    user_emails = [email for email in bcc_list if email not in guest_set]
    
    return guest_emails, user_emails

def send_html_bcc_email(meeting, bcc_list, kind):
    """
    HTML メール + BCC 付きで送信する関数

    :param subject: メールの件名
    :param html_content: HTML メール本文
    :param recipient_list: 宛先リスト (TO)
    :param bcc_list: BCC 送信リスト
    """
    SUBJECT = meeting.mail_title
    FROM_EMAIL = settings.DEFAULT_FROM_EMAIL
    
    if kind=='create':
        kind_of_mail = "通知"
        mail_message = f"""\
{meeting.creator}により会議が作成されました。
以下のリンクより会議に参加してください：
{settings.BBB_FRONTEND_URL}/join-mtg/?meeting_id={meeting.id}
"""

    elif kind=='edit':
        kind_of_mail = "変更通知"
        mail_message = f"""\
{meeting.creator}により会議内容が変更されました。
以下のリンクより会議の開催時刻15分前から参加できます：
{settings.BBB_FRONTEND_URL}/join-mtg/?meeting_id={meeting.id}
"""

    elif kind=='remind':
        kind_of_mail = "リマインド"
        mail_message = f"""\
会議が15分後に開催されます。
以下のリンクより会議に参加してください：
{settings.BBB_FRONTEND_URL}/join-mtg/?meeting_id={meeting.id}
"""

    elif kind=='immediately':
        kind_of_mail = "即時通知"
        mail_message = f"""\
会議が早急に開催されます。
以下のリンクより会議に参加してください：
{settings.BBB_FRONTEND_URL}/join-mtg/?meeting_id={meeting.id}
"""    

    elif kind=='recurrence':
        kind_of_mail = "繰り返し通知"
        mail_message = f"""\
次回の会議は上記のように設定されました。
"""

    elif kind=='cancel':
        kind_of_mail = "キャンセル通知"
        mail_message = f"""\
上記の会議は{meeting.creator}によりキャンセルされました。
"""

    else:
        kind_of_mail = "通知"
        mail_message = f"""\
会議情報は以下の通りです。
"""

    if meeting.mail_text:
        mail_message += f"""

以下は会議作成者からのメッセージです。
--------------------------------------
{meeting.mail_text}
"""
        
    # ゲスト用URLの修正
    guest_mail_message = mail_message.replace(
        f"{settings.BBB_FRONTEND_URL}/join-mtg/?meeting_id={meeting.id}",
        f"{settings.BBB_FRONTEND_URL}/guest-join-mtg/{meeting.meeting_id}"
    )    

    user_html_content = f"""\
会議の{kind_of_mail}メールです。

【会議情報】
- 会議名: {meeting.meeting_name}
- 開催日時: {timezone.localtime(meeting.date).strftime('%Y-%m-%d %H:%M:%S')}
    
{mail_message}
"""

    
    
    guest_html_content = f"""\
会議の{kind_of_mail}メールです。

【会議情報】
- 会議名: {meeting.meeting_name}
- 開催日時: {timezone.localtime(meeting.date).strftime('%Y-%m-%d %H:%M:%S')}
    
{guest_mail_message}
"""

    guest_emails = check_guest(bcc_list)
    # bcc_list に含まれる登録済みメールとゲストのメールアドレスの配列を分ける
    guest_emails, user_emails = split_bcc_list_fast(bcc_list, guest_emails)

    # すべての送信メールをリストに格納
    email_messages = [
        EmailMultiAlternatives(
            subject=SUBJECT,
            body=user_html_content,
            from_email=FROM_EMAIL,
            to=[email],  # 各受信者の To に設定
        ) for email in user_emails
    ] + [
        EmailMultiAlternatives(
            subject=SUBJECT,
            body=guest_html_content,
            from_email=FROM_EMAIL,
            to=[email],  # 各ゲストの To に設定
        ) for email in guest_emails
    ]

    # SMTP セッションを共有して一括送信
    connection = get_connection()
    connection.send_messages(email_messages)
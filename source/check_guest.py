
from django.shortcuts import render, redirect
from django.urls import reverse 
def check_guest(participant_emails):
    """
    メールアドレスのリストを受け取り、ゲストかどうかを判定する関数
    """
    from .models import CustomUser
    guest_emails = []
    for email in participant_emails:
        # ユーザーがDBに存在するか判定する。
        if not CustomUser.objects.filter(email=email).exists():
            guest_emails.append(email)
    
    if not len(guest_emails) == 0:
        return guest_emails
    else:
        return None    

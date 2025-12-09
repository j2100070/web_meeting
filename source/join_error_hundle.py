import urllib.parse
import uuid
from datetime import datetime
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Meeting 
from datetime import timedelta
def validate_join_mtg(request, minute):
    """
    フォームの入力値を検証し、エラーがあればリストで返す。
    """
    
    # 参加者(作成者除く)は5分前までアクセスできないエラー
    current_time = (timezone.now() + timedelta(hours=9))
    meeting_id = request.POST.get("meeting_id", "").strip()
    meeting = Meeting.objects.get(meeting_id=meeting_id)
    errors = []
    start_mtg_time = meeting.date + timedelta(hours=9)
    user = request.user
    
    if not (meeting.creator == user) and (start_mtg_time - current_time > timedelta(minutes=minute)):
        errors.append("会議は5分前から参加できます。")

    # 会議名チェック
     

    return errors
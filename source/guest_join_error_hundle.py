import urllib.parse
import uuid
from datetime import datetime
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Meeting 
from datetime import timedelta
def validate_guest_join_mtg(meeting,minute):
    """
    フォームの入力値を検証し、エラーがあればリストで返す。
    """
    current_time = (timezone.now() + timedelta(hours=9))
    errors = []
    start_mtg_time = meeting.date + timedelta(hours=9)
    
    if start_mtg_time - current_time > timedelta(minutes=minute):
        errors.append("会議は5分前から参加できます。")

    # 会議名チェック
     

    return errors

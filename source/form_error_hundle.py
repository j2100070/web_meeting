import urllib.parse
import uuid
from datetime import datetime
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
def validate_mtg_form(request):
    """
    フォームの入力値を検証し、エラーがあればリストで返す。
    """
    errors = []
    
    mtg_name = request.POST.get("mtg_name", "").strip()
    date = request.POST.get("datetime", "").strip()
    participant_emails = request.POST.getlist("participants[]")
    is_recurrence = request.POST.get("is_recurrence") == 'on'
    recurrence_days = request.POST.get("recurrence_days")

    # 会議名チェック
    if not mtg_name:
        errors.append("会議名を入力してください。")

    # 日時チェック
    if not date:
        errors.append("日時を入力してください。")
    else:
        try:
            datetime.strptime(date, '%Y-%m-%dT%H:%M')
        except ValueError:
            errors.append("日時の形式が正しくありません。")

    # 参加者チェック
    if not participant_emails:
        errors.append("参加者を登録してください。")

    # 繰り返し会議チェック
    if is_recurrence:
        if not recurrence_days:
            errors.append("繰り返し会議の日数を入力してください。")
        else:
            try:
                recurrence_days = int(recurrence_days)
                if recurrence_days < 1:
                    errors.append("繰り返し会議の日数は 1 以上で入力してください。")  
            except ValueError:
                errors.append("繰り返し会議の日数は整数で入力してください。")  

    return errors
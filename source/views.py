from . import bbb_api_functions
from . import xml_to_dict
from . import check_guest
from . import form_error_hundle
from . import join_error_hundle 
from . import guest_join_error_hundle
import uuid
from .forms import SignUpForm
import random
import urllib.parse
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.mail import send_mail, EmailMessage
from django.http import HttpResponse, Http404, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.timezone import now, make_aware
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password

from functools import wraps
from decouple import config
from .models import *

from datetime import datetime, time
from django.core.management.base import BaseCommand

from .tasks import *
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json
from django.http import FileResponse
import os




# 認証系ページ
# サインアップ
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # user.refresh_from_db()  # プロファイルが必要な場合に使用
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})
# パスワード変更時のビューおよびルーティング
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change.html'
    success_url = reverse_lazy('home')  # home にリダイレクト

    def form_valid(self, form):
        # パスワード変更成功前にメッセージを追加
        current_time = (timezone.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")
        messages.success(self.request, f"パスワードを変更しました。", extra_tags=current_time)
        return super().form_valid(form)
# ユーザー名変更
def username_change(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        user = request.user
        user.username = username
        user.save()
        return redirect('profile')
    return render(request, 'registration/username_change.html')

def health_check(request):
    return JsonResponse({"status": "ok"})

# ホームページ
@login_required(login_url='/login/')

def home(request):
    # データベース呼び出し
    user = request.user
    element_visible = request.session.get('element_visible', False)
    
    # このクエリはparticipantsテーブルが大きくなければ問題になりにくい
    participants = Participant.objects.filter(email=user.email)

    # 日時関連の準備
    today = datetime.today().date()
    start_of_day = make_aware(datetime.combine(today, datetime.min.time()))
    end_of_day = make_aware(datetime.combine(today, datetime.max.time()))
    
    # 共通のクエリセット
    common_query = Meeting.objects.select_related('creator').prefetch_related('participants')

    
    meetings_list_query = common_query.filter(
        date__gte=start_of_day, participants__email=user.email, is_deleted=False, is_done=False
    ).order_by('date') 
    
    host_meetings_list_query = common_query.filter(
        date__gte=start_of_day, creator=user, is_deleted=False, is_done=False
    ).order_by('date')
    
    # 本日の会議のクエリ（meetings_list_queryから派生させる）
    today_meetings_query = meetings_list_query.filter(date__lte=end_of_day)

    # ページネーションを適用
    paginator_meetings = Paginator(meetings_list_query, 20)
    paginator_host = Paginator(host_meetings_list_query, 20)
    
    page_meetings_num = request.GET.get('m_page', 1)
    page_host_num = request.GET.get('h_page', 1)
    
    meetings_page = paginator_meetings.get_page(page_meetings_num)
    host_meetings_page = paginator_host.get_page(page_host_num)
    
    print(paginator_host.count, 'host_meetings')
    print(paginator_meetings.count, 'meetings')
    print(meetings_page, 'meetings_page')
    print(host_meetings_page, 'host_meetings_page')
    context = {
        'username' : user,
        'element_visible': element_visible,
        'meetings' : meetings_page,
        'host_meetings' : host_meetings_page,
        'participants' : participants,
        'today_meetings': today_meetings_query, # テンプレートで必要分だけ評価される
    }
        
    return render(request, 'home.html', context)



# ユーザー情報ページ
@login_required(login_url='/login/')
def profile(request):
    user = request.user
    element_visible = request.session.get('element_visible', False)
    context = {
        'username' : user,
        'element_visible': element_visible,
    }
    return render(request, 'profile.html',context)



# 会議作成ページ
@login_required(login_url='/login/')
def create_mtg(request):

    user = request.user
    element_visible = request.session.get('element_visible', False)

    if request.method=='POST' and 'mtg_name' in request.POST:
        mtg_name = request.POST.get("mtg_name")
        date = request.POST.get("datetime")
        datetime_object = datetime.strptime(date, '%Y-%m-%dT%H:%M')  # フォーマットを指定して文字列を日時に変換
        participant_emails = request.POST.getlist("participants[]")
        attendee_pw = "ap"
        moderator_pw = str(uuid.uuid4())
        is_guest_join = request.POST.get("is_guest_join") == 'on'
        is_record = request.POST.get("is_record") == 'on'
        is_recurrence = request.POST.get("is_recurrence") == 'on'
        if is_recurrence:
            recurrence_days = request.POST.get("recurrence_days")
        else:
            recurrence_days = 0
        meeting_id = str(uuid.uuid4())
        current_time = (timezone.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")
        mail_title = request.POST.get("mail_title")
        if not mail_title:
            mail_title = "会議情報通知 TerakoyaOnline"
        mail_text = request.POST.get("mail_text")

        # 入力値エラーハンドリング
        errors = form_error_hundle.validate_mtg_form(request)

        # エラーがある場合はフォームを再描画
        if errors:
            for error in errors:
                messages.error(request, error, extra_tags=current_time)

            context = {
                'element_visible': element_visible,
                'post_data': request.POST.dict(),
            }
            return render(request, 'create-mtg.html', context)
        
        # ゲスト参加可否をメールアドレスから判定, is_guest_joinがFalseの場合はゲスト参加不可
        guest_emails = check_guest.check_guest(participant_emails)
        if not is_guest_join and guest_emails:
            current_time = (timezone.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")
            messages.error(request, f"ゲスト参加不可のため、以下のメールアドレスは参加できません。{guest_emails}", extra_tags=current_time)
            context = {
                'element_visible': element_visible,
                'post_data': request.POST.dict(),
            }
            return render(request, 'create-mtg.html', context)

        # 会議作成APIを呼び出す
        response = bbb_api_functions.create_meeting(
            meeting_id,
            mtg_name,
            is_guest_join,
            participant_emails,
            attendee_pw,
            moderator_pw,
            is_record,
            is_recurrence,
            recurrence_days
        )
        createTime = response["createTime"]

        # データベースに登録
        meeting_instance = Meeting(
            meeting_name = mtg_name,
            date = datetime_object,
            created_date = now(),
            creator = request.user,
            meeting_id = meeting_id,
            attendee_pw = attendee_pw,
            moderator_pw = moderator_pw,
            is_record = is_record,
            guest = is_guest_join,
            full_name = user.username,
            is_recurring = is_recurrence,
            recurrence_days = recurrence_days,
            create_time = createTime,
            mail_title = mail_title,
            mail_text = mail_text,
        )
        meeting_instance.save()

        # 参加者を登録
        # 自分自身を参加者に入力していない場合、参加者に登録
        if not user.email in participant_emails:
            participant_emails.append(user.email)

        for participant_email in participant_emails:
            Participant_instance = Participant(
                meeting = meeting_instance,
                email = participant_email
            )
            Participant_instance.save()

        messages.success(request, f"{mtg_name}を作成しました。", extra_tags=current_time)
        print(current_time,'| ',user,'creates a meeting ',mtg_name)
        # tasks.pyに定義しているメールを非同期に処理する関数
        celery_task(meeting_instance, participant_emails, 'create')
        return redirect(reverse('home'))
    
    context = {
        'element_visible': element_visible,
    }
    return render(request, 'create-mtg.html', context)



# 会議参加ページ
@login_required(login_url='/login/')
def join_mtg(request):
    err = False
    user = request.user
    element_visible = request.session.get('element_visible', False)
    # 会議参加ページが表示される場合
    meeting_id = request.GET.get('meeting_id')  # クエリパラメータから会議IDを取得
    meeting = None
    selected_meeting_participants = None
    BEFORE_MINUTE = 15 # 何分前から参加可能になるか
    meetingExpireWhenLastUserLeftInMinutes = 30 # BBBサーバーのmeetingExpireWhenLastUserLeftInMinutes設定値
    
    if meeting_id:
        try:
            meeting = Meeting.objects.get(id=meeting_id,is_deleted=False, is_done=False)
        except Meeting.DoesNotExist:
            raise Http404

    selected_meeting_participants = Participant.objects.filter(meeting=meeting_id)
    if not selected_meeting_participants.filter(email=user.email):  # selected_meeting_participantsのなかにuser.emailがあるか確認、なければ404エラー
        raise Http404
    meeting_info = bbb_api_functions.get_meeting_info(meeting.meeting_id)
    # データベース呼び出し
    participants = Participant.objects.filter(email=user.email)
    meetings = Meeting.objects.filter(participants__email=user.email, is_deleted=False, is_done=False)
    host_meetings = Meeting.objects.filter(creator=user, is_deleted=False, is_done=False)
    active_meeting_id_participant = Participant.objects.filter(email=user.email)

    # 会議参加ボタンが押された場合
    if request.method == 'POST' and 'meeting_id' in request.POST:
        meeting_id = request.POST.get('meeting_id')
        current_time = (timezone.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")
        # 参加時エラーハンドリング
        errors = join_error_hundle.validate_join_mtg(request, BEFORE_MINUTE)
        # 参加時エラーがある場合
        if errors:
            for error in errors:
                messages.error(request, error, extra_tags=current_time)
            context = {
                'username': user,
                'element_visible': element_visible,
                'meetings': meetings,
                'host_meetings': host_meetings,
                'participants': participants,
                'active_meetings': active_meeting_id_participant,
                'selected_meeting': meeting,
                'selected_meeting_participants': selected_meeting_participants,
                'meeting_info': meeting_info['returncode'],
                'error': err,
            }
            return render(request, 'join-mtg.html', context)
        
        try:
            meeting = Meeting.objects.get(meeting_id=meeting_id,is_deleted=False, is_done=False)
        except Meeting.DoesNotExist:
            Http404
        full_name = request.POST.get('user_name')
        createTime = meeting.create_time
        if meeting.creator == user:
            response = bbb_api_functions.join_meeting_api(meeting_id, full_name, meeting.moderator_pw, createTime, False)
        else:
            response = bbb_api_functions.join_meeting_api(meeting_id, full_name, meeting.attendee_pw, createTime, False)
        print(current_time,'| ',full_name,'joined the meeting(login_user)')
        return redirect(response['meeting_url'])

    
    
    # 会議が終了している場合
    if meeting_info['returncode'] == 'FAILED':
        selected_meeting_participants = Participant.objects.filter(meeting=meeting_id)
        current_time = (timezone.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M") # 現在時刻（例: '2025-02-02 12:34' の形式）を文字列で用意
        messages.error(request, f"{meeting.meeting_name}は終了しているため、参加できません。", extra_tags=current_time)

        context = {
            'username': user,
            'element_visible': element_visible,
            'meetings': meetings,
            'host_meetings': host_meetings,
            'participants': participants,
            'active_meetings': active_meeting_id_participant,
            'selected_meeting': meeting,
            'selected_meeting_participants': selected_meeting_participants,
            'meeting_info': meeting_info['returncode'],
            'error': err,
        }
        return render(request, 'join-mtg.html', context)

    # 参加時エラーハンドリング
    current_time = timezone.now() + timedelta(hours=9)
    start_mtg_time = meeting.date + timedelta(hours=9)
    if not (meeting.creator == user) and (start_mtg_time - current_time > timedelta(minutes=BEFORE_MINUTE)):
        err = True

    if user == meeting.creator:
        messages.info(request, "会議は退出後"+str(meetingExpireWhenLastUserLeftInMinutes)+"分で削除されます。", extra_tags=current_time.strftime("%Y-%m-%d %H:%M"))


    context = {
        'username': user,
        'element_visible': element_visible,
        'meetings': meetings,
        'host_meetings': host_meetings,
        'participants': participants,
        'active_meetings': active_meeting_id_participant,
        'selected_meeting': meeting,
        'selected_meeting_participants': selected_meeting_participants,
        'meeting_info': meeting_info['returncode'],
        'error': err,
    }

    return render(request, 'join-mtg.html', context)



# ゲスト会議参加ページ
def guest_join_meeting(request, uuid):
    err = False
    BEFORE_MINUTE = 15
    try:
        meeting = Meeting.objects.get(meeting_id=uuid, guest=True, is_deleted=False, is_done=False)
    except Meeting.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        try:
            meeting = Meeting.objects.get(meeting_id=uuid, guest=True, is_deleted=False, is_done=False)
        except Meeting.DoesNotExist:
            raise Http404
        full_name = request.POST.get('user_name')
        pw = meeting.attendee_pw
        createTime = Meeting.objects.get(meeting_id=uuid).create_time
        current_time = (timezone.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")
        response = bbb_api_functions.join_meeting_api(uuid, full_name, pw, createTime, True)
        
        errors = guest_join_error_hundle.validate_guest_join_mtg(meeting,BEFORE_MINUTE)
        # 参加時エラーがある場合
        if errors:
            for error in errors:
                messages.error(request, error, extra_tags=current_time)
            
            return render(request, 'guest-join-mtg.html',)

        if response['status_code']== 200:
            meeting_url = response['meeting_url']
            print(current_time,'| ',full_name,'joined the meeting(guest)')
            return redirect(meeting_url)
        else:
            messages.error(request, "会議に参加できませんでした。")
            return redirect('home')

    current_time = timezone.now() + timedelta(hours=9)
    start_mtg_time = meeting.date + timedelta(hours=9)
    if (start_mtg_time - current_time > timedelta(minutes=BEFORE_MINUTE)):
        err = True

    context = {
        'error': err,
    }

    return render(request, 'guest-join-mtg.html', context)




# 会議編集ページ
@login_required(login_url='/login/')
def edit_mtg(request):
    user = request.user
    element_visible = request.session.get('element_visible', False)

    # クエリパラメータから会議IDを取得
    meeting_id = request.GET.get('meeting_id')                                       
    meeting = None

    if meeting_id:
        try:
            meeting = Meeting.objects.get(creator=user,id=meeting_id,is_deleted=False, is_done=False)
        except Meeting.DoesNotExist:
            raise Http404
    selected_meeting_participants = Participant.objects.filter(meeting=meeting)
    active_meeting_id_participant = Participant.objects.filter(email=user.email)

    if request.method == 'POST' and 'mtg_name' in request.POST:
        mtg_uuid = request.POST.get('meeting_id')
        current_time = (timezone.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")
        user = request.user

        try:
            # 1. 会議情報を取得(存在しなければ404エラー)
            meeting = Meeting.objects.get(creator=user, meeting_id=mtg_uuid, is_deleted=False, is_done=False)
        except Meeting.DoesNotExist:
            raise Http404
        except MultipleObjectsReturned:
            # 複数のレコードが見つかった場合
            # ログを記録するか、データベースのデータを修正する必要がある場合がある
            print(meeting.id,'is not unique')
            raise Http404
        try:
            # 2. POSTデータを取得
            mtg_name = request.POST.get("mtg_name")
            meeting_id = str(uuid.uuid4())
            date = request.POST.get("datetime")
            datetime_object = datetime.strptime(date, '%Y-%m-%dT%H:%M')  # 文字列をdatetime型に変換
            # [ ] 低。以下のエラーを解消したい。
            # app            | /usr/local/lib/python3.13/site-packages/django/db/models/fields/__init__.py:1595: RuntimeWarning: DateTimeField Meeting.date received a naive datetime (2025-03-06 14:15:00) while time zone support is active.
            # app            | warnings.warn(
            is_guest_join = request.POST.get("is_guest_join") == 'on'  # チェックボックスがオンか判定
            participant_emails = request.POST.getlist("participants[]")  # 複数の参加者メール
            attendee_pw = "ap"
            is_record = request.POST.get("is_record") == 'on'
            is_recurrence = request.POST.get("is_recurrence") == 'on'
            recurrence_days = request.POST.get("recurrence_days")
            if is_recurrence:
                recurrence_days = request.POST.get("recurrence_days")
            else:
                recurrence_days = 0
            errors = form_error_hundle.validate_mtg_form(request)
            # 日本時間（UTC+9）に変換
            current_time = (timezone.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")
            mail_title = request.POST.get("mail_title")
            if not mail_title:
                mail_title = "会議情報通知 TerakoyaOnline"
            mail_text = request.POST.get("mail_text")

            # エラーがある場合はフォームを再描画
            if errors:
                for error in errors:
                    messages.error(request, error, extra_tags=current_time)

                context = {
                    'username': user,
                    'element_visible': element_visible,
                    'post_data': request.POST.dict(),
                    'active_meetings': active_meeting_id_participant,
                    'selected_meeting': meeting,  # クリックされた会議情報をコンテキストに追加    
                    'selected_meeting_participants': selected_meeting_participants,
                }
                return render(request, 'edit-mtg.html', context)

            # ゲスト参加可否をメールアドレスから判定, is_guest_joinがFalseの場合はゲスト参加不可
            guest_emails = check_guest.check_guest(participant_emails)
            if not is_guest_join and guest_emails:
                current_time = (timezone.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")
                messages.error(request, f"ゲスト参加不可のため、以下のメールアドレスは参加できません。{guest_emails}", extra_tags=current_time)
                context = {
                    'username': user,
                    'element_visible': element_visible,
                    'post_data': request.POST.dict(),
                    'active_meetings': active_meeting_id_participant,
                    'selected_meeting': meeting,  # クリックされた会議情報をコンテキストに追加    
                    'selected_meeting_participants': selected_meeting_participants,
                }
                return render(request, 'edit-mtg.html', context)
            
            # 3. Meetingオブジェクトを更新
            meeting.meeting_name = mtg_name
            meeting.meeting_id = meeting_id
            meeting.date = datetime_object
            meeting.guest = is_guest_join
            meeting.attendee_pw = attendee_pw
            meeting.is_record = is_record
            meeting.is_recurring = is_recurrence
            meeting.recurrence_days = recurrence_days
            meeting.mail_title = mail_title
            meeting.mail_text = mail_text
            # 新規会議として会議作成APIを呼び出す。
            response = bbb_api_functions.create_meeting(
                meeting_id,
                mtg_name,
                is_guest_join,
                participant_emails,
                attendee_pw,
                meeting.moderator_pw,
                is_record,
                is_recurrence,
                recurrence_days
            )
            createTime = response["createTime"]
            meeting.create_time = createTime
            # 4. データベースに保存
            meeting.save()

            # 5. 参加者（Participants）の更新処理
            # 自分自身を参加者に入力していない場合、参加者に登録
            if not user.email in participant_emails:
                participant_emails.append(user.email)
            # 既存の参加者を削除し、新しいメールアドレスで追加する場合の例
            meeting.participants.all().delete()  # 現在の参加者を全削除
            for email in participant_emails:
                Participant.objects.create(meeting=meeting, email=email)

            # 6. Celeryタスクの再設定(tasks.py参照)
            edit_celery_task(meeting)
            celery_task(meeting, participant_emails, 'edit')

            # 7. 成功メッセージとリダイレクト
            messages.success(request, f"{meeting.meeting_name}を更新しました。")
            print(
                current_time,'| ',
                user,'edit a meeting ',
                mtg_name,
                meeting_id,
                datetime_object,
                is_guest_join,
                attendee_pw,
                is_record,
                is_recurrence,
                recurrence_days
            )
            return redirect('home')

        except Exception as e:
            # エラーハンドリング
            messages.error(request, f"{meeting.meeting_name}の更新中にエラーが発生しました: {e}")
            return redirect('home')

    context = {
        'username': user,
        'element_visible': element_visible,
        'active_meetings': active_meeting_id_participant,
        'selected_meeting': meeting,  # クリックされた会議情報をコンテキストに追加    
        'selected_meeting_participants': selected_meeting_participants,
    }
    
    return render(request, 'edit-mtg.html', context)



# 会議削除ページ
# [ ] 保留。BBBサーバーの会議を削除したい。（BBBサーバーの処理コストや容量が問題なければ対応しなくて良し。）
@login_required(login_url='/login/')
def page_delete_mtg(request):
    if request.method == 'POST' and 'meeting_id' in request.POST:        
        meeting_id = request.POST.get('meeting_id')
        meeting = Meeting.objects.get(meeting_id=meeting_id, is_deleted=False)
        participant_emails = [participant.email for participant in Participant.objects.filter(meeting=meeting.id)]
        celery_task(meeting, participant_emails, 'cancel')
        user = request.user
        current_time = (timezone.now() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")

        try:
            meeting.is_deleted = True
            meeting.save()
            messages.success(request, f"{meeting.meeting_name}を削除しました。")
            # Celeryタスクの再設定
            task = PeriodicTask.objects.filter(name=f"meeting_reminder_{meeting.id}").first()
            if task:
                task.delete()
                print(f"Deleted PeriodicTask: {task.name}")
            else:
                print("No PeriodicTask found to delete")
        except Meeting.DoesNotExist:
            print('meeting does not exist. uuid=', uuid)
            messages.error(request, f"{meeting.meeting_name}は存在しません。")
        except MultipleObjectsReturned:
            # 複数のレコードが見つかった場合
            print('multiple meeting records found. uuid=', uuid)
            messages.error(request, f"{meeting.meeting_name}が複数存在します。")

        print(current_time,'| ',user,'deletes a meeting ',meeting.meeting_name)
        return redirect('home')

    user = request.user
    element_visible = request.session.get('element_visible', False)

    # クエリパラメータから会議IDを取得
    meeting_id = request.GET.get('meeting_id')                                     
    meeting = None

    if meeting_id:
        try:
            meeting = Meeting.objects.get(id=meeting_id, creator=user, is_deleted=False, is_done=False)
        except Meeting.DoesNotExist:
            raise Http404

    selected_meeting_participants = Participant.objects.filter(meeting=meeting.id)

    # データベース呼び出し
    participants = Participant.objects.filter(email=user.email)
    meetings = Meeting.objects.filter(participants__email=user.email, is_deleted=False, is_done=False)
    host_meetings = Meeting.objects.filter(creator=user, is_deleted=False, is_done=False)

    active_meeting_id_participant = Participant.objects.filter(email=user.email)

    context = {
        'username': user,
        'element_visible': element_visible,
        'meetings': meetings,
        'host_meetings': host_meetings,
        'participants': participants,
        'active_meetings': active_meeting_id_participant,
        'selected_meeting': meeting,  # クリックされた会議情報をコンテキストに追加    
        'selected_meeting_participants': selected_meeting_participants,
    }
    return render(request, 'delete-mtg.html', context)



# マニュアルページ
@login_required(login_url='/login/')
def read_me(request):
    element_visible = request.session.get('element_visible', False)
    context = {
        'element_visible': element_visible,
    }
    return render(request, 'read-me.html', context)



# 会議後リダイレクトページ
def tab_close(request):
    return render(request, 'tab-close.html')





# セッション管理　--------------------------------------------------------------
# セッションに状態を保存するAPI
def set_visibility(request):
    if request.method == 'POST':
        # フォームから表示状態を取得しセッションに保存
        is_visible = request.POST.get('visible') == 'true'
        request.session['element_visible'] = is_visible
        return JsonResponse({'status': 'success', 'visible': is_visible})
    return JsonResponse({'status': 'error'}, status=400)
# セッションから状態を取得するAPI
def get_visibility(request):
    element_visible = request.session.get('element_visible', False)
    return JsonResponse({'visible': element_visible})


# テスト用API  --------------------------------------------------------------

# 会議が進行中か確認
def is_meeting_running(request):
    response = bbb_api_functions.is_meeting_running(request)
    username = request.user.username
    context = {
        'username': username, 
        'json_response': response,
    }
    return render(request, 'home.html', context)

def get_meeting_info(request):
    response = bbb_api_functions.get_meeting_info(request)
    username = request.user.username
    context = {
        'username': username, 
        'json_response': response,
    }
    return render(request, 'home.html', context)

# 会議の録画リストを取得
def get_recordings(request):
    response = bbb_api_functions.get_recordings(request)
    username = request.user.username
    context = {
        'username': username, 
        'json_response': response,
    }
    return render(request, 'home.html', context)

# 録画を共有
def publish_recordings(request):
    response = bbb_api_functions.publish_recordings(request)
    username = request.user.username
    context = {
        'username': username, 
        'json_response': response,
    }
    return render(request, 'home.html', context)

# 録画を非共有
def unpublish_recordings(request):
    response = bbb_api_functions.unpublish_recordings(request)
    username = request.user.username
    context = {
        'username': username, 
        'json_response': response,
    }
    return render(request, 'home.html', context)

# 録画を削除
def delete_recordings(request):
    response = bbb_api_functions.delete_recordings(request)
    username = request.user.username
    context = {
        'username': username, 
        'json_response': response,
    }
    return render(request, 'home.html', context)

def db_register(request):
    
     # 本来のループ回数（例: 1,000,000件）
    loop_count = 1000000 
    
    # 1. ループで必要となるユニークなユーザーIDのセットを作成
    user_ids_to_fetch = { (i % 100000) + 1 for i in range(1, loop_count + 1) }

    # 2. 必要なユーザーオブジェクトを1回のクエリで全て取得
    users = CustomUser.objects.filter(id__in=user_ids_to_fetch)
    
    # 3. IDをキーにした辞書を作成し、高速にアクセスできるようにする
    users_dict = { user.id: user for user in users }
    
    meetings_to_create = []
    batch_size = 10000

    for i in range(1, loop_count + 1):
        user_id = (i % 100000) + 1
        
        # 4. データベースではなく、事前に作成した辞書からユーザーを取得
        user = users_dict.get(user_id) 
        
        # 辞書にユーザーが存在しないケースも考慮（念のため）
        if not user:
            continue

        meetings_to_create.append(
            Meeting(
                meeting_name=f"Test Meeting {i}",
                date=now(),
                created_date=now(),
                creator=user,
                meeting_id=str(uuid.uuid4()),
                attendee_pw="ap",
                moderator_pw=str(uuid.uuid4()),
                is_record=True,
                guest=True,
                full_name=str(user_id),
                is_recurring=False,
                recurrence_days=0,
                create_time=10,
            )
        )
        
        if i % batch_size == 0:
            Meeting.objects.bulk_create(meetings_to_create)
            meetings_to_create = []

    if meetings_to_create:
        Meeting.objects.bulk_create(meetings_to_create) # ignore_conflictsは必要に応じて

    return JsonResponse({"status": "success", "message": "Meetings registered successfully."})
def db_delete(request):
    # Meetingモデルの全てのレコードを削除
    Meeting.objects.all().delete()
    # Participantモデルの全てのレコードを削除
    Participant.objects.all().delete()
    return JsonResponse({"status": "success", "message": "All meetings and participants deleted successfully."})

def create_user(request):
    user_to_create = []
    # 適切なバッチサイズを設定（例：1000件ごと）
    batch_size = 10000
    passwords = make_password("password123")  # パスワードはハッシュ化して保存
    for i in range(1, 100000 + 1): # 1から1,000,000まで
        user_to_create.append(
            CustomUser(
                username=f"testuser{i}",
                email=f"testuser{i}@testuser{i}",
                password=passwords,  # パスワードはハッシュ化して保存
                is_active=True,  # ユーザーをアクティブに設定
                is_staff=False,  # スタッフ権限は不要
                is_superuser=False,  # スーパーユーザー権限は不要
            )
        )
        
        # リストがバッチサイズに達したら、一度 bulk_create を実行し、リストを空にする
        if i % batch_size == 0:
            CustomUser.objects.bulk_create(user_to_create)
            user_to_create = []

    # ループの最後にリストに残っているオブジェクトがあれば、それらも登録する
    if user_to_create:
        CustomUser.objects.bulk_create(user_to_create, ignore_conflicts=True)
    return JsonResponse({"status": "success", "message": "Meetings registered successfully."})

def create_participants(request):
    participants_to_create = []
    # 適切なバッチサイズを設定（例：1000件ごと）
    batch_size = 10000
    tmp = 530058
    for i in range(tmp, 500000 + tmp): # 1から1,000,000まで
        participants_to_create.append(
            Participant(
                meeting_id=i,
                email=f"testuser{i}@testuser{i}",
            )
        )
        
        # リストがバッチサイズに達したら、一度 bulk_create を実行し、リストを空にする
        if i % batch_size == 0:
            Participant.objects.bulk_create(participants_to_create)
            participants_to_create = []

    # ループの最後にリストに残っているオブジェクトがあれば、それらも登録する
    if participants_to_create:
        Participant.objects.bulk_create(participants_to_create, ignore_conflicts=True)
    return JsonResponse({"status": "success", "message": "Participants registered successfully."})
        
        
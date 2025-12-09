from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required  # 未ログインの場合、setting.LOGIN_URLにリダイレクトする。
from . import views



urlpatterns = [
    # フロントページ
    path('', login_required(views.home), name='home'),
    path('join-mtg/', login_required(views.join_mtg), name='join-mtg'),
    path('guest-join-mtg/<uuid:uuid>', views.guest_join_meeting, name='guest-join-mtg'),
    path('create-mtg/', login_required(views.create_mtg), name='create-mtg'),
    path('edit-mtg/', login_required(views.edit_mtg), name='edit-mtg'),
    path('page-delete-mtg/', login_required(views.page_delete_mtg), name='page-delete-mtg'),
    path('profile/', login_required(views.profile), name='profile'),
    path('tab-close/', views.tab_close, name='tab-close'),

    # 認証系ページ
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('username_change/', views.username_change, name='username_change'),
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # API用URL
    path('is-meeting-running/', views.is_meeting_running, name='is_meeting_running'),
    path('get-meeting-info/', views.get_meeting_info, name='get_meeting_info'),
    path('get-recordings/', views.get_recordings, name='get_recordings'),
    path('publish-recordings/', views.publish_recordings, name='publish_recordings'),
    path('unpublish-recordings/', views.unpublish_recordings, name='unpublish_recordings'),
    path('delete-recordings/', views.delete_recordings, name='delete_recordings'),

    # セッション管理URL
    path('set_visibility/', views.set_visibility, name='set_visibility'),
    path('get_visibility/', views.get_visibility, name='get_visibility'),
    
    # 大人数登録(開発用)
    path('db_register/', views.db_register, name='db_register'),
    path('db_delete/', views.db_delete, name='db_delete'),
    path('create_user/', views.create_user, name='create_user'),
    path('create_participants', views.create_participants, name='create_participants'),
    
]
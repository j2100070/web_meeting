from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Meeting, Participant, Notification_Now



class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # 表示するフィールドをカスタマイズ
    list_display = ('id','username', 'email', 'is_staff', 'is_active', 'last_login')
    list_filter = ('is_staff', 'is_active')
    readonly_fields = ("last_login",)
    search_fields = ('username', 'email')
    ordering = ('username',)

class MeetingAdmin(admin.ModelAdmin):
    # 一覧にID、会議名、作成者、開催日を表示
    list_display = ('id', 'meeting_name', 'creator', 'date', 'is_done')
    # 検索フィールドを追加
    search_fields = ('meeting_name', 'creator__username')
    # フィルタを追加
    list_filter = ('date', 'is_done', 'is_deleted')
    list_select_related = ['creator']

# 3. Participantの管理サイト設定
class ParticipantAdmin(admin.ModelAdmin):
    list_per_page = 20  # 1ページあたり20件に設定
    # 一覧にID、メールアドレス、関連する会議名を表示
    list_display = ('id', 'email', 'meeting')
    # 検索フィールドを追加
    search_fields = ('email', 'meeting__meeting_name')
    list_select_related = ['meeting', 'user']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Meeting)
admin.site.register(Participant)
admin.site.register(Notification_Now)
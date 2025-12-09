from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Terakoya管理画面"
admin.site.site_title = "Terakoya管理"
admin.site.index_title = "Terakoya管理ページ"
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('source.urls')), 
    path("__debug__/", include("debug_toolbar.urls")),
]

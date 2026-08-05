"""Djangoプロジェクト全体のURL入口。

ブラウザやReactから届いたURLを最初に確認するファイルです。
`/api/`はapiアプリへ、`/admin/`はDjango管理画面へ処理を渡します。
API個別のURLは `api/urls.py` に定義しています。
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # DBデータをブラウザで確認・編集するDjango標準管理画面。
    path("admin/", admin.site.urls),
    # `/api/`以降のURL判定をapi/urls.pyへ委譲する。
    path("api/", include("api.urls")),
]

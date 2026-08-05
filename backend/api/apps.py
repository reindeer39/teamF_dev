"""apiアプリをDjangoへ登録するためのアプリ設定。"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """INSTALLED_APPSの`api`に対応する設定クラス。"""

    name = "api"

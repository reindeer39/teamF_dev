"""
メイン実行エントリーポイント (main.py)
アプリケーションの起動プロセスおよびルート構成を明確に示します。
"""
import os
import sys
from django.core.management import execute_from_command_line
from config.config import AppConfig


class ApplicationLauncher(AppConfig):
    """
    アプリケーション起動クラス
    構成情報（AppConfig）を継承し、環境をロードしてサービスを起動します。
    """
    def __init__(self):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    def run(self):
        print(f"=== 送金システム バックエンド起動 ===")
        print(f"Base URL: {self.BASE_URL}")
        print(f"Database: {self.DB_NAME}")
        print(f"=====================================")
        
        args = sys.argv if len(sys.argv) > 1 else ["manage.py", "runserver", "0.0.0.0:8000"]
        execute_from_command_line(args)


if __name__ == "__main__":
    launcher = ApplicationLauncher()
    launcher.run()

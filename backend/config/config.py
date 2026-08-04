"""
システム共通の構成クラス (config.py)
環境依存値やベースURLを一元管理します。
"""
from pathlib import Path


class AppConfig:
    # サーバー・URL設定
    BASE_URL: str = "http://localhost:8000"
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
    
    # データベース設定
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DB_ENGINE: str = "django.db.backends.sqlite3"
    DB_NAME: Path = BASE_DIR / "db.sqlite3"
    
    # CORS設定
    CORS_ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # デフォルトメディア/静的ファイルパス
    DEFAULT_USER_ICON: str = "/static/images/default_user.png"

    @classmethod
    def get_db_config(cls) -> dict:
        """データベース設定辞書を取得"""
        return {
            "default": {
                "ENGINE": cls.DB_ENGINE,
                "NAME": cls.DB_NAME,
            }
        }

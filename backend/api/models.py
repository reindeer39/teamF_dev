"""
既存のSQLiteデータベースを参照するモデル定義 (models.py)

【重要】
既存SQLiteデータベーステーブルと連携するため、
`managed = False` を指定 (Djangoによる自動テーブル作成・削除を無効化)。
"""
from django.db import models
from config.config import AppConfig


class BaseModel(models.Model):
    """構成クラスを参照する基底モデルクラス"""

    class Meta:
        abstract = True

    @property
    def config(self):
        return AppConfig


class UserAccount(BaseModel):
    """
    ユーザー口座モデル
    各フィールド名: account_number, user_icon, user_name, account_balance
    """
    account_number = models.CharField(max_length=20, primary_key=True, verbose_name="口座番号")
    user_icon = models.CharField(max_length=255, verbose_name="ユーザアイコン")
    user_name = models.CharField(max_length=100, verbose_name="ユーザ名")
    account_balance = models.IntegerField(default=0, verbose_name="預金残高")

    class Meta:
        managed = False
        # =========================================================================
        # 【要設定】実際のSQLiteデータベースのテーブル名を指定してください
        # 例: db_table = "main" または db_table = "user_account"
        # =========================================================================
        db_table = "CHANGE_TO_ACTUAL_USER_TABLE_NAME"

    def __str__(self):
        return f"{self.user_name} ({self.account_number})"


class TransferTransaction(BaseModel):
    """
    送金関連履歴モデル
    各フィールド名: transaction_number, sender_account_number, recipient_account_number, transfer_amount, message, time
    """
    transaction_number = models.CharField(max_length=50, primary_key=True, verbose_name="取引番号")
    sender_account = models.ForeignKey(
        UserAccount, 
        on_delete=models.DO_NOTHING, 
        related_name="sent_transfers", 
        db_column="sender_account_number",
        verbose_name="送信元口座"
    )
    recipient_account = models.ForeignKey(
        UserAccount, 
        on_delete=models.DO_NOTHING, 
        related_name="received_transfers", 
        db_column="recipient_account_number",
        verbose_name="送信先口座"
    )
    transfer_amount = models.IntegerField(verbose_name="金額")
    message = models.CharField(max_length=255, null=True, blank=True, verbose_name="メッセージ")
    
    # 時間カラム (形式: "YYYY-MM-DD HH:MM:SS.ffffff" 例: "2026-08-04 22:07:30.123456")
    time = models.CharField(max_length=35, verbose_name="時間")

    class Meta:
        managed = False
        # =========================================================================
        # 【要設定】実際のSQLiteデータベースのテーブル名を指定してください
        # 例: db_table = "transfer_transaction" または db_table = "transfer"
        # =========================================================================
        db_table = "CHANGE_TO_ACTUAL_TRANSFER_TABLE_NAME"

    def __str__(self):
        return f"Tx:{self.transaction_number} ({self.sender_account_id} -> {self.recipient_account_id})"

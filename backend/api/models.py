import uuid

from django.core.validators import MinValueValidator
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

class Account(models.Model):
    account_number = models.CharField(max_length=20, primary_key=True)
    user_icon = models.CharField(max_length=255, blank=True, default="")
    user_name = models.CharField(max_length=100)
    account_balance = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "accounts"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(account_balance__gte=0),
                name="account_balance_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.user_name}（{self.account_number}）"


class Transaction(models.Model):
    transaction_number = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    sender = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="sent_transactions",
    )
    recipient = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="received_transactions",
    )
    transfer_amount = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)],
    )
    message = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(transfer_amount__gte=1),
                name="transfer_amount_gte_1",
            ),
            models.CheckConstraint(
                condition=~models.Q(sender=models.F("recipient")),
                name="sender_recipient_different",
            ),
        ]

    def __str__(self):
        return (
            f"{self.sender.account_number} → {self.recipient.account_number}："
            f"{self.transfer_amount}円"
        )

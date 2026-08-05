"""Django ORMとSQLiteテーブルの対応を定義するモデル。

ViewはSQLを直接書かず、このAccount/Transactionクラスを通じてDBを操作します。
モデル変更後は `python manage.py makemigrations api` が必要です。
"""

import uuid

from django.core.validators import MinValueValidator
from django.db import models


class Account(models.Model):
    """口座情報を表し、SQLiteの`accounts`テーブルに対応する。"""

    # 口座番号を主キーにするため、同じ番号のAccountは重複登録できない。
    account_number = models.CharField(max_length=20, primary_key=True)
    user_icon = models.CharField(max_length=255, blank=True, default="")
    user_name = models.CharField(max_length=100)
    account_balance = models.PositiveBigIntegerField(default=0)

    class Meta:
        # Django標準のapi_accountではなく、仕様どおりaccountsを使用する。
        db_table = "accounts"
        constraints = [
            # APIを経由しない更新でも、DB側で負の残高を拒否する。
            models.CheckConstraint(
                condition=models.Q(account_balance__gte=0),
                name="account_balance_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.user_name}（{self.account_number}）"


class Transaction(models.Model):
    """1回の送金履歴を表し、SQLiteの`transactions`テーブルに対応する。"""

    # URLなどで安全に扱える一意なUUIDを取引番号として自動生成する。
    transaction_number = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    sender = models.ForeignKey(
        Account,
        # 履歴から参照中の口座を削除すると整合性が崩れるため保護する。
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
        # Transaction.objects.all()は送金日時が新しいものから返す。
        ordering = ["-created_at"]
        constraints = [
            # バリデータに加え、DB側でも0円以下の送金を拒否する。
            models.CheckConstraint(
                condition=models.Q(transfer_amount__gte=1),
                name="transfer_amount_gte_1",
            ),
            models.CheckConstraint(
                # sender_idとrecipient_idが同じレコードをDB側で拒否する。
                condition=~models.Q(sender=models.F("recipient")),
                name="sender_recipient_different",
            ),
        ]

    def __str__(self):
        return (
            f"{self.sender.account_number} → {self.recipient.account_number}："
            f"{self.transfer_amount}円"
        )

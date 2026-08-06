"""Django ORMとSQLiteテーブルの対応を定義するモデル。

Viewや管理コマンドはSQLを直接書かず、各モデルを通じてDBを操作します。
モデル変更後は `python manage.py makemigrations api` が必要です。
"""

import uuid

from django.core.exceptions import ValidationError
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


class Invoice(models.Model):
    """請求リンクで使用する請求情報を表す。"""

    class InvoiceFlag(models.TextChoices):
        NOTPAY = "notpay", "未払い"
        PAID = "paid", "支払済み"

    invoice_number = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    invoice_amount = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)],
    )
    message = models.CharField(max_length=200, blank=True, default="")
    account_number = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="issued_invoices",
        db_column="account_number",
    )
    created_time = models.DateTimeField(auto_now_add=True)
    invoice_flag = models.CharField(
        max_length=10,
        choices=InvoiceFlag.choices,
        default=InvoiceFlag.NOTPAY,
    )
    paid_time = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="paid_invoices",
        null=True,
        blank=True,
        db_column="paid_by",
    )
    transaction_number = models.OneToOneField(
        Transaction,
        on_delete=models.PROTECT,
        related_name="invoice",
        null=True,
        blank=True,
        db_column="transaction_number",
    )

    class Meta:
        db_table = "invoices"
        ordering = ["-created_time"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(invoice_amount__gte=1),
                name="invoice_amount_gte_1",
            ),
            models.CheckConstraint(
                condition=models.Q(invoice_flag__in=["notpay", "paid"]),
                name="invoice_flag_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        invoice_flag="notpay",
                        paid_time__isnull=True,
                        paid_by__isnull=True,
                        transaction_number__isnull=True,
                    )
                    | models.Q(
                        invoice_flag="paid",
                        paid_time__isnull=False,
                        paid_by__isnull=False,
                        transaction_number__isnull=False,
                    )
                ),
                name="invoice_payment_fields_match_flag",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(paid_by__isnull=True)
                    | ~models.Q(account_number=models.F("paid_by"))
                ),
                name="invoice_issuer_payer_different",
            ),
        ]

    def clean(self):
        """支払状態と支払情報の組み合わせをモデルレベルでも検証する。"""
        super().clean()
        errors = {}
        payment_fields = {
            "paid_time": self.paid_time,
            "paid_by": self.paid_by_id,
            "transaction_number": self.transaction_number_id,
        }

        if self.invoice_flag == self.InvoiceFlag.NOTPAY:
            for field_name, value in payment_fields.items():
                if value is not None:
                    errors[field_name] = "未払いの請求には設定できません。"
        elif self.invoice_flag == self.InvoiceFlag.PAID:
            for field_name, value in payment_fields.items():
                if value is None:
                    errors[field_name] = "支払済みの請求では必須です。"

        if (
            self.account_number_id is not None
            and self.paid_by_id is not None
            and self.account_number_id == self.paid_by_id
        ):
            errors["paid_by"] = "請求元口座と支払口座は同じ口座にできません。"

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.account_number.user_name}：{self.invoice_amount}円"
            f"（{self.get_invoice_flag_display()}）"
        )

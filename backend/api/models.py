import uuid

from django.core.validators import MinValueValidator
from django.db import models


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

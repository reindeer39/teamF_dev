from django.contrib import admin
from django.utils import timezone

from .models import Account, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("account_number", "user_name", "account_balance")
    search_fields = ("account_number", "user_name")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_number",
        "sender",
        "recipient",
        "transfer_amount",
        "message",
        "formatted_created_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "sender__account_number",
        "sender__user_name",
        "recipient__account_number",
        "recipient__user_name",
        "message",
    )
    readonly_fields = ("transaction_number", "formatted_created_at")

    @admin.display(ordering="created_at", description="created_at")
    def formatted_created_at(self, obj):
        if not obj.created_at:
            return ""
        return timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S.%f")

from django.contrib import admin

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
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "sender__account_number",
        "sender__user_name",
        "recipient__account_number",
        "recipient__user_name",
        "message",
    )
    readonly_fields = ("transaction_number", "created_at")

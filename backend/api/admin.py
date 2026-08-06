"""Account、Transaction、Invoiceの管理画面表示設定。

APIの実行後に`/admin/`を開くと、残高と送金履歴がDBへ保存されたか確認できます。
このファイルはReact向けAPIのレスポンスには影響しません。
"""

from django.contrib import admin
from django.utils import timezone

from .models import Account, Invoice, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """口座一覧の表示列と検索対象を設定する。"""
    list_display = ("account_number", "user_name", "account_balance")
    search_fields = ("account_number", "user_name")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """送金履歴の表示列、絞り込み、検索、読み取り専用項目を設定する。"""
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
        """送金日時をチームで統一したマイクロ秒付き形式で表示する。"""
        if not obj.created_at:
            return ""
        return timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S.%f")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """請求情報の表示列、検索、絞り込み、読み取り専用項目を設定する。"""

    list_display = (
        "invoice_number",
        "account_number",
        "invoice_amount",
        "invoice_flag",
        "paid_by",
        "formatted_created_time",
        "formatted_paid_time",
    )
    search_fields = (
        "invoice_number",
        "account_number__account_number",
        "account_number__user_name",
        "paid_by__account_number",
        "paid_by__user_name",
        "message",
        "transaction_number__transaction_number",
    )
    list_filter = ("invoice_flag", "created_time", "paid_time")
    readonly_fields = ("invoice_number", "created_time")

    @admin.display(ordering="created_time", description="created_time")
    def formatted_created_time(self, obj):
        if not obj.created_time:
            return ""
        return timezone.localtime(obj.created_time).strftime("%Y-%m-%d %H:%M:%S.%f")

    @admin.display(ordering="paid_time", description="paid_time")
    def formatted_paid_time(self, obj):
        if not obj.paid_time:
            return ""
        return timezone.localtime(obj.paid_time).strftime("%Y-%m-%d %H:%M:%S.%f")

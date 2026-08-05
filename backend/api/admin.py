"""AccountとTransactionをDjango管理画面で確認するための表示設定。

APIの実行後に`/admin/`を開くと、残高と送金履歴がDBへ保存されたか確認できます。
このファイルはReact向けAPIのレスポンスには影響しません。
"""

from django.contrib import admin
from django.utils import timezone

from .models import Account, Transaction


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

"""共有JSONを各開発者のSQLiteへ投入するカスタム管理コマンド。

APIが利用するAccountとTransactionを、fixture形式ではない通常のJSONから
作成します。実行方法は `python manage.py seed_mock_data` です。
"""

import json
import uuid
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.deletion import ProtectedError

from api.models import Account, Transaction


class Command(BaseCommand):
    help = "通常のJSON形式で管理された共同開発用モックデータを登録します。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="JSONに記載されたデータだけを削除してから再登録します。",
        )

    def get_mock_data_path(self):
        return Path(settings.BASE_DIR) / "api" / "mock_data" / "mock_data.json"

    def handle(self, *args, **options):
        # DBへ書き込む前にJSON全体を検証し、不正データの途中登録を防ぐ。
        data = self._load_and_validate(self.get_mock_data_path())

        account_created = 0
        account_updated = 0
        transaction_created = 0
        transaction_updated = 0

        try:
            # Account作成からTransaction作成までを全部成功・全部取消にする。
            with transaction.atomic():
                if options["reset"]:
                    # 外部キー制約に従い、必ずTransactionを先に削除する。
                    transaction_numbers = [
                        item["parsed_transaction_number"]
                        for item in data["transactions"]
                    ]
                    account_numbers = [
                        item["account_number"] for item in data["accounts"]
                    ]
                    Transaction.objects.filter(
                        transaction_number__in=transaction_numbers
                    ).delete()
                    Account.objects.filter(account_number__in=account_numbers).delete()

                for item in data["accounts"]:
                    # 口座番号が既存なら更新、なければ新規作成する。
                    _, created = Account.objects.update_or_create(
                        account_number=item["account_number"],
                        defaults={
                            "user_icon": item.get("user_icon", ""),
                            "user_name": item["user_name"],
                            "account_balance": item["account_balance"],
                        },
                    )
                    account_created += int(created)
                    account_updated += int(not created)

                for index, item in enumerate(data["transactions"]):
                    # 外部キーへ渡すため、JSONの口座番号からAccountを取得する。
                    sender = self._get_account(
                        item["sender_account_number"], index, "sender_account_number"
                    )
                    recipient = self._get_account(
                        item["recipient_account_number"],
                        index,
                        "recipient_account_number",
                    )
                    _, created = Transaction.objects.update_or_create(
                        transaction_number=item["parsed_transaction_number"],
                        defaults={
                            "sender": sender,
                            "recipient": recipient,
                            "transfer_amount": item["transfer_amount"],
                            "message": item.get("message", ""),
                        },
                    )
                    transaction_created += int(created)
                    transaction_updated += int(not created)
        except ProtectedError as exc:
            raise CommandError(
                "--reset対象のAccountがJSON対象外のTransactionから参照されているため、"
                "安全のため処理を中断しました。参照中のTransactionを確認してください。"
            ) from exc
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(
                f"モックデータの登録中にエラーが発生したため、すべてロールバックしました: {exc}"
            ) from exc

        self.stdout.write(self.style.SUCCESS("モックデータの登録が完了しました。"))
        self.stdout.write(
            f"Account：新規{account_created}件，更新{account_updated}件"
        )
        self.stdout.write(
            "Transaction："
            f"新規{transaction_created}件，更新{transaction_updated}件"
        )

    def _load_and_validate(self, path):
        try:
            with path.open(encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as exc:
            raise CommandError(f"モックデータファイルが見つかりません: {path}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(
                f"mock_data.jsonのJSON形式が不正です（{exc.lineno}行{exc.colno}列）: "
                f"{exc.msg}"
            ) from exc

        if not isinstance(data, dict):
            raise CommandError("mock_data.jsonの最上位はオブジェクトにしてください。")
        if not isinstance(data.get("accounts"), list):
            raise CommandError("accountsは配列にしてください。")
        if not isinstance(data.get("transactions"), list):
            raise CommandError("transactionsは配列にしてください。")

        seen_accounts = set()
        for index, item in enumerate(data["accounts"]):
            location = f"accounts[{index}]"
            if not isinstance(item, dict):
                raise CommandError(f"{location}はオブジェクトにしてください。")
            account_number = item.get("account_number")
            if not isinstance(account_number, str) or not account_number.strip():
                raise CommandError(f"{location}.account_numberは空でない文字列にしてください。")
            if account_number in seen_accounts:
                raise CommandError(
                    f"{location}.account_numberがJSON内で重複しています: {account_number}"
                )
            seen_accounts.add(account_number)
            if not isinstance(item.get("user_name"), str) or not item["user_name"]:
                raise CommandError(f"{location}.user_nameは空でない文字列にしてください。")
            balance = item.get("account_balance")
            if type(balance) is not int or balance < 0:
                raise CommandError(
                    f"{location}.account_balanceは0以上の整数にしてください。"
                )

        seen_transactions = set()
        for index, item in enumerate(data["transactions"]):
            location = f"transactions[{index}]"
            if not isinstance(item, dict):
                raise CommandError(f"{location}はオブジェクトにしてください。")
            transaction_number = item.get("transaction_number")
            try:
                parsed_number = uuid.UUID(transaction_number)
            except (AttributeError, TypeError, ValueError) as exc:
                raise CommandError(
                    f"{location}.transaction_numberは正しいUUID形式にしてください: "
                    f"{transaction_number!r}"
                ) from exc
            if parsed_number in seen_transactions:
                raise CommandError(
                    f"{location}.transaction_numberがJSON内で重複しています: "
                    f"{transaction_number}"
                )
            seen_transactions.add(parsed_number)
            item["parsed_transaction_number"] = parsed_number

            amount = item.get("transfer_amount")
            if type(amount) is not int or amount < 1:
                raise CommandError(
                    f"{location}.transfer_amountは1以上の整数にしてください。"
                )
            sender = item.get("sender_account_number")
            recipient = item.get("recipient_account_number")
            if not isinstance(sender, str) or not sender.strip():
                raise CommandError(
                    f"{location}.sender_account_numberは空でない文字列にしてください。"
                )
            if not isinstance(recipient, str) or not recipient.strip():
                raise CommandError(
                    f"{location}.recipient_account_numberは空でない文字列にしてください。"
                )
            if sender == recipient:
                raise CommandError(
                    f"{location}のsender_account_numberとrecipient_account_numberは"
                    "同じ口座にできません。"
                )

        return data

    def _get_account(self, account_number, index, field_name):
        try:
            return Account.objects.get(account_number=account_number)
        except Account.DoesNotExist as exc:
            raise CommandError(
                f"transactions[{index}].{field_name}で指定された口座が存在しません: "
                f"{account_number}"
            ) from exc

"""共有JSONを各開発者のSQLiteへ投入するカスタム管理コマンド。

APIが利用するAccount、Transaction、Invoiceを、fixture形式ではない通常のJSONから
作成します。実行方法は `python manage.py seed_mock_data` です。
"""

import json
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.utils.dateparse import parse_datetime

from api.models import Account, Invoice, Transaction


User = get_user_model()


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
        invoice_created = 0
        invoice_updated = 0
        auth_user_created = 0
        auth_user_updated = 0

        try:
            # 3種類のデータの削除・作成を全部成功または全部取消にする。
            with transaction.atomic():
                if options["reset"]:
                    # 外部キー制約に従い、Invoice、Transaction、Accountの順で削除する。
                    invoice_numbers = [
                        item["parsed_invoice_number"] for item in data["invoices"]
                    ]
                    transaction_numbers = [
                        item["parsed_transaction_number"]
                        for item in data["transactions"]
                    ]
                    account_numbers = [
                        item["account_number"] for item in data["accounts"]
                    ]
                    Invoice.objects.filter(invoice_number__in=invoice_numbers).delete()
                    Transaction.objects.filter(
                        transaction_number__in=transaction_numbers
                    ).delete()
                    Account.objects.filter(account_number__in=account_numbers).delete()

                for item in data["accounts"]:
                    auth_user = None
                    if item.get("login_username"):
                        auth_user, user_created = User.objects.get_or_create(
                            username=item["login_username"]
                        )
                        auth_user.set_password(item["login_password"])
                        auth_user.save(update_fields=["password"])
                        auth_user_created += int(user_created)
                        auth_user_updated += int(not user_created)
                    account_defaults = {
                        "user_icon": item.get("user_icon", ""),
                        "user_name": item["user_name"],
                        "account_balance": item["account_balance"],
                    }
                    if auth_user is not None:
                        account_defaults["user"] = auth_user
                    # 口座番号が既存なら更新、なければ新規作成する。
                    _, created = Account.objects.update_or_create(
                        account_number=item["account_number"],
                        defaults=account_defaults,
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

                for index, item in enumerate(data["invoices"]):
                    issuer = self._get_account(
                        item["account_number"],
                        index,
                        "account_number",
                        "invoices",
                        item["invoice_number"],
                    )
                    payer = None
                    if item.get("paid_by") is not None:
                        payer = self._get_account(
                            item["paid_by"],
                            index,
                            "paid_by",
                            "invoices",
                            item["invoice_number"],
                        )
                    linked_transaction = None
                    if item.get("parsed_linked_transaction_number") is not None:
                        linked_transaction = self._get_transaction(
                            item["parsed_linked_transaction_number"],
                            index,
                            item["invoice_number"],
                        )

                    defaults = {
                        "invoice_amount": item["invoice_amount"],
                        "message": item.get("message", ""),
                        "account_number": issuer,
                        "invoice_flag": item["invoice_flag"],
                        "paid_time": item["parsed_paid_time"],
                        "paid_by": payer,
                        "transaction_number": linked_transaction,
                    }
                    invoice = Invoice.objects.filter(
                        invoice_number=item["parsed_invoice_number"]
                    ).first()
                    if invoice is None:
                        invoice = Invoice(
                            invoice_number=item["parsed_invoice_number"], **defaults
                        )
                    else:
                        for field_name, value in defaults.items():
                            setattr(invoice, field_name, value)
                    try:
                        invoice.full_clean()
                    except ValidationError as exc:
                        raise CommandError(
                            f"invoices[{index}]（invoice_number="
                            f"{item['invoice_number']}）の検証に失敗しました: {exc}"
                        ) from exc

                    _, created = Invoice.objects.update_or_create(
                        invoice_number=item["parsed_invoice_number"],
                        defaults=defaults,
                    )
                    invoice_created += int(created)
                    invoice_updated += int(not created)
        except ProtectedError as exc:
            raise CommandError(
                "--reset対象がJSON対象外の関連データから参照されているため、"
                "安全のため処理を中断しました。Invoice、Transaction、Accountの"
                "関連を確認してください。"
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
            f"AuthUser：新規{auth_user_created}件，更新{auth_user_updated}件"
        )
        self.stdout.write(
            "Transaction："
            f"新規{transaction_created}件，更新{transaction_updated}件"
        )
        self.stdout.write(
            f"Invoice：新規{invoice_created}件，更新{invoice_updated}件"
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
        if not isinstance(data.get("invoices"), list):
            raise CommandError("invoicesは配列にしてください。")

        seen_accounts = set()
        seen_login_usernames = set()
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
            login_username = item.get("login_username")
            login_password = item.get("login_password")
            if (login_username is None) != (login_password is None):
                raise CommandError(
                    f"{location}.login_usernameとlogin_passwordは両方設定するか、"
                    "両方省略してください。"
                )
            if login_username is not None:
                if not isinstance(login_username, str) or not login_username.strip():
                    raise CommandError(
                        f"{location}.login_usernameは空でない文字列にしてください。"
                    )
                if login_username in seen_login_usernames:
                    raise CommandError(
                        f"{location}.login_usernameがJSON内で重複しています: "
                        f"{login_username}"
                    )
                seen_login_usernames.add(login_username)
                if not isinstance(login_password, str) or len(login_password) < 8:
                    raise CommandError(
                        f"{location}.login_passwordは8文字以上の文字列にしてください。"
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

        seen_invoices = set()
        for index, item in enumerate(data["invoices"]):
            location = f"invoices[{index}]"
            if not isinstance(item, dict):
                raise CommandError(f"{location}はオブジェクトにしてください。")
            invoice_number = item.get("invoice_number")
            try:
                parsed_number = uuid.UUID(invoice_number)
            except (AttributeError, TypeError, ValueError) as exc:
                raise CommandError(
                    f"{location}.invoice_numberは正しいUUID形式にしてください: "
                    f"{invoice_number!r}"
                ) from exc
            invoice_location = (
                f"{location}（invoice_number={invoice_number}）"
            )
            if parsed_number in seen_invoices:
                raise CommandError(
                    f"{invoice_location}.invoice_numberがJSON内で重複しています。"
                )
            seen_invoices.add(parsed_number)
            item["parsed_invoice_number"] = parsed_number

            amount = item.get("invoice_amount")
            if type(amount) is not int or amount < 1:
                raise CommandError(
                    f"{invoice_location}.invoice_amountは1以上の整数にしてください。"
                )
            issuer = item.get("account_number")
            if not isinstance(issuer, str) or not issuer.strip():
                raise CommandError(
                    f"{invoice_location}.account_numberは空でない文字列にしてください。"
                )
            invoice_flag = item.get("invoice_flag")
            if invoice_flag not in Invoice.InvoiceFlag.values:
                raise CommandError(
                    f"{invoice_location}.invoice_flagはnotpayまたはpaidにしてください。"
                )

            paid_time = item.get("paid_time")
            parsed_paid_time = None
            if paid_time is not None:
                if not isinstance(paid_time, str):
                    parsed_paid_time = None
                else:
                    parsed_paid_time = parse_datetime(paid_time)
                if parsed_paid_time is None:
                    raise CommandError(
                        f"{invoice_location}.paid_timeは正しいISO 8601形式にしてください。"
                    )
            item["parsed_paid_time"] = parsed_paid_time

            payer = item.get("paid_by")
            if payer is not None and (
                not isinstance(payer, str) or not payer.strip()
            ):
                raise CommandError(
                    f"{invoice_location}.paid_byは口座番号の文字列またはnullにしてください。"
                )
            if payer is not None and payer == issuer:
                raise CommandError(
                    f"{invoice_location}.paid_byはaccount_numberと同じ口座にできません。"
                )

            linked_number = item.get("transaction_number")
            parsed_linked_number = None
            if linked_number is not None:
                try:
                    parsed_linked_number = uuid.UUID(linked_number)
                except (AttributeError, TypeError, ValueError) as exc:
                    raise CommandError(
                        f"{invoice_location}.transaction_numberは正しいUUID形式または"
                        "nullにしてください。"
                    ) from exc
            item["parsed_linked_transaction_number"] = parsed_linked_number

            payment_values = {
                "paid_time": paid_time,
                "paid_by": payer,
                "transaction_number": linked_number,
            }
            if invoice_flag == Invoice.InvoiceFlag.NOTPAY:
                for field_name, value in payment_values.items():
                    if value is not None:
                        raise CommandError(
                            f"{invoice_location}.{field_name}は未払い時にはnullにしてください。"
                        )
            else:
                for field_name, value in payment_values.items():
                    if value is None:
                        raise CommandError(
                            f"{invoice_location}.{field_name}は支払済み時には必須です。"
                        )

        return data

    def _get_account(
        self,
        account_number,
        index,
        field_name,
        collection="transactions",
        invoice_number=None,
    ):
        try:
            return Account.objects.get(account_number=account_number)
        except Account.DoesNotExist as exc:
            invoice_context = (
                f"（invoice_number={invoice_number}）" if invoice_number else ""
            )
            raise CommandError(
                f"{collection}[{index}]{invoice_context}.{field_name}で指定された"
                f"口座が存在しません: {account_number}"
            ) from exc

    def _get_transaction(self, transaction_number, index, invoice_number):
        try:
            return Transaction.objects.get(transaction_number=transaction_number)
        except Transaction.DoesNotExist as exc:
            raise CommandError(
                f"invoices[{index}]（invoice_number={invoice_number}）."
                f"transaction_numberで指定されたTransactionが存在しません: "
                f"{transaction_number}"
            ) from exc

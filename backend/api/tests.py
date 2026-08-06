"""モデル、モック投入、HTTP APIとDBの連携を確認する自動テスト。

テスト実行時はDjangoが一時的なテストDBを作るため、backend/db.sqlite3は
変更されません。実行コマンドは `python manage.py test api` です。
"""

import json
import tempfile
import uuid
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from api.management.commands.seed_mock_data import Command as SeedCommand
from api.models import Account, Invoice, Transaction


User = get_user_model()


class ModelTests(TestCase):
    """models.pyの関連とDB制約を、ORMから直接確認するテスト。"""
    def setUp(self):
        self.sender = Account.objects.create(
            account_number="2000001",
            user_name="送金者",
            account_balance=10000,
        )
        self.recipient = Account.objects.create(
            account_number="2000002",
            user_name="受取人",
            account_balance=5000,
        )

    def test_account_can_be_created(self):
        account = Account.objects.create(
            account_number="2000003",
            user_icon="/icons/test.png",
            user_name="テスト太郎",
            account_balance=3000,
        )

        self.assertEqual(account.user_name, "テスト太郎")
        self.assertEqual(str(account), "テスト太郎（2000003）")

    def test_account_balance_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Account.objects.create(
                account_number="2000004",
                user_name="残高不正",
                account_balance=-1,
            )

    def test_transaction_can_be_created(self):
        transfer = Transaction.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            transfer_amount=1000,
            message="テスト送金",
        )

        self.assertIsNotNone(transfer.created_at)
        self.assertEqual(
            str(transfer), "2000001 → 2000002：1000円"
        )

    def test_transfer_amount_cannot_be_zero_or_less(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Transaction.objects.create(
                        sender=self.sender,
                        recipient=self.recipient,
                        transfer_amount=amount,
                    )

    def test_sender_and_recipient_cannot_be_same(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Transaction.objects.create(
                sender=self.sender,
                recipient=self.sender,
                transfer_amount=100,
            )

    def test_sent_transactions_can_be_retrieved_from_account(self):
        transfer = Transaction.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            transfer_amount=100,
        )

        self.assertQuerySetEqual(self.sender.sent_transactions.all(), [transfer])

    def test_received_transactions_can_be_retrieved_from_account(self):
        transfer = Transaction.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            transfer_amount=100,
        )

        self.assertQuerySetEqual(self.recipient.received_transactions.all(), [transfer])


class InvoiceModelTests(TestCase):
    """Invoiceのフィールド、モデル検証、DB制約、関連を確認する。"""

    def setUp(self):
        self.issuer = Account.objects.create(
            account_number="2100001", user_name="請求者", account_balance=10000
        )
        self.payer = Account.objects.create(
            account_number="2100002", user_name="支払者", account_balance=10000
        )
        self.other = Account.objects.create(
            account_number="2100003", user_name="別口座", account_balance=10000
        )
        self.payment_transaction = Transaction.objects.create(
            sender=self.payer,
            recipient=self.issuer,
            transfer_amount=3000,
        )
        self.other_transaction = Transaction.objects.create(
            sender=self.other,
            recipient=self.issuer,
            transfer_amount=2000,
        )

    def _paid_invoice(self, **overrides):
        values = {
            "invoice_amount": 3000,
            "account_number": self.issuer,
            "invoice_flag": Invoice.InvoiceFlag.PAID,
            "paid_time": timezone.now(),
            "paid_by": self.payer,
            "transaction_number": self.payment_transaction,
        }
        values.update(overrides)
        return Invoice(**values)

    def test_unpaid_invoice_can_be_created(self):
        invoice = Invoice.objects.create(
            invoice_amount=2500,
            message="夕食代",
            account_number=self.issuer,
        )

        invoice.full_clean()
        self.assertIsInstance(invoice.invoice_number, uuid.UUID)
        self.assertIsNotNone(invoice.created_time)
        self.assertEqual(invoice.message, "夕食代")
        self.assertEqual(invoice.invoice_flag, Invoice.InvoiceFlag.NOTPAY)
        self.assertEqual(str(invoice), "請求者：2500円（未払い）")

    def test_paid_invoice_can_be_created(self):
        invoice = self._paid_invoice()
        invoice.full_clean()
        invoice.save()

        self.assertEqual(invoice.paid_by, self.payer)
        self.assertEqual(invoice.transaction_number, self.payment_transaction)
        self.assertEqual(str(invoice), "請求者：3000円（支払済み）")

    def test_invoice_number_is_uuid(self):
        invoice = Invoice.objects.create(
            invoice_amount=100, account_number=self.issuer
        )

        self.assertIsInstance(invoice.invoice_number, uuid.UUID)
        self.assertEqual(Invoice.objects.get(pk=str(invoice.pk)), invoice)

    def test_invoice_amount_cannot_be_zero_or_less(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):
                invoice = Invoice(
                    invoice_amount=amount, account_number=self.issuer
                )
                with self.assertRaises(ValidationError):
                    invoice.full_clean()
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Invoice.objects.create(
                        invoice_amount=amount, account_number=self.issuer
                    )

    def test_unknown_invoice_flag_is_rejected(self):
        invoice = Invoice(
            invoice_amount=100,
            account_number=self.issuer,
            invoice_flag="unknown",
        )
        with self.assertRaises(ValidationError):
            invoice.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Invoice.objects.create(
                invoice_amount=100,
                account_number=self.issuer,
                invoice_flag="unknown",
            )

    def test_unknown_issuer_account_is_rejected(self):
        invoice = Invoice(invoice_amount=100, account_number_id="9999999")

        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_unpaid_invoice_rejects_paid_time(self):
        invoice = Invoice(
            invoice_amount=100,
            account_number=self.issuer,
            paid_time=timezone.now(),
        )
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_unpaid_invoice_rejects_paid_by(self):
        invoice = Invoice(
            invoice_amount=100,
            account_number=self.issuer,
            paid_by=self.payer,
        )
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_unpaid_invoice_rejects_transaction_number(self):
        invoice = Invoice(
            invoice_amount=100,
            account_number=self.issuer,
            transaction_number=self.payment_transaction,
        )
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_paid_invoice_requires_paid_time(self):
        invoice = self._paid_invoice(paid_time=None)
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_paid_invoice_requires_paid_by(self):
        invoice = self._paid_invoice(paid_by=None)
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_paid_invoice_requires_transaction_number(self):
        invoice = self._paid_invoice(transaction_number=None)
        with self.assertRaises(ValidationError):
            invoice.full_clean()

    def test_issuer_and_payer_cannot_be_same(self):
        invoice = self._paid_invoice(paid_by=self.issuer)
        with self.assertRaises(ValidationError):
            invoice.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Invoice.objects.create(
                invoice_amount=3000,
                account_number=self.issuer,
                invoice_flag=Invoice.InvoiceFlag.PAID,
                paid_time=timezone.now(),
                paid_by=self.issuer,
                transaction_number=self.payment_transaction,
            )

    def test_transaction_cannot_be_linked_to_multiple_invoices(self):
        first = self._paid_invoice()
        first.full_clean()
        first.save()
        second = self._paid_invoice(invoice_number=uuid.uuid4())

        with self.assertRaises(ValidationError):
            second.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Invoice.objects.create(
                invoice_amount=3000,
                account_number=self.other,
                invoice_flag=Invoice.InvoiceFlag.PAID,
                paid_time=timezone.now(),
                paid_by=self.payer,
                transaction_number=self.payment_transaction,
            )


class SeedMockDataCommandTests(TestCase):
    """共有JSONの投入、更新、ロールバック、安全なresetを確認するテスト。"""
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.mock_data_path = Path(self.temp_directory.name) / "mock_data.json"

    def _default_data(self):
        return {
            "accounts": [
                {
                    "account_number": "3000001",
                    "login_username": "developer1",
                    "login_email": "developer1@example.com",
                    "login_password": "teamf-test-pass",
                    "user_icon": "/icons/a.png",
                    "user_name": "開発一郎",
                    "account_balance": 10000,
                },
                {
                    "account_number": "3000002",
                    "login_username": "developer2",
                    "login_email": "developer2@example.com",
                    "login_password": "teamf-test-pass",
                    "user_icon": "/icons/b.png",
                    "user_name": "開発花子",
                    "account_balance": 20000,
                },
            ],
            "transactions": [
                {
                    "transaction_number": "33333333-3333-4333-8333-333333333333",
                    "sender_account_number": "3000001",
                    "recipient_account_number": "3000002",
                    "transfer_amount": 500,
                    "message": "テストデータ",
                }
            ],
            "invoices": [
                {
                    "invoice_number": "55555555-5555-4555-8555-555555555555",
                    "invoice_amount": 500,
                    "message": "未払いテスト",
                    "account_number": "3000002",
                    "invoice_flag": "notpay",
                    "paid_time": None,
                    "paid_by": None,
                    "transaction_number": None,
                },
                {
                    "invoice_number": "66666666-6666-4666-8666-666666666666",
                    "invoice_amount": 500,
                    "message": "支払済みテスト",
                    "account_number": "3000002",
                    "invoice_flag": "paid",
                    "paid_time": "2026-08-05T15:00:00+09:00",
                    "paid_by": "3000001",
                    "transaction_number": "33333333-3333-4333-8333-333333333333",
                },
            ],
        }

    def _write_data(self, data):
        with self.mock_data_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False)

    def _seed(self, data=None, reset=False):
        self._write_data(self._default_data() if data is None else data)
        stdout = StringIO()
        with patch.object(
            SeedCommand, "get_mock_data_path", return_value=self.mock_data_path
        ):
            call_command("seed_mock_data", reset=reset, stdout=stdout)
        return stdout.getvalue()

    def test_first_run_registers_mock_data(self):
        output = self._seed()

        self.assertEqual(Account.objects.count(), 2)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Invoice.objects.count(), 2)
        self.assertTrue(User.objects.get(username="developer1").check_password(
            "teamf-test-pass"
        ))
        self.assertEqual(
            User.objects.get(username="developer1").email,
            "developer1@example.com",
        )
        self.assertIn("Account：新規2件，更新0件", output)
        self.assertIn("Transaction：新規1件，更新0件", output)
        self.assertIn("Invoice：新規2件，更新0件", output)

    def test_second_run_does_not_increase_record_count(self):
        self._seed()
        created_at = Transaction.objects.get().created_at
        invoice_created_time = Invoice.objects.get(
            pk="55555555-5555-4555-8555-555555555555"
        ).created_time
        output = self._seed()

        self.assertEqual(Account.objects.count(), 2)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Invoice.objects.count(), 2)
        self.assertEqual(Transaction.objects.get().created_at, created_at)
        self.assertEqual(
            Invoice.objects.get(
                pk="55555555-5555-4555-8555-555555555555"
            ).created_time,
            invoice_created_time,
        )
        self.assertIn("Account：新規0件，更新2件", output)
        self.assertIn("Transaction：新規0件，更新1件", output)
        self.assertIn("Invoice：新規0件，更新2件", output)

    def test_changed_json_updates_existing_data(self):
        data = self._default_data()
        self._seed(data)
        data["accounts"][0]["user_name"] = "更新済み"
        data["transactions"][0]["transfer_amount"] = 900
        data["invoices"][0]["invoice_amount"] = 900
        data["invoices"][0]["message"] = "更新済み請求"
        self._seed(data)

        self.assertEqual(Account.objects.get(pk="3000001").user_name, "更新済み")
        self.assertEqual(Transaction.objects.get().transfer_amount, 900)
        invoice = Invoice.objects.get(pk="55555555-5555-4555-8555-555555555555")
        self.assertEqual(invoice.invoice_amount, 900)
        self.assertEqual(invoice.message, "更新済み請求")

    def test_transaction_with_unknown_account_is_not_registered(self):
        existing = Account.objects.create(
            account_number="3000001", user_name="既存口座"
        )
        data = self._default_data()
        data["accounts"] = []
        data["transactions"][0]["recipient_account_number"] = "9999999"

        with self.assertRaisesMessage(CommandError, "9999999"):
            self._seed(data)

        self.assertTrue(Account.objects.filter(pk=existing.pk).exists())
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_error_rolls_back_accounts_created_before_failure(self):
        data = self._default_data()
        data["transactions"][0]["recipient_account_number"] = "9999999"

        with self.assertRaises(CommandError):
            self._seed(data)

        self.assertEqual(Account.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_invalid_invoice_rolls_back_all_mock_data(self):
        data = self._default_data()
        data["invoices"][1]["paid_by"] = "3999999"

        with self.assertRaisesMessage(CommandError, "paid_by"):
            self._seed(data)

        self.assertEqual(Account.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_reset_recreates_only_json_target_data(self):
        self._seed()
        Account.objects.filter(pk="3000001").update(user_name="手動変更")
        output = self._seed(reset=True)

        self.assertEqual(Account.objects.get(pk="3000001").user_name, "開発一郎")
        self.assertEqual(Account.objects.count(), 2)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Invoice.objects.count(), 2)
        self.assertIn("Account：新規2件，更新0件", output)
        self.assertIn("Transaction：新規1件，更新0件", output)
        self.assertIn("Invoice：新規2件，更新0件", output)

    def test_reset_recreates_json_invoices(self):
        self._seed()
        target = Invoice.objects.get(pk="55555555-5555-4555-8555-555555555555")
        original_created_time = target.created_time
        Invoice.objects.filter(pk=target.pk).update(message="手動変更")

        self._seed(reset=True)

        recreated = Invoice.objects.get(pk=target.pk)
        self.assertEqual(recreated.message, "未払いテスト")
        self.assertNotEqual(recreated.created_time, original_created_time)

    def test_reset_does_not_delete_data_absent_from_json(self):
        self._seed()
        manual_sender = Account.objects.create(
            account_number="3999998", user_name="手動送金者", account_balance=1000
        )
        manual_recipient = Account.objects.create(
            account_number="3999999", user_name="手動受取人", account_balance=1000
        )
        manual_transaction_number = uuid.uuid4()
        Transaction.objects.create(
            transaction_number=manual_transaction_number,
            sender=manual_sender,
            recipient=manual_recipient,
            transfer_amount=100,
        )
        manual_invoice_number = uuid.uuid4()
        Invoice.objects.create(
            invoice_number=manual_invoice_number,
            invoice_amount=100,
            account_number=manual_sender,
        )

        self._seed(reset=True)

        self.assertTrue(Account.objects.filter(pk="3999998").exists())
        self.assertTrue(Account.objects.filter(pk="3999999").exists())
        self.assertTrue(
            Transaction.objects.filter(pk=manual_transaction_number).exists()
        )
        self.assertTrue(Invoice.objects.filter(pk=manual_invoice_number).exists())

    def test_invoices_must_be_a_list(self):
        data = self._default_data()
        data["invoices"] = {}

        with self.assertRaisesMessage(CommandError, "invoicesは配列"):
            self._seed(data)

    def test_invoice_validation_message_identifies_number_and_field(self):
        data = self._default_data()
        data["invoices"][0]["invoice_amount"] = 0

        with self.assertRaisesMessage(
            CommandError,
            "55555555-5555-4555-8555-555555555555）.invoice_amount",
        ):
            self._seed(data)


class InvoiceAPITests(APITestCase):
    """請求の作成・取得・支払い・一覧がSQLiteと連携することを確認する。"""

    def setUp(self):
        self.issuer = Account.objects.create(
            account_number="5000001",
            user_name="請求元",
            account_balance=1000,
        )
        self.payer = Account.objects.create(
            account_number="5000002",
            user_name="支払元",
            account_balance=10000,
        )

    def _create_invoice(self, amount=3000, message="会食代"):
        return Invoice.objects.create(
            invoice_amount=amount,
            message=message,
            account_number=self.issuer,
        )

    def _payment_data(self, invoice, **overrides):
        data = {
            "my_account_number": self.payer.account_number,
            "invoice_account_number": self.issuer.account_number,
            "invoice_amount": str(invoice.invoice_amount),
            "message": "請求支払い",
        }
        data.update(overrides)
        return data

    def test_invoice_request_creates_database_record_and_link(self):
        response = self.client.post(
            "/api/user/5000001/invoice_request",
            {"invoice_amount": 2500, "message": "夕食代"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        invoice = Invoice.objects.get()
        self.assertEqual(invoice.invoice_amount, 2500)
        self.assertEqual(invoice.message, "夕食代")
        self.assertEqual(invoice.account_number, self.issuer)
        self.assertEqual(invoice.invoice_flag, Invoice.InvoiceFlag.NOTPAY)
        self.assertIsNotNone(invoice.created_time)
        self.assertEqual(
            response.data["invoice_link"],
            f"http://localhost:3000/invoice/{invoice.invoice_number}",
        )

    def test_invoice_request_rejects_invalid_amount(self):
        for amount in (0, -1, "3000"):
            with self.subTest(amount=amount):
                response = self.client.post(
                    "/api/user/5000001/invoice_request",
                    {"invoice_amount": amount},
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_invoice_info_reads_database_record(self):
        invoice = self._create_invoice()

        response = self.client.get(f"/api/{invoice.invoice_number}/get_inf")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["invoice_account_number"], "5000001")
        self.assertEqual(response.data["invoice_amount"], "3000")
        self.assertEqual(response.data["invoice_message"], "会食代")
        self.assertEqual(response.data["invoice_flag"], "notpay")

    def test_invoice_info_rejects_invalid_uuid(self):
        response = self.client.get("/api/not-a-uuid/get_inf")

        self.assertEqual(response.status_code, 404)

    def test_invoice_payment_updates_all_related_records_atomically(self):
        invoice = self._create_invoice()

        response = self.client.post(
            f"/api/{invoice.invoice_number}/pay",
            self._payment_data(invoice),
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.issuer.refresh_from_db()
        self.payer.refresh_from_db()
        invoice.refresh_from_db()
        transfer = Transaction.objects.get()
        self.assertEqual(self.issuer.account_balance, 4000)
        self.assertEqual(self.payer.account_balance, 7000)
        self.assertEqual(transfer.sender, self.payer)
        self.assertEqual(transfer.recipient, self.issuer)
        self.assertEqual(transfer.transfer_amount, 3000)
        self.assertEqual(invoice.invoice_flag, Invoice.InvoiceFlag.PAID)
        self.assertEqual(invoice.paid_by, self.payer)
        self.assertEqual(invoice.transaction_number, transfer)
        self.assertEqual(invoice.paid_time, transfer.created_at)

    def test_invoice_payment_rejects_tampered_amount_without_changes(self):
        invoice = self._create_invoice()

        response = self.client.post(
            f"/api/{invoice.invoice_number}/pay",
            self._payment_data(invoice, invoice_amount="1"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)
        self.payer.refresh_from_db()
        self.assertEqual(self.payer.account_balance, 10000)

    def test_invoice_payment_rejects_tampered_issuer_without_changes(self):
        invoice = self._create_invoice()

        response = self.client.post(
            f"/api/{invoice.invoice_number}/pay",
            self._payment_data(invoice, invoice_account_number="5000002"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_paid_invoice_cannot_be_paid_twice(self):
        invoice = self._create_invoice()
        payment_data = self._payment_data(invoice)
        self.client.post(
            f"/api/{invoice.invoice_number}/pay", payment_data, format="json"
        )

        second_response = self.client.post(
            f"/api/{invoice.invoice_number}/pay", payment_data, format="json"
        )

        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_invoice_payment_rejects_insufficient_balance(self):
        invoice = self._create_invoice(amount=10001)

        response = self.client.post(
            f"/api/{invoice.invoice_number}/pay",
            self._payment_data(invoice),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)
        invoice.refresh_from_db()
        self.assertEqual(invoice.invoice_flag, Invoice.InvoiceFlag.NOTPAY)

    def test_invoice_payment_rejects_missing_invoice(self):
        missing_invoice_number = uuid.uuid4()
        response = self.client.post(
            f"/api/{missing_invoice_number}/pay",
            {
                "my_account_number": "5000002",
                "invoice_account_number": "5000001",
                "invoice_amount": "3000",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_invoice_payment_rejects_issuer_as_payer(self):
        invoice = self._create_invoice()

        response = self.client.post(
            f"/api/{invoice.invoice_number}/pay",
            self._payment_data(invoice, my_account_number="5000001"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_invoice_list_reads_database_in_newest_first_order(self):
        older = self._create_invoice(message="古い請求")
        newer = self._create_invoice(message="新しい請求")
        Invoice.objects.filter(pk=older.pk).update(
            created_time=timezone.now() - timedelta(days=1)
        )

        response = self.client.get("/api/user/5000001/invoice_list")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["invoice_number"] for item in response.data["invoice_list"]],
            [str(newer.invoice_number), str(older.invoice_number)],
        )
        self.assertRegex(
            response.data["invoice_list"][0]["invoice_time"],
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}$",
        )

class AuthenticationAPITests(APITestCase):
    """新規登録、ログイン保持用トークン、認証済み口座APIを確認する。"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="login-user",
            email="login@example.com",
            password="strong-test-pass",
        )
        self.account = Account.objects.create(
            account_number="4100001",
            auth_user=self.user,
            user_name="ログイン利用者",
            account_balance=10000,
        )
        self.recipient = Account.objects.create(
            account_number="4100002",
            user_name="送金先",
            account_balance=1000,
        )

    def _authenticate(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return token

    def signup_data(self, **overrides):
        data = {
            "account_number": "4200001",
            "user_name": "新規利用者",
            "email": "new-user@example.com",
            "password": "Correct-Horse-57!",
        }
        data.update(overrides)
        return data

    def test_signup_creates_user_account_and_token(self):
        response = self.client.post(
            "/api/auth/signup/",
            self.signup_data(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        created_user = User.objects.get(email="new-user@example.com")
        self.assertTrue(created_user.check_password("Correct-Horse-57!"))
        self.assertEqual(created_user.bank_account.user_name, "新規利用者")
        self.assertEqual(created_user.bank_account.account_balance, 0)
        self.assertEqual(created_user.bank_account.account_number, "4200001")
        self.assertEqual(response.data["token"], created_user.auth_token.key)
        self.assertEqual(response.data["email"], "new-user@example.com")
        self.assertNotIn("password", response.data)
        self.assertNotIn("password", response.data["account"])

    def test_signup_creates_general_user_permissions(self):
        self.client.post("/api/auth/signup/", self.signup_data(), format="json")

        created_user = User.objects.get(email="new-user@example.com")
        self.assertTrue(created_user.is_active)
        self.assertFalse(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)

    def test_signup_links_user_and_account_one_to_one(self):
        self.client.post("/api/auth/signup/", self.signup_data(), format="json")

        created_user = User.objects.get(email="new-user@example.com")
        account = Account.objects.get(account_number="4200001")
        self.assertEqual(account.auth_user, created_user)
        self.assertEqual(created_user.bank_account, account)

    def test_signup_saves_normalized_values_in_separate_models(self):
        self.client.post(
            "/api/auth/signup/",
            self.signup_data(
                account_number=" 0123456 ",
                user_name=" 新規利用者 ",
                email=" NEW-USER@Example.COM ",
            ),
            format="json",
        )

        created_user = User.objects.get(email="new-user@example.com")
        account = Account.objects.get(pk="0123456")
        self.assertEqual(created_user.username, "new-user@example.com")
        self.assertEqual(account.account_number, "0123456")
        self.assertEqual(account.user_name, "新規利用者")
        self.assertEqual(account.user_icon, "")
        self.assertEqual(account.account_balance, 0)

    def test_signup_hashes_password_and_account_has_no_password_field(self):
        plain_password = "Correct-Horse-57!"
        self.client.post(
            "/api/auth/signup/",
            self.signup_data(password=plain_password),
            format="json",
        )

        created_user = User.objects.get(email="new-user@example.com")
        self.assertNotEqual(created_user.password, plain_password)
        self.assertTrue(created_user.check_password(plain_password))
        self.assertNotIn("password", [field.name for field in Account._meta.fields])

    def test_signup_rejects_duplicate_email_without_creating_account(self):
        response = self.client.post(
            "/api/auth/signup/",
            self.signup_data(email="LOGIN@example.com"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["email"],
            ["このメールアドレスは既に使用されています。"],
        )
        self.assertEqual(Account.objects.count(), 2)

    def test_signup_rejects_duplicate_account_number(self):
        response = self.client.post(
            "/api/auth/signup/",
            self.signup_data(account_number="4100001"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["account_number"],
            ["この口座番号は既に使用されています。"],
        )
        self.assertFalse(User.objects.filter(email="new-user@example.com").exists())

    def test_signup_rejects_invalid_account_number(self):
        response = self.client.post(
            "/api/auth/signup/",
            self.signup_data(account_number="0012A45"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("account_number", response.data)

    def test_signup_rejects_invalid_email(self):
        response = self.client.post(
            "/api/auth/signup/",
            self.signup_data(email="not-an-email"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    def test_signup_rejects_weak_password(self):
        response = self.client.post(
            "/api/auth/signup/",
            self.signup_data(password="12345678"),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email="new-user@example.com").exists())

    @patch("api.views.Account.objects.create", side_effect=IntegrityError("failure"))
    def test_signup_rolls_back_user_if_account_creation_fails(self, _mock_create):
        response = self.client.post(
            "/api/auth/signup/", self.signup_data(), format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="new-user@example.com").exists())

    def test_login_returns_token_and_account(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "LOGIN@example.com", "password": "strong-test-pass"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["account"]["account_number"], "4100001")
        self.assertEqual(response.data["email"], "login@example.com")
        self.assertTrue(Token.objects.filter(key=response.data["token"]).exists())

    def test_login_failure_does_not_reveal_invalid_field(self):
        wrong_password_response = self.client.post(
            "/api/auth/login/",
            {"email": "login@example.com", "password": "wrong-password"},
            format="json",
        )
        unknown_email_response = self.client.post(
            "/api/auth/login/",
            {"email": "unknown@example.com", "password": "strong-test-pass"},
            format="json",
        )

        self.assertEqual(wrong_password_response.status_code, 400)
        self.assertEqual(unknown_email_response.status_code, 400)
        self.assertEqual(wrong_password_response.data, unknown_email_response.data)
        self.assertEqual(
            wrong_password_response.data["error"],
            "メールアドレスまたはパスワードが正しくありません。",
        )
        self.assertEqual(Token.objects.count(), 0)

    def test_login_without_linked_account_uses_same_generic_error(self):
        User.objects.create_user(
            username="no-account",
            email="no-account@example.com",
            password="strong-test-pass",
        )

        response = self.client.post(
            "/api/auth/login/",
            {"email": "no-account@example.com", "password": "strong-test-pass"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"],
            "メールアドレスまたはパスワードが正しくありません。",
        )

    def test_current_user_requires_authentication(self):
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 401)

    def test_current_user_returns_linked_account(self):
        self._authenticate()

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "login@example.com")
        self.assertEqual(response.data["account_number"], "4100001")
        self.assertEqual(response.data["account"]["account_number"], "4100001")
        self.assertNotIn("password", response.data)

    def test_general_user_cannot_access_django_admin(self):
        self.client.force_authenticate(user=None)
        self.client.force_login(self.user)

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_logout_invalidates_token(self):
        token = self._authenticate()

        response = self.client.post("/api/auth/logout/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Token.objects.filter(key=token.key).exists())

    def test_authenticated_transfer_uses_logged_in_account_as_sender(self):
        self._authenticate()

        response = self.client.post(
            "/api/transfers/4100002",
            {"transfer_amount": 750, "message": "認証送金"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        transfer = Transaction.objects.get()
        self.assertEqual(transfer.sender, self.account)
        self.assertEqual(transfer.recipient, self.recipient)
        self.account.refresh_from_db()
        self.assertEqual(self.account.account_balance, 9250)


class AuthenticatedInvoiceAPITests(APITestCase):
    """React請求画面用APIが認証口座とInvoice DBを使用することを確認する。"""

    def setUp(self):
        self.issuer_user = User.objects.create_user(
            username="invoice-issuer@example.com",
            email="invoice-issuer@example.com",
            password="strong-test-pass",
        )
        self.issuer = Account.objects.create(
            account_number="4300001",
            auth_user=self.issuer_user,
            user_name="請求者",
            account_balance=1000,
        )
        self.payer_user = User.objects.create_user(
            username="invoice-payer@example.com",
            email="invoice-payer@example.com",
            password="strong-test-pass",
        )
        self.payer = Account.objects.create(
            account_number="4300002",
            auth_user=self.payer_user,
            user_name="支払者",
            account_balance=10000,
        )

    def authenticate(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_authenticated_user_creates_invoice_for_own_account(self):
        self.authenticate(self.issuer_user)

        response = self.client.post(
            "/api/invoices/",
            {"invoice_amount": 2500, "message": "夕食代"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        invoice = Invoice.objects.get(invoice_number=response.data["invoice_number"])
        self.assertEqual(invoice.account_number, self.issuer)
        self.assertEqual(invoice.invoice_amount, 2500)
        self.assertEqual(invoice.message, "夕食代")
        self.assertEqual(
            response.data["invoice_link"],
            f"http://localhost:3000/invoice/{invoice.invoice_number}",
        )

    def test_invoice_collection_requires_authentication(self):
        response = self.client.get("/api/invoices/")

        self.assertEqual(response.status_code, 401)

    def test_invoice_list_returns_only_logged_in_users_invoices(self):
        mine = Invoice.objects.create(
            invoice_amount=2500,
            message="自分の請求",
            account_number=self.issuer,
        )
        Invoice.objects.create(
            invoice_amount=3000,
            message="他人の請求",
            account_number=self.payer,
        )
        self.authenticate(self.issuer_user)

        response = self.client.get("/api/invoices/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["invoice_list"]), 1)
        self.assertEqual(
            response.data["invoice_list"][0]["invoice_number"], str(mine.invoice_number)
        )
        self.assertEqual(response.data["invoice_list"][0]["message"], "自分の請求")

    def test_invoice_detail_uses_uuid_and_returns_database_data(self):
        invoice = Invoice.objects.create(
            invoice_amount=2500,
            message="詳細確認",
            account_number=self.issuer,
        )
        self.authenticate(self.payer_user)

        response = self.client.get(f"/api/invoices/{invoice.invoice_number}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["invoice_amount"], 2500)
        self.assertEqual(response.data["message"], "詳細確認")
        self.assertEqual(response.data["issuer"]["account_number"], "4300001")

    def test_payment_uses_logged_in_account_and_updates_all_database_records(self):
        invoice = Invoice.objects.create(
            invoice_amount=2500,
            message="支払い確認",
            account_number=self.issuer,
        )
        self.authenticate(self.payer_user)

        response = self.client.post(
            f"/api/invoices/{invoice.invoice_number}/pay/", {}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.issuer.refresh_from_db()
        self.payer.refresh_from_db()
        self.assertEqual(invoice.invoice_flag, Invoice.InvoiceFlag.PAID)
        self.assertEqual(invoice.paid_by, self.payer)
        self.assertIsNotNone(invoice.paid_time)
        self.assertIsNotNone(invoice.transaction_number)
        self.assertEqual(invoice.transaction_number.sender, self.payer)
        self.assertEqual(invoice.transaction_number.recipient, self.issuer)
        self.assertEqual(self.payer.account_balance, 7500)
        self.assertEqual(self.issuer.account_balance, 3500)
        self.assertEqual(
            response.data["transaction_number"],
            str(invoice.transaction_number_id),
        )

        self.client.credentials()
        self.authenticate(self.issuer_user)
        list_response = self.client.get("/api/invoices/")
        paid_invoice = list_response.data["invoice_list"][0]
        self.assertEqual(paid_invoice["invoice_flag"], "paid")
        self.assertEqual(paid_invoice["paid_by"]["account_number"], "4300002")
        self.assertEqual(paid_invoice["paid_by"]["user_name"], "支払者")

    def test_issuer_cannot_pay_own_invoice(self):
        invoice = Invoice.objects.create(
            invoice_amount=500,
            account_number=self.issuer,
        )
        self.authenticate(self.issuer_user)

        response = self.client.post(
            f"/api/invoices/{invoice.invoice_number}/pay/", {}, format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)


class TransferAPITests(APITestCase):
    """HTTPリクエスト→View→ORM→テストDB→レスポンスの全経路を確認する。"""
    def setUp(self):
        self.user = User.objects.create_user(
            username="transfer-user", password="strong-test-pass"
        )
        self.sender = Account.objects.create(
            account_number="4000001",
            auth_user=self.user,
            user_icon="/icons/sender.png",
            user_name="API送金者",
            account_balance=10000,
        )
        self.recipient = Account.objects.create(
            account_number="4000002",
            user_icon="/icons/recipient.png",
            user_name="API受取人",
            account_balance=2000,
        )
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_summary_api_reads_account_from_database(self):
        response = self.client.get("/api/user/4000001/summary")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user_name"], "API送金者")
        self.assertEqual(response.data["account_balance"], 10000)

    def test_recipient_list_api_excludes_sender(self):
        response = self.client.get("/api/user/4000001/recipient_list")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["recipient_list"]), 1)
        self.assertEqual(
            response.data["recipient_list"][0]["account_number"], "4000002"
        )

    def test_recipient_info_api_reads_both_accounts(self):
        response = self.client.get("/api/user/4000001/4000002/recipient")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["recipient_name"], "API受取人")
        self.assertEqual(response.data["sender_account_balance"], 10000)

    def test_transfer_api_updates_balances_and_creates_history(self):
        response = self.client.post(
            "/api/user/4000001/4000002/transfer",
            {"transfer_amount": 1500, "message": "API連携テスト"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.sender.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(self.sender.account_balance, 8500)
        self.assertEqual(self.recipient.account_balance, 3500)
        transfer = Transaction.objects.get()
        self.assertEqual(transfer.transfer_amount, 1500)
        self.assertEqual(transfer.message, "API連携テスト")
        self.assertEqual(
            response.data["transaction_number"], str(transfer.transaction_number)
        )

    def test_transfer_api_rejects_zero_amount_without_changing_database(self):
        response = self.client.post(
            "/api/user/4000001/4000002/transfer",
            {"transfer_amount": 0},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.sender.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(self.sender.account_balance, 10000)
        self.assertEqual(self.recipient.account_balance, 2000)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_transfer_api_rejects_insufficient_balance(self):
        response = self.client.post(
            "/api/user/4000001/4000002/transfer",
            {"transfer_amount": 10001},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Insufficient account balance")
        self.assertEqual(Transaction.objects.count(), 0)

    def test_transfer_api_rejects_same_sender_and_recipient(self):
        response = self.client.post(
            "/api/user/4000001/4000001/transfer",
            {"transfer_amount": 100},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_transfer_api_rejects_unknown_account(self):
        response = self.client.post(
            "/api/user/4000001/4999999/transfer",
            {"transfer_amount": 100},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_transfer_api_rejects_spoofed_sender(self):
        response = self.client.post(
            "/api/user/4000002/4000001/transfer",
            {"transfer_amount": 100},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Transaction.objects.count(), 0)

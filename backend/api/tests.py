"""モデル、モック投入、HTTP APIとDBの連携を確認する自動テスト。

テスト実行時はDjangoが一時的なテストDBを作るため、backend/db.sqlite3は
変更されません。実行コマンドは `python manage.py test api` です。
"""

import json
import tempfile
import uuid
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APITestCase

from api.management.commands.seed_mock_data import Command as SeedCommand
from api.models import Account, Transaction


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
                    "user_icon": "/icons/a.png",
                    "user_name": "開発一郎",
                    "account_balance": 10000,
                },
                {
                    "account_number": "3000002",
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
        self.assertIn("Account：新規2件，更新0件", output)
        self.assertIn("Transaction：新規1件，更新0件", output)

    def test_second_run_does_not_increase_record_count(self):
        self._seed()
        created_at = Transaction.objects.get().created_at
        output = self._seed()

        self.assertEqual(Account.objects.count(), 2)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.get().created_at, created_at)
        self.assertIn("Account：新規0件，更新2件", output)
        self.assertIn("Transaction：新規0件，更新1件", output)

    def test_changed_json_updates_existing_data(self):
        data = self._default_data()
        self._seed(data)
        data["accounts"][0]["user_name"] = "更新済み"
        data["transactions"][0]["transfer_amount"] = 900
        self._seed(data)

        self.assertEqual(Account.objects.get(pk="3000001").user_name, "更新済み")
        self.assertEqual(Transaction.objects.get().transfer_amount, 900)

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

    def test_error_rolls_back_accounts_created_before_failure(self):
        data = self._default_data()
        data["transactions"][0]["recipient_account_number"] = "9999999"

        with self.assertRaises(CommandError):
            self._seed(data)

        self.assertEqual(Account.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_reset_recreates_only_json_target_data(self):
        self._seed()
        Account.objects.filter(pk="3000001").update(user_name="手動変更")
        output = self._seed(reset=True)

        self.assertEqual(Account.objects.get(pk="3000001").user_name, "開発一郎")
        self.assertEqual(Account.objects.count(), 2)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertIn("Account：新規2件，更新0件", output)
        self.assertIn("Transaction：新規1件，更新0件", output)

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

        self._seed(reset=True)

        self.assertTrue(Account.objects.filter(pk="3999998").exists())
        self.assertTrue(Account.objects.filter(pk="3999999").exists())
        self.assertTrue(
            Transaction.objects.filter(pk=manual_transaction_number).exists()
        )


class TransferAPITests(APITestCase):
    """HTTPリクエスト→View→ORM→テストDB→レスポンスの全経路を確認する。"""
    def setUp(self):
        self.sender = Account.objects.create(
            account_number="4000001",
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

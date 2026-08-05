"""
API 自動テストコード (tests.py)
DjangoおよびDjango REST FrameworkのAPITestCaseを利用し、
フロントエンドなしでバックエンドおよびデータベースの動作を包括的にテストします。
"""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from config.config import AppConfig

# models.pyが定義されている前提でインポート
try:
    from api.models import UserAccount, TransferTransaction
except ImportError:
    UserAccount = None
    TransferTransaction = None


class BaseAPITestCase(APITestCase):
    """構成クラスを参照する基底テストケースクラス"""
    config = AppConfig

class TransferAPITestCase(BaseAPITestCase):
    """
    送金システム API 全Stepの自動テストクラス
    """
    def setUp(self):
        """
        各テスト実行前に自動実行される初期化処理。
        テスト専用のインメモリデータベース上にテストデータを投入します。
        """
        if UserAccount is not None:
            # テストデータ 1: 送金元（山田太郎）
            self.user1 = UserAccount.objects.create(
                account_number="123456",
                user_icon="/static/user1.png",
                user_name="山田太郎",
                account_balance=100000
            )
            # テストデータ 2: 送金先（佐藤花子）
            self.user2 = UserAccount.objects.create(
                account_number="654321",
                user_icon="/static/user2.png",
                user_name="佐藤花子",
                account_balance=50000
            )

    def test_step1_user_summary(self):
        """Step 1: ユーザ口座情報取得 API のテスト"""
        if UserAccount is None:
            self.skipTest("UserAccount model is not defined yet.")

        url = reverse("user-summary", kwargs={"account_number": "123456"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["account_number"], "123456")
        self.assertEqual(response.data["user_name"], "山田太郎")
        self.assertEqual(response.data["account_balance"], 100000)

    def test_step2_recipient_list(self):
        """Step 2: 送金先一覧取得 API のテスト"""
        if UserAccount is None:
            self.skipTest("UserAccount model is not defined yet.")

        url = reverse("recipient-list", kwargs={"account_number": "123456"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("recipient_list", response.data)
        # 自分(123456)以外の送金先(654321)が含まれているか検証
        self.assertEqual(len(response.data["recipient_list"]), 1)
        self.assertEqual(response.data["recipient_list"][0]["account_number"], "654321")

    def test_step3_recipient_info(self):
        """Step 3: 送信先処理画面取得 API のテスト"""
        if UserAccount is None:
            self.skipTest("UserAccount model is not defined yet.")

        url = reverse("recipient-info", kwargs={
            "sender_account_number": "123456",
            "recipient_account_number": "654321"
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sender_account_number"], "123456")
        self.assertEqual(response.data["recipient_name"], "佐藤花子")

    def test_step4_transfer_execution(self):
        """Step 4: 送金処理 API のテスト (残高減算・加算の検証)"""
        if UserAccount is None:
            self.skipTest("UserAccount model is not defined yet.")

        url = reverse("transfer", kwargs={
            "sender_account_number": "123456",
            "recipient_account_number": "654321"
        })
        payload = {
            "transfer_amount": 30000,
            "message": "ランチ代お返し"
        }
        
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # データベースを再検索して残高が正しく移動したか検証
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()

        # 送金元: 100,000 - 30,000 = 70,000 円
        self.assertEqual(self.user1.account_balance, 70000)
        # 送金先: 50,000 + 30,000 = 80,000 円
        self.assertEqual(self.user2.account_balance, 80000)

        # 送金履歴レコードが作成されたか検証
        if TransferTransaction is not None:
            self.assertEqual(TransferTransaction.objects.count(), 1)
            tx = TransferTransaction.objects.first()
            self.assertEqual(tx.transfer_amount, 30000)
            self.assertEqual(tx.message, "ランチ代お返し")

    def test_step4_transfer_insufficient_balance(self):
        """Step 4: 残高不足時のエラーレスポンス (400 Bad Request) テスト"""
        if UserAccount is None:
            self.skipTest("UserAccount model is not defined yet.")

        url = reverse("transfer", kwargs={
            "sender_account_number": "123456",
            "recipient_account_number": "654321"
        })
        # 残高100,000円に対して 150,000円の過剰送金リクエスト
        payload = {
            "transfer_amount": 150000,
            "message": "高額送金"
        }
        
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

        # データベースの残高が変動していないことを検証
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.assertEqual(self.user1.account_balance, 100000)
        self.assertEqual(self.user2.account_balance, 50000)

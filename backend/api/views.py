"""
API ビュークラス定義 (views.py)
"""
import uuid
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
try:
    from api.models import UserAccount, TransferTransaction
except ImportError:
    UserAccount = None
    TransferTransaction = None

from config.config import AppConfig


class BaseAPIView(APIView):
    """構成クラスを継承・保持するAPI基底クラス"""
    config = AppConfig


class UserSummaryView(BaseAPIView):
    """
    Step 1: ユーザ口座情報取得
    GET /api/user/{account_number}/summary
    """
    def get(self, request, account_number: str):
        if UserAccount is None:
            return Response({"error": "Model not defined yet"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            user = UserAccount.objects.get(account_number=account_number)
            data = {
                "account_number": user.account_number,
                "user_icon": user.user_icon,
                "user_name": user.user_name,
                "account_balance": user.account_balance,
            }
            return Response(data, status=status.HTTP_200_OK)
        except UserAccount.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class RecipientListView(BaseAPIView):
    """
    Step 2: 送金先一覧の取得
    GET /api/user/{account_number}/recipient_list
    """
    def get(self, request, account_number: str):
        if UserAccount is None:
            return Response({"error": "Model not defined yet"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        users = UserAccount.objects.exclude(account_number=account_number)
        recipient_list = [
            {
                "account_number": user.account_number,
                "user_icon": user.user_icon,
                "user_name": user.user_name,
            }
            for user in users
        ]
        return Response({"recipient_list": recipient_list}, status=status.HTTP_200_OK)


class RecipientInfoView(BaseAPIView):
    """
    Step 3 (Step 4表記): 送信先処理画面取得
    GET /api/user/{sender_account_number}/{recipient_account_number}/recipient
    """
    def get(self, request, sender_account_number: str, recipient_account_number: str):
        if UserAccount is None:
            return Response({"error": "Model not defined yet"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            sender = UserAccount.objects.get(account_number=sender_account_number)
            recipient = UserAccount.objects.get(account_number=recipient_account_number)
            
            data = {
                "sender_account_number": sender.account_number,
                "sender_bank_balance": sender.account_balance,
                "recipient_icon": recipient.user_icon,
                "recipient_name": recipient.user_name,
            }
            return Response(data, status=status.HTTP_200_OK)
        except UserAccount.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)


class TransferView(BaseAPIView):
    """
    Step 4: 送金処理
    POST /api/user/{sender_account_number}/{recipient_account_number}/transfer
    """
    def post(self, request, sender_account_number: str, recipient_account_number: str):
        if UserAccount is None:
            return Response({"error": "Model not defined yet"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        transfer_amount = request.data.get("transfer_amount")
        message = request.data.get("message", None)

        if transfer_amount is None:
            return Response({"error": "transfer_amount is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 悲観的ロック (select_for_update) により競合状態 (Race Condition) を防止
                sender = UserAccount.objects.select_for_update().get(account_number=sender_account_number)
                recipient = UserAccount.objects.select_for_update().get(account_number=recipient_account_number)

                # 1. 自身の預金残高から送金金額を減算
                sender.account_balance -= int(transfer_amount)
                
                # 2. 送金宛先の預金残高に送金金額を加算
                recipient.account_balance += int(transfer_amount)

                # 変更をデータベースに保存
                sender.save()
                recipient.save()

                # 3. 送金履歴の保存 (モデルが存在する場合)
                if TransferTransaction is not None:
                    TransferTransaction.objects.create(
                        transaction_number=str(uuid.uuid4()),
                        sender_account=sender,
                        recipient_account=recipient,
                        transfer_amount=int(transfer_amount),
                        message=message,
                    )

            # 正常終了時 200 OK
            return Response(status=status.HTTP_200_OK)
        except UserAccount.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

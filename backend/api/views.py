"""
API ビュークラス定義 (views.py)
"""
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.models import Account, Transaction


class UserSummaryView(APIView):
    """
    Step 1: ユーザ口座情報取得
    GET /api/user/{account_number}/summary
    """
    def get(self, request, account_number: str):
        try:
            # API連携ポイント: Reactトップ画面へAccountの現在値を返す。
            user = Account.objects.get(account_number=account_number)
            data = {
                "account_number": user.account_number,
                "user_icon": user.user_icon,
                "user_name": user.user_name,
                "account_balance": user.account_balance,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class RecipientListView(APIView):
    """
    Step 3: 送金先一覧の取得
    GET /api/user/{account_number}/recipient_list
    """
    def get(self, request, account_number: str):
        # API連携ポイント: React送金先一覧へ送金元以外のAccountを返す。
        if not Account.objects.filter(account_number=account_number).exists():
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        users = Account.objects.exclude(account_number=account_number)
        recipient_list = [
            {
                "account_number": user.account_number,
                "user_icon": user.user_icon,
                "user_name": user.user_name,
            }
            for user in users
        ]
        return Response({"recipient_list": recipient_list}, status=status.HTTP_200_OK)


class RecipientInfoView(APIView):
    """
    Step 4: 送金処理画面情報取得
    GET /api/user/{sender_account_number}/{recipient_account_number}/recipient
    """
    def get(self, request, sender_account_number: str, recipient_account_number: str):
        try:
            # API連携ポイント: React送金画面へ送金元残高と送金先情報を返す。
            sender = Account.objects.get(account_number=sender_account_number)
            recipient = Account.objects.get(account_number=recipient_account_number)

            data = {
                "sender_account_number": sender.account_number,
                "sender_account_balance": sender.account_balance,
                "recipient_account_number": recipient.account_number,
                "recipient_icon": recipient.user_icon,
                "recipient_name": recipient.user_name,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)


class TransferView(APIView):
    """
    Step 5・6: 送金処理, メッセージ
    POST /api/user/{sender_account_number}/{recipient_account_number}/transfer
    """
    def post(self, request, sender_account_number: str, recipient_account_number: str):
        transfer_amount = request.data.get("transfer_amount")
        message = request.data.get("message", "")

        if transfer_amount is None:
            return Response({"error": "transfer_amount is required"}, status=status.HTTP_400_BAD_REQUEST)
        if type(transfer_amount) is not int or transfer_amount < 1:
            return Response(
                {"error": "transfer_amount must be an integer greater than or equal to 1"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if sender_account_number == recipient_account_number:
            return Response(
                {"error": "Sender and recipient must be different"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if message is None:
            message = ""
        if not isinstance(message, str) or len(message) > 200:
            return Response(
                {"error": "message must be a string of 200 characters or fewer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # API・DB連携ポイント: 送金元と送金先をロックし、残高更新と履歴登録を
                # 1つのトランザクションとして実行する。途中で失敗した場合は全て戻る。
                sender = Account.objects.select_for_update().get(account_number=sender_account_number)
                recipient = Account.objects.select_for_update().get(account_number=recipient_account_number)

                if sender.account_balance < transfer_amount:
                    return Response({"error": "Insufficient account balance"}, status=status.HTTP_400_BAD_REQUEST)

                sender.account_balance -= transfer_amount
                recipient.account_balance += transfer_amount
                sender.save(update_fields=["account_balance"])
                recipient.save(update_fields=["account_balance"])

                transfer = Transaction.objects.create(
                    sender=sender,
                    recipient=recipient,
                    transfer_amount=transfer_amount,
                    message=message,
                )

            return Response(
                {
                    "transaction_number": str(transfer.transaction_number),
                    "sender_account_number": sender.account_number,
                    "recipient_account_number": recipient.account_number,
                    "transfer_amount": transfer.transfer_amount,
                    "message": transfer.message,
                    "sender_account_balance": sender.account_balance,
                },
                status=status.HTTP_200_OK,
            )
        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

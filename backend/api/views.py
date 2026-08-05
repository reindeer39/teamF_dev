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
            sender = Account.objects.get(account_number=sender_account_number)
            recipient = Account.objects.get(account_number=recipient_account_number)

            data = {
                "sender_account_number": sender.account_number,
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
        message = request.data.get("message", None)

        if transfer_amount is None:
            return Response({"error": "transfer_amount is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 悲観的ロック (select_for_update) により競合状態 (Race Condition) を防止
                sender = Account.objects.select_for_update().get(account_number=sender_account_number)
                recipient = Account.objects.select_for_update().get(account_number=recipient_account_number)

                # 0. 残高不足チェック (バックエンド側でのバリデーション制御)
                if sender.account_balance < int(transfer_amount):
                    return Response({"error": "Insufficient account balance"}, status=status.HTTP_400_BAD_REQUEST)

                # 1. 自身の預金残高から送金金額を減算
                sender.account_balance -= int(transfer_amount)

                # 2. 送金宛先の預金残高に送金金額を加算
                recipient.account_balance += int(transfer_amount)

                # 変更をデータベースに保存
                sender.save()
                recipient.save()

                # 3. 送金履歴の保存
                Transaction.objects.create(
                    sender=sender,
                    recipient=recipient,
                    transfer_amount=int(transfer_amount),
                    message=message or "",
                )

            # 正常終了時 200 OK
            return Response(status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

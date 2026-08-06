"""React向けAPIの受付、入力検証、DB操作、JSON応答を担当するView。

処理は config/urls.py → api/urls.py → このファイルの順で到着します。
`Account.objects...`などがDjango ORMによるDB操作、`Response(...)`が
Reactへ返すJSONレスポンスです。詳しい流れはBACKEND_FLOW_GUIDE.mdを参照。
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.models import Account, Invoice, Transaction


class UserSummaryView(APIView):
    """
    Step 1: ユーザ口座情報取得
    GET /api/user/{account_number}/summary
    """
    def get(self, request, account_number: str):
        try:
            # API連携ポイント: Reactトップ画面へAccountの現在値を返す。
            # DB操作: URLから受け取った口座番号を主キーとしてaccountsを1件検索。
            user = Account.objects.get(account_number=account_number)
            # Accountオブジェクトを、Reactが扱える辞書（JSONの元）へ変換する。
            data = {
                "account_number": user.account_number,
                "user_icon": user.user_icon,
                "user_name": user.user_name,
                "account_balance": user.account_balance,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            # get()で該当口座がない場合は、成功ではなく404をReactへ返す。
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class RecipientListView(APIView):
    """
    Step 3: 送金先一覧の取得
    GET /api/user/{account_number}/recipient_list
    """
    def get(self, request, account_number: str):
        # API連携ポイント: React送金先一覧へ送金元以外のAccountを返す。
        # 最初に送金元自体が存在するか確認し、誤ったURLなら404にする。
        if not Account.objects.filter(account_number=account_number).exists():
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # DB操作: 自分自身を除外したaccountsのQuerySetを取得する。
        users = Account.objects.exclude(account_number=account_number)
        # QuerySetの各Accountを、Reactで一覧表示しやすい配列へ変換する。
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
            # DB操作: 送金元と送金先をそれぞれaccountsから取得する。
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
        # ReactがPOSTしたJSONは、DRFによりrequest.dataへ変換される。
        transfer_amount = request.data.get("transfer_amount")
        message = request.data.get("message", "")

        # DB操作前の入力検証。不正な場合は残高や履歴を一切変更しない。
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

                # DBの最新残高を取得した後で、残高不足を再確認する。
                if sender.account_balance < transfer_amount:
                    return Response({"error": "Insufficient account balance"}, status=status.HTTP_400_BAD_REQUEST)

                sender.account_balance -= transfer_amount
                recipient.account_balance += transfer_amount
                # DB操作: accountsテーブルの残高カラムだけをUPDATEする。
                sender.save(update_fields=["account_balance"])
                recipient.save(update_fields=["account_balance"])

                # DB操作: transactionsテーブルへ送金履歴をINSERTする。
                transfer = Transaction.objects.create(
                    sender=sender,
                    recipient=recipient,
                    transfer_amount=transfer_amount,
                    message=message,
                )

            # DB確定後、取引番号と更新後残高をJSONでReactへ返す。
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
            # 送金元または送金先が存在しない場合。atomic内の変更は取り消される。
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)


class InvoiceRequestView(APIView):
    """
    Step 7: 請求のリクエスト
    POST /api/user/{account_number}/invoice_request
    """
    def post(self, request, account_number: str):
        invoice_amount = request.data.get("invoice_amount")
        message = request.data.get("message", "")

        if invoice_amount is None:
            return Response(
                {"error": "Not enough parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if type(invoice_amount) is not int or invoice_amount < 1:
            return Response(
                {"error": "invoice_amount must be an integer greater than or equal to 1"},
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
            account = Account.objects.get(account_number=account_number)
            invoice = Invoice(
                invoice_amount=invoice_amount,
                message=message,
                account_number=account,
            )
            invoice.full_clean()
            invoice.save()

            invoice_link = (
                f"{settings.FRONTEND_BASE_URL.rstrip('/')}"
                f"/invoice/{invoice.invoice_number}"
            )
            return Response({"invoice_link": invoice_link}, status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            return Response(
                {"error": exc.message_dict}, status=status.HTTP_400_BAD_REQUEST
            )


class InvoiceInfoView(APIView):
    """
    Step 8-1: 請求情報の取得
    GET /api/{invoice_number}/get_inf
    """
    def get(self, request, invoice_number: str):
        try:
            invoice = Invoice.objects.get(invoice_number=invoice_number)
        except (Invoice.DoesNotExist, ValidationError, ValueError):
            return Response(
                {"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "invoice_account_number": invoice.account_number_id,
                "invoice_amount": str(invoice.invoice_amount),
                "invoice_message": invoice.message,
                "invoice_flag": invoice.invoice_flag,
            },
            status=status.HTTP_200_OK,
        )


class InvoicePayView(APIView):
    """
    Step 8-2: 請求の支払い用API
    POST /api/{invoice_number}/pay
    """
    def post(self, request, invoice_number: str):
        my_account_number = request.data.get("my_account_number")
        invoice_account_number = request.data.get("invoice_account_number")
        invoice_amount = request.data.get("invoice_amount")
        message = request.data.get("message", "")

        if not my_account_number or not invoice_account_number or invoice_amount is None:
            return Response(
                {"error": "Not enough parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if message is None:
            message = ""
        if not isinstance(message, str) or len(message) > 200:
            return Response(
                {"error": "message must be a string of 200 characters or fewer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if type(invoice_amount) is int:
            requested_amount = invoice_amount
        elif isinstance(invoice_amount, str) and invoice_amount.isdigit():
            requested_amount = int(invoice_amount)
        else:
            return Response(
                {"error": "invoice_amount must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if requested_amount < 1:
            return Response(
                {"error": "invoice_amount must be greater than or equal to 1"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                invoice = (
                    Invoice.objects.select_for_update()
                    .select_related("account_number")
                    .get(invoice_number=invoice_number)
                )
                if invoice.invoice_flag == Invoice.InvoiceFlag.PAID:
                    return Response(
                        {"error": "Invoice already paid"},
                        status=status.HTTP_409_CONFLICT,
                    )
                if invoice.account_number_id != str(invoice_account_number):
                    return Response(
                        {"error": "Invoice account does not match"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if invoice.invoice_amount != requested_amount:
                    return Response(
                        {"error": "Invoice amount does not match"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if str(my_account_number) == invoice.account_number_id:
                    return Response(
                        {"error": "Payer and invoice account must be different"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                payer = Account.objects.select_for_update().get(
                    account_number=my_account_number
                )
                payee = Account.objects.select_for_update().get(
                    account_number=invoice.account_number_id
                )
                if payer.account_balance < invoice.invoice_amount:
                    return Response(
                        {"error": "Insufficient account balance"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                payer.account_balance -= invoice.invoice_amount
                payee.account_balance += invoice.invoice_amount
                payer.save(update_fields=["account_balance"])
                payee.save(update_fields=["account_balance"])

                transfer = Transaction.objects.create(
                    sender=payer,
                    recipient=payee,
                    transfer_amount=invoice.invoice_amount,
                    message=message,
                )

                invoice.invoice_flag = Invoice.InvoiceFlag.PAID
                invoice.paid_time = transfer.created_at
                invoice.paid_by = payer
                invoice.transaction_number = transfer
                invoice.full_clean()
                invoice.save(
                    update_fields=[
                        "invoice_flag",
                        "paid_time",
                        "paid_by",
                        "transaction_number",
                    ]
                )

            return Response(status=status.HTTP_200_OK)
        except Invoice.DoesNotExist:
            return Response(
                {"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        except (ValidationError, ValueError):
            return Response(
                {"error": "Invalid invoice data"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class InvoiceListView(APIView):
    """
    Step 9: 請求リストの取得
    GET /api/user/{account_number}/invoice_list
    """
    def get(self, request, account_number: str):
        if not Account.objects.filter(account_number=account_number).exists():
            return Response({"error": "not found account"}, status=status.HTTP_404_NOT_FOUND)

        invoices = Invoice.objects.filter(account_number=account_number).order_by(
            "-created_time"
        )
        invoice_list = [
            {
                "invoice_time": timezone.localtime(invoice.created_time).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                ),
                "invoice_flag": invoice.invoice_flag,
                "paid_by": invoice.paid_by_id,
                "invoice_number": str(invoice.invoice_number),
            }
            for invoice in invoices
        ]
        return Response({"invoice_list": invoice_list}, status=status.HTTP_200_OK)

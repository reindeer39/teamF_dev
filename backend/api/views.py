"""React向けAPIの受付、入力検証、DB操作、JSON応答を担当するView。

処理は config/urls.py → api/urls.py → このファイルの順で到着します。
`Account.objects...`などがDjango ORMによるDB操作、`Response(...)`が
Reactへ返すJSONレスポンスです。詳しい流れはBACKEND_FLOW_GUIDE.mdを参照。
"""
import uuid
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


# 請求関連モデルの安全な参照
try:
    from api.models import Invoice
except ImportError:
    Invoice = None


class InvoiceRequestView(APIView):
    """
    Step 7: 請求のリクエスト
    POST /api/user/{account_number}/invoice_request
    """
    def post(self, request, account_number: str):
        # ReactがPOSTしたJSONを取得
        invoice_amount = request.data.get("invoice_amount")
        message = request.data.get("message", "")

        # 入力検証: パラメータが不足している場合
        if invoice_amount is None:
            return Response({"error": "Not enough parameters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # DB操作: 請求元口座が存在するか確認
            account = Account.objects.get(account_number=account_number)
            invoice_number = str(uuid.uuid4())

            # Invoice DBへ登録
            if Invoice is not None:
                from datetime import datetime
                created_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                Invoice.objects.create(
                    invoice_number=invoice_number,
                    invoice_amount=int(invoice_amount),
                    message=message,
                    account_number=account,
                    created_time=created_time_str,
                    invoice_flag="notpay",
                )

            # 生成された請求URLをJSONでReactへ返す
            invoice_link = f"http://localhost:3000/invoice/{invoice_number}"
            return Response({"invoice_link": invoice_link}, status=status.HTTP_200_OK)

        except Account.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "Server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvoiceInfoView(APIView):
    """
    Step 8-1: 請求情報の取得
    GET /api/{invoice_number}/get_inf
    """
    def get(self, request, invoice_number: str):
        if Invoice is None:
            return Response({"error": "Invoice model not defined yet"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # DB操作: invoice_numberで請求レコードを1件検索
            invoice = Invoice.objects.get(invoice_number=invoice_number)
            data = {
                "invoice_account_number": getattr(invoice, "account_number_id", str(getattr(invoice, "account_number", ""))),
                "invoice_amount": str(invoice.invoice_amount),
                "invoice_message": getattr(invoice, "message", "") or "",
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)


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

        # 入力検証: 必須パラメータチェック
        if not my_account_number or not invoice_account_number or invoice_amount is None:
            return Response({"error": "Not enough parameters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # DB操作: 支払元・請求元口座の検索と残高ロック
                payer = Account.objects.select_for_update().get(account_number=my_account_number)
                payee = Account.objects.select_for_update().get(account_number=invoice_account_number)

                int_amount = int(invoice_amount)

                # 残高不足チェック
                if payer.account_balance < int_amount:
                    return Response({"error": "Insufficient account balance"}, status=status.HTTP_400_BAD_REQUEST)

                # 1. 残高移動処理
                payer.account_balance -= int_amount
                payee.account_balance += int_amount
                payer.save(update_fields=["account_balance"])
                payee.save(update_fields=["account_balance"])

                # 2. 送金履歴 (transactions) の登録 (共通の取引番号を使用)
                transfer = Transaction.objects.create(
                    sender=payer,
                    recipient=payee,
                    transfer_amount=int_amount,
                    message=message,
                )

                # 3. 請求DB (invoice) の更新 (送金DBの取引番号および支払日時を統一)
                if Invoice is not None:
                    try:
                        invoice = Invoice.objects.select_for_update().get(invoice_number=invoice_number)
                        
                        # 送金DBの作成日時 (created_at) を paid_time フォーマット文字列へ統一
                        paid_time_str = transfer.created_at.strftime("%Y-%m-%d %H:%M:%S.%f")
                        
                        invoice.invoice_flag = "paid"
                        invoice.paid_time = paid_time_str
                        invoice.paid_by = payer
                        # 送金DBの取引番号 (transaction_number) と請求DBの取引番号を統一
                        invoice.transaction_number = transfer
                        invoice.save()
                    except Exception:
                        pass

            # 処理完了 200 OK (空レスポンス)
            return Response(status=status.HTTP_200_OK)

        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvoiceListView(APIView):
    """
    Step 9: 請求リストの取得
    GET /api/user/{account_number}/invoice_list
    """
    def get(self, request, account_number: str):
        # アカウントの存在確認
        if not Account.objects.filter(account_number=account_number).exists():
            return Response({"error": "not found account"}, status=status.HTTP_404_NOT_FOUND)

        if Invoice is None:
            return Response({"invoice_list": []}, status=status.HTTP_200_OK)

        try:
            # DB操作: 指定された請求元の請求を作成日時降順 (新しい順) で取得
            invoices = Invoice.objects.filter(account_number=account_number).order_by("-created_time")

            invoice_list = []
            for inv in invoices:
                # 日時文字列を YYYY-MM-DD HH:MM (分まで) に加工
                created_time_raw = getattr(inv, "created_time", "") or ""
                invoice_time = created_time_raw[:16] if len(created_time_raw) >= 16 else created_time_raw

                # 支払った人の口座番号 (支払い前は null)
                paid_by_val = getattr(inv, "paid_by_id", None)
                if not paid_by_val and getattr(inv, "paid_by", None):
                    paid_by_val = str(getattr(inv.paid_by, "account_number", ""))

                invoice_list.append({
                    "invoice_time": invoice_time,
                    "invoice_flag": getattr(inv, "invoice_flag", "notpay"),
                    "paid_by": paid_by_val if paid_by_val else None,
                    "invoice_number": inv.invoice_number,
                })

            return Response({"invoice_list": invoice_list}, status=status.HTTP_200_OK)

        except Exception:
            return Response({"error": "not found account"}, status=status.HTTP_404_NOT_FOUND)

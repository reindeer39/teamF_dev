"""React向けAPIの受付、入力検証、DB操作、JSON応答を担当するView。

処理は config/urls.py → api/urls.py → このファイルの順で到着します。
`Account.objects...`などがDjango ORMによるDB操作、`Response(...)`が
Reactへ返すJSONレスポンスです。詳しい流れはBACKEND_FLOW_GUIDE.mdを参照。
"""
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from api.models import Account, Invoice, Transaction
from api.serializers import SignupSerializer


User = get_user_model()


def account_data(account):
    """Reactで共通利用する口座情報を同じJSON形式へ変換する。"""
    return {
        "account_number": account.account_number,
        "user_icon": account.user_icon,
        "user_name": account.user_name,
        "account_balance": account.account_balance,
    }


def authenticated_account_data(account):
    """認証API向けにAccount情報と認証Userのメールアドレスを返す。"""
    return {
        **account_data(account),
        "email": account.auth_user.email if account.auth_user else "",
    }


def invoice_data(invoice):
    """請求画面・請求一覧で共通利用するInvoice情報をJSON化する。"""
    return {
        "invoice_number": str(invoice.invoice_number),
        "invoice_time": timezone.localtime(invoice.created_time).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        ),
        "invoice_amount": invoice.invoice_amount,
        "message": invoice.message,
        "invoice_flag": invoice.invoice_flag,
        "issuer": account_data(invoice.account_number),
        "paid_time": (
            timezone.localtime(invoice.paid_time).strftime("%Y-%m-%d %H:%M:%S.%f")
            if invoice.paid_time
            else None
        ),
        "paid_by": account_data(invoice.paid_by) if invoice.paid_by else None,
        "transaction_number": (
            str(invoice.transaction_number_id)
            if invoice.transaction_number_id
            else None
        ),
    }


def authenticated_account(request):
    """認証ユーザーに紐づくAccountを取得する。"""
    try:
        return request.user.bank_account
    except Account.DoesNotExist:
        return None


class SignupView(APIView):
    """認証ユーザーと送金口座を同時に作成する。"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=validated_data["email"],
                    email=validated_data["email"],
                    password=validated_data["password"],
                    is_active=True,
                    is_staff=False,
                    is_superuser=False,
                )
                account = Account.objects.create(
                    account_number=validated_data["account_number"],
                    user_name=validated_data["user_name"],
                    user_icon="",
                    account_balance=0,
                    auth_user=user,
                )
                token = Token.objects.create(user=user)
        except IntegrityError:
            duplicate_errors = {}
            if Account.objects.filter(pk=validated_data["account_number"]).exists():
                duplicate_errors["account_number"] = [
                    "この口座番号は既に使用されています。"
                ]
            if User.objects.filter(email__iexact=validated_data["email"]).exists():
                duplicate_errors["email"] = [
                    "このメールアドレスは既に使用されています。"
                ]
            if duplicate_errors:
                return Response(
                    duplicate_errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"error": "アカウントを作成できませんでした。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "token": token.key,
                "email": user.email,
                "account": authenticated_account_data(account),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """メールアドレスとパスワードを検証して永続トークンを返す。"""

    permission_classes = [AllowAny]

    def post(self, request):
        raw_email = request.data.get("email", "")
        email = raw_email.strip().lower() if isinstance(raw_email, str) else ""
        password = request.data.get("password", "")
        user_by_email = (
            User.objects.filter(email__iexact=email).first() if email else None
        )
        authentication_name = user_by_email.username if user_by_email else email
        user = authenticate(
            request=request,
            username=authentication_name,
            password=password,
        )
        if user is None:
            return Response(
                {"error": "メールアドレスまたはパスワードが正しくありません。"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            account = user.bank_account
        except Account.DoesNotExist:
            return Response(
                {"error": "メールアドレスまたはパスワードが正しくありません。"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "email": user.email,
                "account": authenticated_account_data(account),
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account = authenticated_account(request)
        if account is None:
            return Response(
                {"error": "ログインユーザーに口座が紐づいていません。"},
                status=status.HTTP_409_CONFLICT,
            )
        data = authenticated_account_data(account)
        return Response({**data, "account": account_data(account)})


class MyAccountSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account = authenticated_account(request)
        if account is None:
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(account_data(account))


class AuthenticatedRecipientListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account = authenticated_account(request)
        if account is None:
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )
        users = Account.objects.exclude(pk=account.pk)
        return Response(
            {
                "recipient_list": [
                    {
                        "account_number": user.account_number,
                        "user_icon": user.user_icon,
                        "user_name": user.user_name,
                    }
                    for user in users
                ]
            }
        )


class AuthenticatedRecipientInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, recipient_account_number):
        sender = authenticated_account(request)
        if sender is None:
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )
        try:
            recipient = Account.objects.get(pk=recipient_account_number)
        except Account.DoesNotExist:
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if sender.pk == recipient.pk:
            return Response(
                {"error": "Sender and recipient must be different"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "sender_account_number": sender.account_number,
                "sender_account_balance": sender.account_balance,
                "recipient_account_number": recipient.account_number,
                "recipient_icon": recipient.user_icon,
                "recipient_name": recipient.user_name,
            }
        )


class UserSummaryView(APIView):
    """
    Step 1: ユーザ口座情報取得
    GET /api/user/{account_number}/summary
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, account_number: str):
        login_account = authenticated_account(request)
        if login_account is None or login_account.pk != account_number:
            return Response(
                {"error": "この口座へアクセスする権限がありません。"},
                status=status.HTTP_403_FORBIDDEN,
            )
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
    permission_classes = [IsAuthenticated]

    def get(self, request, account_number: str):
        login_account = authenticated_account(request)
        if login_account is None or login_account.pk != account_number:
            return Response(
                {"error": "この口座へアクセスする権限がありません。"},
                status=status.HTTP_403_FORBIDDEN,
            )
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
    permission_classes = [IsAuthenticated]

    def get(self, request, sender_account_number: str, recipient_account_number: str):
        login_account = authenticated_account(request)
        if login_account is None or login_account.pk != sender_account_number:
            return Response(
                {"error": "この口座へアクセスする権限がありません。"},
                status=status.HTTP_403_FORBIDDEN,
            )
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
    permission_classes = [IsAuthenticated]

    def post(self, request, sender_account_number: str, recipient_account_number: str):
        login_account = authenticated_account(request)
        if login_account is None or login_account.pk != sender_account_number:
            return Response(
                {"error": "この口座から送金する権限がありません。"},
                status=status.HTTP_403_FORBIDDEN,
            )
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


class AuthenticatedInvoiceCollectionView(APIView):
    """ログイン口座による請求作成と、その口座が発行した請求一覧。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        issuer = authenticated_account(request)
        if issuer is None:
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )
        invoices = (
            Invoice.objects.filter(account_number=issuer)
            .select_related("account_number", "paid_by", "transaction_number")
            .order_by("-created_time")
        )
        return Response({"invoice_list": [invoice_data(item) for item in invoices]})

    def post(self, request):
        issuer = authenticated_account(request)
        if issuer is None:
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )

        invoice_amount = request.data.get("invoice_amount")
        message = request.data.get("message", "")
        errors = {}
        if type(invoice_amount) is not int or invoice_amount < 1:
            errors["invoice_amount"] = ["請求金額は1円以上の整数にしてください。"]
        if message is None:
            message = ""
        if not isinstance(message, str) or len(message) > 200:
            errors["message"] = ["メッセージは200文字以内にしてください。"]
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        invoice = Invoice(
            invoice_amount=invoice_amount,
            message=message,
            account_number=issuer,
        )
        try:
            invoice.full_clean()
            invoice.save()
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        invoice_link = (
            f"{settings.FRONTEND_BASE_URL.rstrip('/')}"
            f"/invoice/{invoice.invoice_number}"
        )
        return Response(
            {**invoice_data(invoice), "invoice_link": invoice_link},
            status=status.HTTP_201_CREATED,
        )


class AuthenticatedInvoiceDetailView(APIView):
    """請求リンクのUUIDから請求内容を取得する。"""

    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_number):
        try:
            invoice = (
                Invoice.objects.select_related(
                    "account_number", "paid_by", "transaction_number"
                ).get(invoice_number=invoice_number)
            )
        except (Invoice.DoesNotExist, ValidationError, ValueError):
            return Response(
                {"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(invoice_data(invoice))


class AuthenticatedInvoicePayView(APIView):
    """ログイン口座を支払者として請求を支払う。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, invoice_number):
        payer = authenticated_account(request)
        if payer is None:
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
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
                        {"error": "この請求は支払済みです。"},
                        status=status.HTTP_409_CONFLICT,
                    )
                if payer.pk == invoice.account_number_id:
                    return Response(
                        {"error": "自分が発行した請求は支払えません。"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                locked_accounts = {
                    account.pk: account
                    for account in Account.objects.select_for_update().filter(
                        pk__in=[payer.pk, invoice.account_number_id]
                    )
                }
                locked_payer = locked_accounts[payer.pk]
                payee = locked_accounts[invoice.account_number_id]
                if locked_payer.account_balance < invoice.invoice_amount:
                    return Response(
                        {"error": "口座残高が不足しています。"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                locked_payer.account_balance -= invoice.invoice_amount
                payee.account_balance += invoice.invoice_amount
                locked_payer.save(update_fields=["account_balance"])
                payee.save(update_fields=["account_balance"])

                transfer = Transaction.objects.create(
                    sender=locked_payer,
                    recipient=payee,
                    transfer_amount=invoice.invoice_amount,
                    message=invoice.message,
                )
                invoice.invoice_flag = Invoice.InvoiceFlag.PAID
                invoice.paid_time = transfer.created_at
                invoice.paid_by = locked_payer
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
        except (Invoice.DoesNotExist, ValidationError, ValueError, KeyError):
            return Response(
                {"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "invoice_number": str(invoice.invoice_number),
                "invoice_amount": invoice.invoice_amount,
                "payment_amount": invoice.invoice_amount,
                "transaction_number": str(transfer.transaction_number),
                "payer_account_balance": locked_payer.account_balance,
            }
        )


class AuthenticatedTransferView(TransferView):
    """URLに送金元を含めず、ログイン中の口座から送金する。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, recipient_account_number):
        sender = authenticated_account(request)
        if sender is None:
            return Response(
                {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
            )
        return super().post(request, sender.account_number, recipient_account_number)

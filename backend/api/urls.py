"""apiアプリ内のURLとViewを対応付けるルーティング設定。

config/urls.pyが`/api/`を取り除いた残りのURLをこのファイルへ渡します。
`<str:...>`部分はURLから取り出され、views.pyのget/postメソッドへ
同名の引数として渡されます。このファイル自身はDB操作を行いません。
"""
from django.urls import path

from api.views import (
    CurrentUserView,
    InvoiceInfoView,
    InvoiceListView,
    InvoicePayView,
    InvoiceRequestView,
    LoginView,
    LogoutView,
    RecipientInfoView,
    RecipientListView,
    SignupView,
    TransferView,
    UserSummaryView,
)

urlpatterns = [
    # Step 10: 会員登録・ログイン。
    path("make_account", SignupView.as_view(), name="signup"),
    path("login", LoginView.as_view(), name="login"),
    # 仕様にはないが、ログイン状態の保持に必要な補助エンドポイント。
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/logout", LogoutView.as_view(), name="logout-legacy"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("auth/me", CurrentUserView.as_view(), name="current-user-legacy"),
    # GET /api/user/1000001/summary → UserSummaryView.get(..., "1000001")
    path(
        "user/<str:account_number>/summary",
        UserSummaryView.as_view(),
        name="user-summary",
    ),
    # GET /api/user/1000001/recipient_list → 送金先候補を取得するView。
    path(
        "user/<str:account_number>/recipient_list",
        RecipientListView.as_view(),
        name="recipient-list",
    ),
    # GET。送金元・送金先の2口座番号をViewへ渡す。
    path(
        "user/<str:sender_account_number>/<str:recipient_account_number>/recipient",
        RecipientInfoView.as_view(),
        name="recipient-info",
    ),
    # POST。Reactから受け取った金額・メッセージでDBの送金処理を行うView。
    path(
        "user/<str:sender_account_number>/<str:recipient_account_number>/transfer",
        TransferView.as_view(),
        name="transfer",
    ),
    # POST。請求リクエストを発行するView。
    path(
        "user/<str:account_number>/invoice_request",
        InvoiceRequestView.as_view(),
        name="invoice-request",
    ),
    # GET。請求情報を取得するView。
    path(
        "<str:invoice_number>/get_inf",
        InvoiceInfoView.as_view(),
        name="invoice-info",
    ),
    # POST。請求の支払い処理を行うView。
    path(
        "<str:invoice_number>/pay",
        InvoicePayView.as_view(),
        name="invoice-pay",
    ),
    # GET。指定ユーザが作成した請求リストを取得するView。
    path(
        "user/<str:account_number>/invoice_list",
        InvoiceListView.as_view(),
        name="invoice-list-user",
    ),
]

"""apiアプリ内のURLとViewを対応付けるルーティング設定。

config/urls.pyが`/api/`を取り除いた残りのURLをこのファイルへ渡します。
`<str:...>`部分はURLから取り出され、views.pyのget/postメソッドへ
同名の引数として渡されます。このファイル自身はDB操作を行いません。
"""
from django.urls import path

from api.views import (
    RecipientInfoView,
    RecipientListView,
    TransferView,
    UserSummaryView,
)

urlpatterns = [
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
]

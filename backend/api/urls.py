"""
APIルーティング設定 (api/urls.py)
"""
from django.urls import path
from api.views import (
    UserSummaryView,
    RecipientListView,
    RecipientInfoView,
    TransferView,
)

urlpatterns = [
    # Step 1: ユーザ口座情報取得
    path("user/<str:account_number>/summary", UserSummaryView.as_view(), name="user-summary"),
    
    # Step 2: 送金先一覧の取得
    path("user/<str:account_number>/recipient_list", RecipientListView.as_view(), name="recipient-list"),
    
    # Step 3: 送信先処理画面取得
    path(
        "user/<str:sender_account_number>/<str:recipient_account_number>/recipient", 
        RecipientInfoView.as_view(), 
        name="recipient-info"
    ),
    
    # Step 4: 送金処理
    path(
        "user/<str:sender_account_number>/<str:recipient_account_number>/transfer", 
        TransferView.as_view(), 
        name="transfer"
    ),
]
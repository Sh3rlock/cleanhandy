from django.urls import path
from .views import check_giftcard_balance, purchase_gift_card, giftcard_success

urlpatterns = [
    path("check-balance/", check_giftcard_balance, name="check_giftcard_balance"),
    path("purchase/", purchase_gift_card, name="purchase_gift_card"),
    path("success/", giftcard_success, name="giftcard_success"),
]

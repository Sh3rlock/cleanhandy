from django.urls import path
from .views import check_giftcard_balance, purchase_gift_card, giftcard_success, validate_discount_or_giftcard, add_giftcard, add_discount

urlpatterns = [
    path("api/validate/", validate_discount_or_giftcard, name="validate_discount_or_giftcard"),
    path("check-balance/", check_giftcard_balance, name="check_giftcard_balance"),
    path("purchase/", purchase_gift_card, name="purchase_gift_card"),
    path("success/", giftcard_success, name="giftcard_success"),

    path("add_giftcard/", add_giftcard, name="add_giftcard"),
    path("add_discount/", add_discount, name="add_discount"),
]

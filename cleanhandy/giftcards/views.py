# views.py
from django.shortcuts import render, redirect
from .models import GiftCard, DiscountCode
from .forms import GiftCardPurchaseForm
from .utils import generate_giftcard_pdf, send_giftcard_email
from .models import GiftCard
from quotes.models import ServiceCategory
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import HttpResponseBadRequest
from decimal import Decimal

def giftcard_success(request):
    return render(request, "giftcards/giftcard_success.html")

@login_required
def purchase_gift_card(request):
    service_cat = ServiceCategory.objects.filter(name__iexact='home').first()

    if request.method == "POST":
        form = GiftCardPurchaseForm(request.POST)
        if form.is_valid():
            giftcard = form.save(commit=False)
            giftcard.purchaser_email = request.user.email  # <-- Automatically set
            giftcard.balance = giftcard.amount
            giftcard.save()

            # Generate PDF and send via email
            pdf_file = generate_giftcard_pdf(giftcard)
            send_giftcard_email(giftcard.recipient_email, giftcard, pdf_file)

            return redirect("giftcard_success")
    else:
        form = GiftCardPurchaseForm(initial={
            "purchaser_email": request.user.email  # <-- Pre-fill for display (optional)
        })

    return render(request, "giftcards/purchase.html", {
        "form": form,
        "service_cat": service_cat
    })



def check_giftcard_balance(request):
    balance = None
    code_entered = None
    error = None

    if request.method == "POST":
        code_entered = request.POST.get("code", "").strip().upper()
        try:
            giftcard = GiftCard.objects.get(code=code_entered)
            balance = giftcard.balance
        except GiftCard.DoesNotExist:
            error = "Gift card not found."

    return render(request, "giftcards/check_balance.html", {
        "balance": balance,
        "code": code_entered,
        "error": error
    })

def validate_discount_or_giftcard(request):
    code = request.GET.get("code", "").strip()

    # 1. Try Gift Card
    try:
        giftcard = GiftCard.objects.get(code=code, is_active=True)
        if giftcard.balance > 0:
            return JsonResponse({
                "type": "giftcard",
                "valid": True,
                "amount": str(giftcard.balance)
            })
    except GiftCard.DoesNotExist:
        pass

    # 2. Try Discount Code
    try:
        discount = DiscountCode.objects.get(code__iexact=code, is_active=True)
        if discount.is_valid():
            return JsonResponse({
                "type": "discount",
                "valid": True,
                "discount_type": discount.discount_type,
                "value": str(discount.value)
            })
    except DiscountCode.DoesNotExist:
        pass

    # 3. Not found
    return JsonResponse({"valid": False})


@login_required
def add_giftcard(request):
    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount", "0"))  # Convert string to Decimal

            GiftCard.objects.create(
                amount=amount,
                balance=amount,  # 💰 Set balance equal to amount
                purchaser_name=request.POST.get("purchaser_name"),
                purchaser_email=request.POST.get("purchaser_email"),
                recipient_name=request.POST.get("recipient_name"),
                recipient_email=request.POST.get("recipient_email"),
                message=request.POST.get("message") or "",
                is_active=bool(request.POST.get("is_active")),
            )

            next_url = request.POST.get("next")
            return redirect(next_url) if next_url else redirect("giftcard_discount")

        except Exception as e:
            return HttpResponseBadRequest(f"Invalid data: {e}")

    return HttpResponseBadRequest("Invalid method")

@login_required
def add_discount(request):
    if request.method == "POST":
        try:
            DiscountCode.objects.create(
                code=request.POST.get("code"),
                discount_type=request.POST.get("discount_type"),
                value=Decimal(request.POST.get("value") or "0"),
                usage_limit=int(request.POST.get("usage_limit") or 1),
                expires_at=request.POST.get("expires_at") or None,
                is_active=bool(request.POST.get("is_active")),
            )
            next_url = request.POST.get("next")
            return redirect(next_url) if next_url else redirect("giftcard_discount")
        except Exception as e:
            return HttpResponseBadRequest(f"❌ Invalid data: {e}")
    return HttpResponseBadRequest("Invalid request method.")






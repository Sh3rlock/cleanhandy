# views.py
from django.shortcuts import render, redirect
from .models import GiftCard
from .forms import GiftCardPurchaseForm
from .utils import generate_giftcard_pdf, send_giftcard_email
from .models import GiftCard
from quotes.models import ServiceCategory
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

def giftcard_success(request):
    return render(request, "giftcards/giftcard_success.html")

@login_required
def purchase_gift_card(request):
    service_cat = ServiceCategory.objects.filter(name__iexact='cleaning').first()

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

def validate_gift_card(request):
    code = request.GET.get("code", "").strip()
    try:
        giftcard = GiftCard.objects.get(code=code, is_active=True)
        if giftcard.balance > 0:
            return JsonResponse({"valid": True, "amount": str(giftcard.balance)})
    except GiftCard.DoesNotExist:
        pass
    return JsonResponse({"valid": False})



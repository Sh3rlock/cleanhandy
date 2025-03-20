from django.shortcuts import render, get_object_or_404, redirect
from quotes.models import Quote, Service, ServiceCategory
from bookings.models import Booking
from customers.models import Customer
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from .forms import ServiceForm, ServiceCategoryForm

def admin_check(user):
    return user.is_staff  # Only allow staff users

@login_required
@user_passes_test(admin_check)
# 📌 ADMIN DASHBOARD VIEW
def admin_dashboard(request):
    # Fetch latest 10 records
    latest_quotes = Quote.objects.all().order_by("-created_at")[:10]
    latest_bookings = Booking.objects.all().order_by("-created_at")[:10]
    latest_customers = Customer.objects.all().order_by("-id")[:10]

    total_quotes = Quote.objects.count()
    total_bookings = Booking.objects.count()
    total_customers = Customer.objects.count()

    return render(request, "adminpanel/dashboard.html", {
        "latest_quotes": latest_quotes,
        "latest_bookings": latest_bookings,
        "latest_customers": latest_customers,
        "total_quotes": total_quotes,
        "total_bookings": total_bookings,
        "total_customers": total_customers,
    })


# 📌 QUOTES MANAGEMENT
def quote_list(request):
    quotes = Quote.objects.all().order_by("-created_at")
    return render(request, "adminpanel/quote_list.html", {"quotes": quotes})

def update_quote_status(request):
    if request.method == "POST":
        for quote in Quote.objects.all():
            new_status = request.POST.get(f"status_{quote.id}")
            if new_status and new_status != quote.status:
                quote.status = new_status
                quote.save()
    return redirect("quote_list")

def quote_detail(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    return render(request, "adminpanel/quote_detail.html", {"quote": quote})

def update_quote_detail_status(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status and new_status != quote.status:
            quote.status = new_status
            quote.save()
    return redirect("quote_detail", quote_id=quote.id)


# 📌 BOOKINGS MANAGEMENT
def booking_list(request):
    bookings = Booking.objects.all().order_by("-created_at")
    return render(request, "adminpanel/booking_list.html", {"bookings": bookings})

def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "adminpanel/booking_detail.html", {"booking": booking})

# 📌 CUSTOMERS MANAGEMENT
def customer_list(request):
    customers = Customer.objects.all().order_by("name")
    return render(request, "adminpanel/customer_list.html", {"customers": customers})

def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    quotes = Quote.objects.filter(customer=customer)  # Fetch quotes linked to this customer
    return render(request, "adminpanel/customer_detail.html", {"customer": customer, "quotes": quotes})


# 📌 List All Service Categories & Services
def service_list(request):
    categories = ServiceCategory.objects.all()
    services = Service.objects.all()
    return render(request, "adminpanel/service_list.html", {"categories": categories, "services": services})

# 📌 Add a New Service Category
def add_service_category(request):
    if request.method == "POST":
        form = ServiceCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("service_list")
    else:
        form = ServiceCategoryForm()
    return render(request, "adminpanel/service_category_form.html", {"form": form})

# 📌 Edit an Existing Service Category
def edit_service_category(request, category_id):
    category = get_object_or_404(ServiceCategory, id=category_id)
    if request.method == "POST":
        form = ServiceCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect("service_list")
    else:
        form = ServiceCategoryForm(instance=category)
    return render(request, "adminpanel/service_category_form.html", {"form": form})

# 📌 Delete a Service Category
def delete_service_category(request, category_id):
    category = get_object_or_404(ServiceCategory, id=category_id)
    category.delete()
    return redirect("service_list")

# 📌 Add a New Sub-Service
def add_service(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("service_list")
    else:
        form = ServiceForm()
    return render(request, "adminpanel/service_form.html", {"form": form})

# 📌 Edit an Existing Sub-Service
def edit_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect("service_list")
    else:
        form = ServiceForm(instance=service)
    return render(request, "adminpanel/service_form.html", {"form": form})

# 📌 Delete a Sub-Service
def delete_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    service.delete()
    return redirect("service_list")
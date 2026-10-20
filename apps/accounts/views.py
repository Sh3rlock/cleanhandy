from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.models import User
from apps.booking.forms import EmailAuthenticationForm, PropertyForm, SignupForm
from apps.booking.models import Job, QuoteRequest
from apps.booking.quote_actions import accept_quoted_request
from apps.company.models import get_company
from apps.content.views import _seo


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = get_company()
        context.update(
            _seo(
                self.request,
                company,
                title="Log in | TheCleanHandy",
                description="Log in to see your TheCleanHandy quotes.",
                path="/account/login/",
                noindex=True,
            )
        )
        return context


class AccountLogoutView(LogoutView):
    pass


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("account_home")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.create_user(
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
            phone=form.cleaned_data["phone"],
            role=form.cleaned_data["role"],
        )
        QuoteRequest.objects.filter(contact_email__iexact=user.email, user__isnull=True).update(user=user)
        login(request, user)
        messages.success(request, "Your account is ready. Any quotes sent from this email are attached.")
        return redirect("account_home")
    company = get_company()
    return render(
        request,
        "accounts/signup.html",
        {
            "form": form,
            **_seo(
                request,
                company,
                title="Create an account | TheCleanHandy",
                description="Create a TheCleanHandy account to follow quotes and save properties.",
                path="/account/signup/",
                noindex=True,
            ),
        },
    )


def _account_context(request, property_form=None):
    company = get_company()
    return {
        "quotes": request.user.quotes.select_related(
            "service", "property", "destination", "estimate"
        ).prefetch_related("payments"),
        "jobs": Job.objects.filter(quote__user=request.user)
        .select_related("quote__service", "quote__property")
        .prefetch_related("invoices"),
        "properties": request.user.properties.all(),
        "property_form": property_form or PropertyForm(),
        **_seo(
            request,
            company,
            title="Your account | TheCleanHandy",
            description="Quotes, jobs, and saved properties.",
            path="/account/",
            noindex=True,
        ),
    }


@login_required
def account_home(request):
    return render(request, "accounts/dashboard.html", _account_context(request))


@login_required
@require_http_methods(["POST"])
def add_property(request):
    form = PropertyForm(request.POST)
    if form.is_valid():
        prop = form.save(commit=False)
        prop.owner = request.user
        prop.save()
        messages.success(request, "Property saved.")
        return redirect("account_home")
    return render(request, "accounts/dashboard.html", _account_context(request, form))


@login_required
@require_POST
def accept_quote(request, quote_id):
    quote = get_object_or_404(QuoteRequest, pk=quote_id, user=request.user)
    result = accept_quoted_request(quote)
    if result == "accepted":
        messages.success(request, "Quote accepted. TheCleanHandy will confirm the schedule.")
    elif result != "already":
        messages.error(request, "This quote cannot be accepted yet.")
    return redirect("account_home")

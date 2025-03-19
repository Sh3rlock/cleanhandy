from django.urls import path
from .views import request_quote, quote_submitted

urlpatterns = [
    path("request/", request_quote, name="request_quote"),
    path("submitted/", quote_submitted, name="quote_submitted"),
]
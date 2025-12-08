"""
Middleware to show an under construction page when UNDER_CONSTRUCTION is enabled.
Admin users and staff can bypass this.
"""
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse


class UnderConstructionMiddleware:
    """
    Middleware that intercepts all requests when UNDER_CONSTRUCTION is True
    and shows an under construction page, except for:
    - Admin users and staff
    - Static files and media files
    - Healthcheck endpoints
    - Admin panel URLs
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.
    
    def __call__(self, request):
        # Check if under construction mode is enabled
        if getattr(settings, 'UNDER_CONSTRUCTION', False):
            # Allow static and media files to be served (check this first)
            static_url = settings.STATIC_URL if settings.STATIC_URL.startswith('/') else '/' + settings.STATIC_URL
            media_url = settings.MEDIA_URL if settings.MEDIA_URL.startswith('/') else '/' + settings.MEDIA_URL
            
            if request.path.startswith(static_url) or request.path.startswith(media_url):
                return self.get_response(request)
            
            # Allow healthcheck endpoints
            if request.path in ['/healthz/', '/health/', '/quotes/health/']:
                return self.get_response(request)
            
            # Allow admin panel URLs (so staff can log in)
            if request.path.startswith('/admin/') or request.path.startswith('/django-admin/'):
                return self.get_response(request)
            
            # Allow admin/staff users to access the site normally
            if hasattr(request, 'user') and request.user.is_authenticated:
                if request.user.is_staff or request.user.is_superuser:
                    return self.get_response(request)
            
            # Show under construction page for all other requests
            return render(request, 'under_construction.html', status=503)
        
        # Under construction mode is disabled, proceed normally
        return self.get_response(request)

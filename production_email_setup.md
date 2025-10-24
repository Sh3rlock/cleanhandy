# Production Email Configuration Guide

## Current Issues Fixed

### 1. Email Configuration Problems
- ✅ **Fixed duplicate DEFAULT_FROM_EMAIL** in settings.py
- ✅ **Fixed invalid email format** ("TheCleanHandy" → "support@thecleanhandy.com")
- ✅ **Replaced hardcoded emails** with settings.DEFAULT_FROM_EMAIL
- ✅ **Added environment variable support** for production

### 2. Gmail App Password Setup

#### For Production Deployment:

1. **Generate Gmail App Password**:
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Security → 2-Step Verification (enable if not already)
   - App passwords → Generate new password for "Mail"
   - Copy the 16-character password

2. **Set Environment Variables** (in your production platform):
   ```bash
   EMAIL_HOST_USER=matyass91@gmail.com
   EMAIL_HOST_PASSWORD=your_new_app_password_here
   DEFAULT_FROM_EMAIL=support@thecleanhandy.com
   ```

### 3. Alternative Email Services (Recommended for Production)

#### Option A: SendGrid (Recommended)
```python
# In settings.py for production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = "your_sendgrid_api_key"
DEFAULT_FROM_EMAIL = "support@thecleanhandy.com"
```

#### Option B: Mailgun
```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.mailgun.org"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "postmaster@your-domain.mailgun.org"
EMAIL_HOST_PASSWORD = "your_mailgun_password"
DEFAULT_FROM_EMAIL = "support@thecleanhandy.com"
```

### 4. Production Settings Checklist

Ensure these are set in production:

```python
# Production settings
DEBUG = False
ALLOWED_HOSTS = ['cleanhandy-production.up.railway.app']

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"  # or SendGrid/Mailgun
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "support@thecleanhandy.com")

# Security settings
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

### 5. Testing Email Functionality

Create a test view to verify email sending:

```python
# Add to accounts/views.py
from django.core.mail import send_mail
from django.http import JsonResponse

def test_email(request):
    try:
        send_mail(
            'Test Email',
            'This is a test email from CleanHandy.',
            settings.DEFAULT_FROM_EMAIL,
            ['your-email@example.com'],
            fail_silently=False,
        )
        return JsonResponse({'status': 'success', 'message': 'Email sent successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
```

### 6. Common Production Email Issues

1. **Gmail "Less Secure Apps" Disabled**: Use App Passwords instead
2. **Rate Limiting**: Gmail has daily sending limits
3. **Spam Filters**: Use proper email authentication (SPF, DKIM)
4. **HTTPS Required**: Some email services require secure connections

### 7. Monitoring and Logging

Add email logging to track issues:

```python
import logging
logger = logging.getLogger(__name__)

# In email functions
try:
    email.send()
    logger.info(f"Email sent successfully to {email.to}")
except Exception as e:
    logger.error(f"Failed to send email: {str(e)}")
```

## Next Steps

1. **Update Gmail App Password** with a new one
2. **Set environment variables** in production
3. **Test email functionality** with the test view
4. **Consider switching to SendGrid** for better reliability
5. **Monitor email logs** for any issues

## Quick Fix for Immediate Deployment

If you need to deploy quickly:

1. Generate a new Gmail App Password
2. Set these environment variables in your production platform:
   - `EMAIL_HOST_USER=matyass91@gmail.com`
   - `EMAIL_HOST_PASSWORD=your_new_app_password`
   - `DEFAULT_FROM_EMAIL=support@thecleanhandy.com`
3. Deploy the updated code
4. Test email functionality

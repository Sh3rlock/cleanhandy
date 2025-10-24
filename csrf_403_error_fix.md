# CSRF 403 Error - Fix Guide

## Issue: CSRF verification failed. Request aborted.

This error occurs when Django's CSRF protection mechanism rejects a form submission due to an invalid or missing CSRF token.

## Immediate Solutions

### 1. **Quick Fixes (Try These First)**

#### A. Refresh the Page
- **Simple but effective**: Refresh the booking form page
- **Why**: Gets a fresh CSRF token
- **Action**: Press F5 or Ctrl+R (Cmd+R on Mac)

#### B. Clear Browser Cache and Cookies
- **Chrome**: Settings → Privacy → Clear browsing data → Cookies and site data
- **Firefox**: Settings → Privacy → Clear Data → Cookies
- **Safari**: Develop → Empty Caches

#### C. Try a Different Browser
- Test in an incognito/private window
- Try a completely different browser

### 2. **Debug CSRF Token Issues**

#### A. Check CSRF Token Status
Visit: `/csrf-debug/` to see:
- Current CSRF token
- Available cookies
- Session information
- User authentication status

#### B. Test CSRF Token Refresh
Visit: `/refresh-csrf/` to refresh the CSRF token

### 3. **Production Environment Fixes**

#### A. Update CSRF_TRUSTED_ORIGINS
Added to settings.py:
```python
CSRF_TRUSTED_ORIGINS = [
    'https://cleanhandy-production.up.railway.app',
    'https://thecleanhandy.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000'
]
```

#### B. Enhanced CSRF Settings
```python
# CSRF Settings for better compatibility
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access for AJAX requests
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False  # Use cookies instead of sessions for CSRF tokens
CSRF_COOKIE_AGE = 31449600  # 1 year in seconds
```

## Common Causes and Solutions

### 1. **Token Expiration**
**Cause**: CSRF token expired (default: 1 year, but can be shorter)
**Solution**: 
- Refresh the page to get a new token
- Increased CSRF_COOKIE_AGE to 1 year

### 2. **Domain Mismatch**
**Cause**: Form submitted from different domain than expected
**Solution**: 
- Added multiple domains to CSRF_TRUSTED_ORIGINS
- Includes both production and local development domains

### 3. **Browser Cookie Issues**
**Cause**: Browser blocking or clearing cookies
**Solution**:
- Clear browser cache and cookies
- Check browser privacy settings
- Disable ad blockers temporarily

### 4. **Session Issues**
**Cause**: User session expired or invalid
**Solution**:
- Log out and log back in
- Clear session cookies
- Increased SESSION_COOKIE_AGE to 2 weeks

### 5. **JavaScript/AJAX Issues**
**Cause**: AJAX requests not including CSRF token
**Solution**:
- Added automatic CSRF token handling in base template
- Set CSRF_COOKIE_HTTPONLY = False for JavaScript access

## Testing the Fix

### 1. **Test CSRF Debug Endpoint**
```bash
curl https://thecleanhandy.com/csrf-debug/
```
Should return JSON with CSRF token and session info.

### 2. **Test Form Submission**
1. Go to `/quotes/cleaning/booking/`
2. Fill out the form
3. Submit - should work without 403 error

### 3. **Test Token Refresh**
```bash
curl https://thecleanhandy.com/refresh-csrf/
```
Should return success message.

## Advanced Troubleshooting

### 1. **Check Server Logs**
Look for CSRF-related errors in Django logs:
```python
# In Django settings, add logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
        },
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### 2. **Browser Developer Tools**
1. Open Developer Tools (F12)
2. Go to Application/Storage tab
3. Check Cookies for `csrftoken`
4. Verify the token value is not empty

### 3. **Network Tab Analysis**
1. Open Developer Tools → Network tab
2. Submit the form
3. Check the request headers for `X-CSRFToken`
4. Check the form data for `csrfmiddlewaretoken`

## Production Deployment Steps

### 1. **Deploy Updated Settings**
The enhanced CSRF settings are now in place:
- Multiple trusted origins
- Extended cookie lifetime
- Better compatibility settings

### 2. **Restart Django Server**
After deploying settings changes:
```bash
# If using systemd
sudo systemctl restart your-django-service

# If using Docker
docker restart your-container

# If using Railway/Heroku
# Deploy will automatically restart
```

### 3. **Monitor for CSRF Errors**
Watch server logs for CSRF-related errors and monitor the `/csrf-debug/` endpoint.

## Expected Behavior After Fix

1. ✅ **Form Submission**: Should work without 403 errors
2. ✅ **Token Persistence**: CSRF tokens last longer (1 year)
3. ✅ **Multiple Domains**: Works on both production and local domains
4. ✅ **Debug Tools**: `/csrf-debug/` and `/refresh-csrf/` endpoints available

## If Issues Persist

### 1. **Temporary Workaround**
Add this to your view (NOT recommended for production):
```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def your_view(request):
    # Your view code
```

### 2. **Check Middleware Order**
Ensure CSRF middleware is in the correct position:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # This position is important
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # ... other middleware
]
```

The CSRF 403 error should now be resolved with the enhanced settings and debugging tools!

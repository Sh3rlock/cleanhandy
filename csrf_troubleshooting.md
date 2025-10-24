# CSRF Troubleshooting Guide

## Common CSRF Error Solutions

### 1. Clear Browser Cache and Cookies
```bash
# Clear all browser data including cookies and cache
# Or use browser developer tools to clear storage
```

### 2. Restart Django Development Server
```bash
cd /Users/sandormatyas/Desktop/Projects/cleanhandy/cleanhandy
python manage.py runserver
```

### 3. Check CSRF Token in Browser
1. Open browser developer tools (F12)
2. Go to Application/Storage tab
3. Check if `csrftoken` cookie exists
4. Verify the token value is not empty

### 4. Verify Form CSRF Token
1. Right-click on any form with method="post"
2. Inspect element
3. Look for `<input type="hidden" name="csrfmiddlewaretoken" value="...">`
4. Ensure the value is not empty

### 5. Test CSRF Token Refresh
Open browser console and run:
```javascript
// Test CSRF token refresh
$.ajax({
  url: '/refresh-csrf/',
  type: 'GET',
  success: function() {
    console.log('CSRF token refreshed successfully');
  },
  error: function() {
    console.log('Failed to refresh CSRF token');
  }
});
```

### 6. Check Django Settings
Verify these settings in `settings.py`:
- `CSRF_TRUSTED_ORIGINS` includes your domain
- `CSRF_COOKIE_SECURE = False` (for development)
- `CSRF_COOKIE_HTTPONLY = False` (for AJAX requests)

### 7. Manual CSRF Token Check
```javascript
// Check current CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

console.log('CSRF Token:', getCookie('csrftoken'));
```

### 8. Common Causes
- **Session timeout**: User logged out due to inactivity
- **Browser cache**: Old CSRF token cached
- **Multiple tabs**: Different CSRF tokens in different tabs
- **AJAX requests**: Missing CSRF token in AJAX headers
- **Form submission**: Missing or invalid CSRF token in form

### 9. Quick Fixes
1. **Refresh the page** - Gets new CSRF token
2. **Logout and login again** - Resets session and CSRF token
3. **Clear browser data** - Removes all cached tokens
4. **Restart Django server** - Resets server-side session storage

### 10. Prevention
- CSRF tokens are automatically refreshed every 30 minutes
- All forms include proper `{% csrf_token %}` tags
- AJAX requests include CSRF headers automatically
- Session cookies have proper expiration settings

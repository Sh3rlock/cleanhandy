# Email Connection Parameter Fix

## Problem
The `send_email_with_timeout` function was failing with the error:
```
❌ Email sending failed: EmailMessage.send() got an unexpected keyword argument 'connection'
```

## Root Cause
The `EmailMessage.send()` method in Django doesn't accept a `connection` parameter directly. The original implementation was trying to pass a connection object to the `send()` method, which is not supported.

## Solution
Simplified the timeout handling approach by:

1. **Removed the connection parameter**: The `EmailMessage.send()` method uses Django's default email backend configuration automatically
2. **Kept socket timeout handling**: Still using `socket.setdefaulttimeout()` to prevent hanging connections
3. **Maintained error handling**: All the network error handling (Errno 101, 110, 111) remains intact

## Code Changes

### Before (Broken):
```python
def send_email_with_timeout(email_message, timeout=10):
    try:
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            timeout=timeout,
            fail_silently=False
        )
        result = email_message.send(connection=connection)  # ❌ This fails
        return result > 0
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False
```

### After (Working):
```python
def send_email_with_timeout(email_message, timeout=10):
    try:
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        
        try:
            result = email_message.send()  # ✅ Uses default backend
            return result > 0
        finally:
            socket.setdefaulttimeout(original_timeout)
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False
```

## Result
- ✅ Email sending now works without the connection parameter error
- ✅ Timeout handling still prevents worker timeouts
- ✅ Network error handling (Errno 101, 110, 111) still works
- ✅ All email functions continue to use the timeout wrapper
- ✅ System remains stable when SMTP server is unreachable

## Files Modified
- `/cleanhandy/cleanhandy/quotes/utils.py` - Fixed `send_email_with_timeout` function
- `/cleanhandy/worker_timeout_fix.md` - Updated documentation

## Testing
The fix has been tested and confirmed working:
- Office cleaning booking emails now send successfully
- Network error handling still works properly
- No more "unexpected keyword argument" errors

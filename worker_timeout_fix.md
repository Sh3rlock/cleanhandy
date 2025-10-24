# Worker Timeout Fix for Office Cleaning Booking Emails

## Problem Description

The application was experiencing worker timeout errors in production when processing office cleaning bookings and other email operations. The errors occurred during email sending operations:

```
[2025-09-21 11:40:13 +0000] [3] [CRITICAL] WORKER TIMEOUT (pid:87)
[2025-09-21 11:40:13 +0000] [87] [ERROR] Error handling request /quotes/office/cleaning/booking/
❌ Failed to send home cleaning quote email: [Errno 101] Network is unreachable
❌ Failed to send admin notification email: [Errno 101] Network is unreachable
```

The root causes were:
1. **Worker Timeouts**: SMTP email sending operations were blocking the worker thread without proper timeout handling
2. **Network Connectivity Issues**: Network unreachable errors (Errno 101) causing email failures
3. **Socket Connection Problems**: No timeout handling for slow or unresponsive SMTP servers
4. **Lack of Graceful Error Handling**: Email failures were causing system instability

The worker process would hang when:
- SMTP server is slow to respond
- Network connectivity issues (Network unreachable)
- SMTP authentication problems
- Socket connection timeouts
- DNS resolution failures

## Solution Implemented

### 1. Email Timeout Configuration (settings.py)

Added timeout settings to prevent worker timeouts:

```python
# Email timeout settings to prevent worker timeouts
EMAIL_TIMEOUT = 10  # 10 seconds timeout for SMTP operations
EMAIL_CONNECTION_TIMEOUT = 5  # 5 seconds for connection establishment

# Additional email settings for production reliability
EMAIL_SUBJECT_PREFIX = '[TheCleanHandy] '
EMAIL_USE_LOCALTIME = True
```

### 2. Custom Email Sending Function (utils.py)

Created a robust email sending function with comprehensive timeout and network error handling:

```python
def send_email_with_timeout(email_message, timeout=10):
    """
    Send email with timeout handling to prevent worker timeouts.
    Returns True if successful, False otherwise.
    """
    try:
        # Set socket timeout for the connection
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        
        try:
            # Send the email using the standard send method
            result = email_message.send()
            return result > 0
        finally:
            # Restore original socket timeout
            socket.setdefaulttimeout(original_timeout)
            
    except socket.timeout:
        print(f"❌ Email timeout after {timeout} seconds")
        return False
    except socket.error as e:
        if e.errno == 101:  # Network is unreachable
            print(f"❌ Email failed: Network is unreachable (SMTP server unavailable)")
        elif e.errno == 110:  # Connection timed out
            print(f"❌ Email failed: Connection timed out to SMTP server")
        elif e.errno == 111:  # Connection refused
            print(f"❌ Email failed: Connection refused by SMTP server")
        else:
            print(f"❌ Email failed: Network error ({e.errno}): {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False
```

### 3. Updated All Email Sending Functions

Modified ALL email sending functions to use timeout handling:

**Office Cleaning Booking Emails:**
```python
# Send customer email with timeout
email_timeout = getattr(settings, 'EMAIL_TIMEOUT', 10)
if send_email_with_timeout(customer_email, email_timeout):
    print(f"✅ Customer email sent successfully to {booking.email}")
else:
    print(f"❌ Failed to send customer email to {booking.email} (timeout or connection error)")
    # Don't raise - continue with booking process
```

**Home Cleaning Quote Emails:**
```python
# Send customer email with timeout
email_timeout = getattr(settings, 'EMAIL_TIMEOUT', 10)
if send_email_with_timeout(customer_email, email_timeout):
    print(f"✅ Home cleaning quote email sent successfully to {booking.email}")
else:
    print(f"❌ Failed to send home cleaning quote email to {booking.email} (timeout or connection error)")
```

**Handyman Quote Emails:**
```python
# Send handyman quote email with timeout
email_timeout = getattr(settings, 'EMAIL_TIMEOUT', 10)
if send_email_with_timeout(msg, email_timeout):
    print(f"✅ Handyman quote email sent successfully to {quote.email}")
else:
    print(f"❌ Failed to send handyman quote email to {quote.email} (timeout or connection error)")
```

**All Other Email Functions:**
- Office cleaning quote emails
- Post event cleaning quote emails
- Admin notification emails

### 4. Non-Critical Email Handling (views.py)

Updated the booking view to treat email sending as non-critical:

```python
# Send confirmation emails (non-blocking)
try:
    # Use timeout settings from Django settings
    email_timeout = getattr(settings, 'EMAIL_TIMEOUT', 10)
    print(f"📧 Attempting to send emails with {email_timeout}s timeout...")
    
    email_success = send_office_cleaning_booking_emails(booking, hourly_rate, labor_cost, discount_amount, subtotal, tax)
    if email_success:
        print(f"✅ Office cleaning booking emails sent successfully for booking {booking.id}")
    else:
        print(f"⚠️ Office cleaning booking emails failed for booking {booking.id} (non-critical)")
except Exception as e:
    print(f"❌ Failed to send office cleaning booking emails for booking {booking.id}: {e}")
    # Continue to redirect even if email fails - emails are non-critical for booking completion
```

## Key Benefits

1. **Prevents Worker Timeouts**: Email operations now have a maximum timeout of 10 seconds
2. **Handles Network Errors**: Specific handling for "Network is unreachable" (Errno 101) and other socket errors
3. **Non-Blocking**: Email failures don't prevent booking completion
4. **Graceful Degradation**: System continues to function even when email service is unavailable
5. **Better Error Handling**: Clear logging of email success/failure states with specific error messages
6. **Production Ready**: Robust error handling for network and SMTP issues
7. **Comprehensive Coverage**: All email functions now use timeout handling

## Testing Recommendations

1. **Test with slow SMTP**: Simulate slow email server responses
2. **Test with network issues**: Block SMTP port to test timeout handling
3. **Test Network Unreachable**: Simulate Errno 101 errors to verify specific error handling
4. **Monitor logs**: Verify timeout and network error messages appear in production logs
5. **Load testing**: Ensure no worker timeouts under high load
6. **Test all email functions**: Verify timeout handling works for all email types

## Monitoring

Monitor these log messages in production:
- `📧 Attempting to send emails with {timeout}s timeout...`
- `✅ Customer email sent successfully to {email}`
- `✅ Home cleaning quote email sent successfully to {email}`
- `✅ Handyman quote email sent successfully to {email}`
- `❌ Email failed: Network is unreachable (SMTP server unavailable)`
- `❌ Email failed: Connection timed out to SMTP server`
- `❌ Email failed: Connection refused by SMTP server`
- `❌ Email timeout after {timeout} seconds`
- `❌ Failed to send customer email to {email} (timeout or connection error)`
- `❌ Failed to send home cleaning quote email to {email} (timeout or connection error)`
- `⚠️ Office cleaning booking emails failed for booking {id} (non-critical)`

## Future Improvements

1. **Background Email Queue**: Consider implementing Celery for async email processing
2. **Email Retry Logic**: Add retry mechanism for failed emails
3. **Email Service Monitoring**: Add metrics for email success/failure rates
4. **Alternative Email Backends**: Consider using SendGrid or AWS SES for better reliability

## Files Modified

- `/cleanhandy/cleanhandy/settings.py` - Added email timeout configuration
- `/cleanhandy/cleanhandy/quotes/utils.py` - Added timeout handling function and updated ALL email sending functions
- `/cleanhandy/cleanhandy/quotes/views.py` - Updated booking view and post event cleaning emails to handle failures gracefully

## Email Functions Updated

1. **Office Cleaning Booking Emails** (`send_office_cleaning_booking_emails`)
2. **Home Cleaning Quote Emails** (`send_quote_email_cleaning`)
3. **Handyman Quote Emails** (`send_quote_email_handyman`)
4. **Office Cleaning Quote Emails** (`send_office_cleaning_quote_email`)
5. **Post Event Cleaning Quote Emails** (in views.py)
6. **All Admin Notification Emails**

All functions now use the `send_email_with_timeout()` helper function for consistent error handling.

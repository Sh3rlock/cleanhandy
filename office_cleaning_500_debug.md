# Office Cleaning Booking 500 Error Debug Guide

## Issue: 500 Internal Server Error on Office Cleaning Booking Form

The office cleaning booking form (`/quotes/office/cleaning/booking/`) is returning a 500 error, likely related to email configuration changes.

## Enhanced Debugging Added

### 1. **Office Cleaning View Debugging**
Added comprehensive logging to track the entire process:
```python
print("🏢 Office cleaning booking view started")
print(f"✅ Service category: {service_cat}")
print(f"✅ Extras count: {extras.count()}")
print(f"✅ Hourly rate: {hourly_rate}")
```

### 2. **Email Sending Debugging**
Enhanced email debugging with specific details:
```python
print(f"📧 Sending customer email to: {booking.email}")
print(f"📧 From email: {settings.DEFAULT_FROM_EMAIL}")
print(f"✅ Customer email sent successfully to {booking.email}")
print(f"📧 Sending admin email to: {settings.DEFAULT_FROM_EMAIL}")
print(f"✅ Admin email sent successfully")
```

### 3. **Error Tracking**
Added try-catch blocks around critical sections:
- View setup and initialization
- Email template rendering
- Email sending process

## Potential Issues

### 1. **Email Configuration Problems**
**Most Likely Cause**: Recent admin email address changes
- `settings.DEFAULT_FROM_EMAIL` might be invalid
- Email credentials might be incorrect
- SMTP server configuration issues

### 2. **Template Rendering Issues**
**Possible Cause**: Email template problems
- Missing or corrupted email templates
- Template context variables not available
- Template syntax errors

### 3. **Database Issues**
**Possible Cause**: Missing required data
- ServiceCategory with name 'commercial' not found
- HourlyRate records missing
- CleaningExtra records missing

### 4. **Form Validation Issues**
**Possible Cause**: Form data problems
- Invalid form data format
- Missing required fields
- Field validation errors

## Debugging Steps

### 1. **Submit Office Cleaning Form**
1. Go to `/quotes/office/cleaning/booking/`
2. Fill out the form completely
3. Submit and check server logs

### 2. **Check Debug Output**
Look for these messages in server logs:
```
🏢 Office cleaning booking view started
✅ Service category: [category]
✅ Extras count: [count]
✅ Hourly rate: [rate]
📋 POST data received:
  [form data]
📧 Sending customer email to: [email]
📧 From email: [from_email]
✅ Customer email sent successfully to [email]
📧 Sending admin email to: [admin_email]
✅ Admin email sent successfully
```

### 3. **Identify Failure Point**
The debug output will show exactly where the 500 error occurs:
- **View setup failure**: Error in service category or hourly rate lookup
- **Form validation failure**: Form data validation issues
- **Email sending failure**: Email configuration or template problems
- **Template rendering failure**: Missing templates or context variables

## Common Issues & Solutions

### Issue: Email Configuration Problems
**Symptoms**: 
```
📧 From email: [invalid_email]
❌ Failed to send office cleaning booking emails: [SMTP error]
```
**Solutions**:
1. Check `DEFAULT_FROM_EMAIL` in settings
2. Verify email credentials
3. Test email configuration

### Issue: Missing Email Templates
**Symptoms**:
```
❌ Failed to send office cleaning booking emails: TemplateDoesNotExist
```
**Solutions**:
1. Verify templates exist:
   - `quotes/email_office_cleaning_summary.html`
   - `quotes/email_office_cleaning_admin.html`
2. Check template syntax
3. Verify template context variables

### Issue: Database Records Missing
**Symptoms**:
```
❌ Error in office cleaning booking view setup: [database error]
```
**Solutions**:
1. Check ServiceCategory with name 'commercial' exists
2. Verify HourlyRate records exist
3. Check CleaningExtra records exist

### Issue: Form Validation Problems
**Symptoms**:
```
❌ Form validation failed and missing essential data
```
**Solutions**:
1. Check form field requirements
2. Verify form data format
3. Check field validation rules

## Email Configuration Check

### Verify Email Settings:
```python
# Check these settings in production:
EMAIL_HOST_USER = "your-gmail@gmail.com"
EMAIL_HOST_PASSWORD = "your-app-password"
DEFAULT_FROM_EMAIL = "support@thecleanhandy.com"
```

### Test Email Configuration:
```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'support@thecleanhandy.com', ['test@example.com'])
```

## Expected Resolution

After implementing the debugging:

1. **Submit the office cleaning form** in production
2. **Check server logs** for detailed debug messages
3. **Identify the specific failure point** from the debug output
4. **Fix the identified issue** (most likely email configuration)
5. **Test again** to verify the fix works

The enhanced debugging will reveal exactly what's causing the 500 error in the office cleaning booking process!

## Most Likely Fix

Based on the user's comment about "admin email address change", the issue is most likely:

1. **Invalid `DEFAULT_FROM_EMAIL`** - Check if the email address is valid
2. **Email credentials** - Verify Gmail App Password is correct
3. **SMTP configuration** - Ensure email server settings are correct

The debugging will confirm this and provide the exact error message.

# Production 500 Error Debug Guide

## Issue: Form works locally but fails in production with 500 error

The cleaning booking form is working perfectly in localhost but returning a 500 Internal Server Error in production.

## Enhanced Debugging Added

### 1. **Comprehensive Error Logging**
Added detailed logging throughout the view:
- ✅ **View setup**: Service category and extras loading
- 📋 **POST data**: All submitted form data
- ✅ **Database objects**: Count of required models
- ❌ **Environment info**: DEBUG mode and database engine
- ❌ **Full traceback**: Complete error stack trace

### 2. **Production-Specific Debugging**
Enhanced error handling to identify production issues:
```python
print(f"❌ Environment: {settings.DEBUG}")
print(f"❌ Database: {settings.DATABASES['default']['ENGINE']}")
print(f"✅ SquareFeetOption count: {square_feet_options.count()}")
print(f"✅ HomeType count: {home_types.count()}")
```

### 3. **Form Validation Recovery**
Restored the missing `else` block for form validation errors that was accidentally removed.

## Potential Production Issues

### 1. **Database Differences**
**Local vs Production databases might have different data:**
- Missing ServiceCategory records
- Missing SquareFeetOption records  
- Missing HomeType records
- Missing CleaningExtra records

### 2. **Environment Configuration**
**Production settings might differ:**
- Different database engine
- Missing environment variables
- Different DEBUG settings
- Different email configuration

### 3. **Form Data Issues**
**From the request data, I noticed:**
- Duplicate `num_cleaners` fields (1 and 2)
- Empty `cleaning_type` field before actual value
- Multiple `extras` values

### 4. **Dependencies**
**Production might be missing:**
- Required Python packages
- Database migrations not applied
- Static files not collected

## Debugging Steps

### 1. **Check Production Logs**
After submitting the form, look for these debug messages:
```
✅ Service category found: [category]
✅ Cleaning extras count: [count]
📋 POST data received:
  [all form data]
✅ SquareFeetOption count: [count]
✅ HomeType count: [count]
❌ Error processing booking form: [error message]
❌ Environment: [DEBUG setting]
❌ Database: [database engine]
```

### 2. **Verify Database Data**
Check if required records exist in production:
```bash
python manage.py shell
>>> from quotes.models import *
>>> ServiceCategory.objects.filter(id=4).exists()
>>> SquareFeetOption.objects.filter(id=1).exists()
>>> HomeType.objects.filter(id=3).exists()
>>> CleaningExtra.objects.filter(id__in=[1,4,8]).exists()
```

### 3. **Test Debug Endpoints**
Visit these debug endpoints in production:
- `/debug-form/` - Test form validation
- `/debug-booking/` - Test price calculations

### 4. **Check Environment Variables**
Verify production environment variables:
```bash
echo $EMAIL_HOST_USER
echo $EMAIL_HOST_PASSWORD
echo $DEFAULT_FROM_EMAIL
```

## Common Production Issues & Solutions

### Issue: Missing Database Records
**Solution**: Create required records in Django admin:
1. Go to `/django-admin/quotes/servicecategory/`
2. Ensure ServiceCategory with ID 4 exists
3. Go to `/django-admin/quotes/squarefeetoption/`
4. Ensure SquareFeetOption with ID 1 exists
5. Go to `/django-admin/quotes/hometype/`
6. Ensure HomeType with ID 3 exists

### Issue: Database Migration Issues
**Solution**: Apply migrations:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### Issue: Environment Variables
**Solution**: Set required environment variables:
```bash
export EMAIL_HOST_USER="your-gmail@gmail.com"
export EMAIL_HOST_PASSWORD="your-app-password"
export DEFAULT_FROM_EMAIL="support@thecleanhandy.com"
```

### Issue: Form Data Validation
**Solution**: Check form template for duplicate fields or empty values.

## Expected Debug Output

### Successful Production Processing:
```
✅ Service category found: Home Cleaning
✅ Cleaning extras count: 8
📋 POST data received:
  csrfmiddlewaretoken: [token]
  hours_requested: 5
  num_cleaners: 2
  ...
✅ SquareFeetOption count: 5
✅ HomeType count: 3
✅ Booking created with ID: [id]
✅ Calculated booking price: [price]
✅ PDF generated successfully for booking [id]
✅ Home cleaning quote email sent successfully to [email]
```

### Failed Production Processing:
```
❌ Error processing booking form: [specific error]
❌ Environment: False
❌ Database: django.db.backends.postgresql
[Full traceback]
```

## Next Steps

1. **Submit the form in production** and check server logs for detailed error messages
2. **Verify database records** exist for the IDs referenced in the form data
3. **Check environment variables** are properly set
4. **Apply any missing migrations** if needed
5. **Test debug endpoints** to isolate the issue

The enhanced debugging should now provide detailed information about exactly what's failing in production, making it much easier to identify and fix the specific issue!

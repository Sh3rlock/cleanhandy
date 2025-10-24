# Available Hours 500 Error Debug Guide

## Issue: Internal Server Error with Available Hours for Office Cleaning Booking

The office cleaning booking form is experiencing a 500 error when trying to fetch available hours, likely related to the `available_hours_api` endpoint or the `get_available_hours_for_date` function.

## Enhanced Debugging Added

### 1. **Available Hours API Debugging**
Added comprehensive logging to the API endpoint:
```python
print(f"🕐 Available hours API called: date={date_str}, hours={hours}")
print(f"📅 Parsed date: {date}")
print(f"✅ Found {len(available)} available hours")
```

### 2. **Available Hours Function Debugging**
Enhanced the `get_available_hours_for_date` function with detailed logging:
```python
print(f"🕐 get_available_hours_for_date called: date={date}, hours_requested={hours_requested}")
print(f"📅 Day of week: {day_of_week}")
print(f"📅 Weekday/Saturday hours: {start_hour}:00-{end_hour}:00")
```

### 3. **Database Query Debugging**
Added logging for database operations:
```python
print(f"📋 Found {existing_bookings.count()} existing bookings for {date}")
print(f"🚫 Blocked: {quote.hour} - {end.time()}")
```

### 4. **Error Handling for BlockedTimeSlot**
Added try-catch around `BlockedTimeSlot` queries:
```python
try:
    blocked_slots = BlockedTimeSlot.objects.filter(date=date)
    # ... process blocked slots
except Exception as e:
    print(f"⚠️ Warning: Could not load blocked time slots: {str(e)}")
    # Continue without blocked slots if there's an error
```

## Potential Issues

### 1. **BlockedTimeSlot Model Issues**
**Most Likely Cause**: Missing or corrupted `BlockedTimeSlot` model
- Model not properly migrated in production
- Import errors with `adminpanel.models`
- Database table missing or corrupted

### 2. **Booking Model Issues**
**Possible Cause**: Problems with `Booking` model queries
- Database connection issues
- Missing or corrupted booking data
- Field validation errors

### 3. **Date Parsing Issues**
**Possible Cause**: Invalid date format or timezone issues
- Date format not matching expected format
- Timezone conversion problems
- Invalid date values

### 4. **Template/JavaScript Issues**
**Possible Cause**: Frontend calling API incorrectly
- Invalid date format in JavaScript
- Missing parameters in API call
- JavaScript errors preventing API calls

## Debugging Steps

### 1. **Test Available Hours API Directly**
Visit the API endpoint directly:
```
https://thecleanhandy.com/quotes/api/available-hours/?date=2025-09-24&hours=3
```

### 2. **Check Server Logs**
Look for these debug messages:
```
🕐 Available hours API called: date=2025-09-24, hours=3
📅 Parsed date: 2025-09-24
🕐 get_available_hours_for_date called: date=2025-09-24, hours_requested=3
📅 Day of week: 2
📅 Weekday hours: 8:00-18:00
📋 Found X existing bookings for 2025-09-24
✅ Found X available hours
```

### 3. **Test Office Cleaning Form**
1. Go to `/quotes/office/cleaning/booking/`
2. Select a date
3. Check browser console for JavaScript errors
4. Check server logs for API call debug messages

### 4. **Check Database Migration Status**
```bash
python manage.py showmigrations adminpanel
python manage.py showmigrations quotes
```

## Common Issues & Solutions

### Issue: BlockedTimeSlot Model Missing
**Symptoms**: 
```
⚠️ Warning: Could not load blocked time slots: [error]
```
**Solutions**:
1. Check if `adminpanel` app is properly installed
2. Run migrations: `python manage.py migrate adminpanel`
3. Verify model exists in `adminpanel/models.py`

### Issue: Booking Model Query Errors
**Symptoms**:
```
⚠️ Warning: Could not load existing bookings: [error]
```
**Solutions**:
1. Check database connection
2. Verify `Booking` model is properly migrated
3. Check for field validation issues

### Issue: Date Parsing Errors
**Symptoms**:
```
❌ Invalid date format: [date]
❌ Error in available_hours_api: [error]
```
**Solutions**:
1. Check date format in JavaScript
2. Verify timezone settings
3. Check for invalid date values

### Issue: JavaScript API Call Problems
**Symptoms**: No API calls in server logs
**Solutions**:
1. Check browser console for JavaScript errors
2. Verify API endpoint URL is correct
3. Check for CORS issues

## Expected Debug Output

### Successful API Call:
```
🕐 Available hours API called: date=2025-09-24, hours=3
📅 Parsed date: 2025-09-24
🕐 get_available_hours_for_date called: date=2025-09-24, hours_requested=3
📅 Day of week: 2
📅 Weekday hours: 8:00-18:00
📋 Found 2 existing bookings for 2025-09-24
🚫 Blocked: 09:00:00 - 12:00:00
🚫 Blocked: 14:00:00 - 17:00:00
✅ Found 8 available hours
```

### Failed API Call:
```
🕐 Available hours API called: date=2025-09-24, hours=3
❌ Error in available_hours_api: [specific error]
[Full traceback]
```

## Testing Commands

### Test API Endpoint:
```bash
curl "https://thecleanhandy.com/quotes/api/available-hours/?date=2025-09-24&hours=3"
```

### Check Model Existence:
```bash
python manage.py shell
>>> from adminpanel.models import BlockedTimeSlot
>>> BlockedTimeSlot.objects.count()
>>> from quotes.models import Booking
>>> Booking.objects.count()
```

### Check Migrations:
```bash
python manage.py showmigrations
python manage.py migrate --plan
```

## Expected Resolution

After implementing the debugging:

1. **Test the office cleaning form** - Select a date and check for API calls
2. **Check server logs** - Look for detailed debug messages
3. **Identify the specific failure point** - From the debug output
4. **Fix the identified issue** - Most likely BlockedTimeSlot model issues
5. **Test again** - Verify available hours load correctly

The enhanced debugging will reveal exactly what's causing the 500 error in the available hours functionality!

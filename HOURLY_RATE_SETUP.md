# Hourly Rate Management System Setup Guide

This guide explains how to set up and use the new configurable hourly rate system for the CleanHandy project.

## Overview

The new system allows administrators to manage hourly rates for different service types through the Django admin interface, replacing hardcoded rates with configurable ones.

## What's Been Added

### 1. New Model: `HourlyRate`
- **Location**: `quotes/models.py`
- **Purpose**: Stores configurable hourly rates for different service types
- **Fields**:
  - `service_type`: Type of service (office_cleaning, home_cleaning, etc.)
  - `hourly_rate`: Decimal field for the rate amount
  - `is_active`: Boolean to enable/disable rates
  - `description`: Optional description field
  - `created_at` & `updated_at`: Timestamps

### 2. Admin Interface
- **Location**: `quotes/admin.py`
- **Features**:
  - List view with editable active status
  - Filtering by service type and active status
  - Bulk actions to activate/deactivate rates
  - Organized fieldsets for better UX

### 3. Utility Functions
- **Location**: `quotes/utils.py`
- **Functions**:
  - `get_hourly_rate(service_type)`: Get rate for specific service
  - `get_all_hourly_rates()`: Get all active rates
  - `calculate_labor_cost()`: Calculate total labor cost
  - `clear_hourly_rate_cache()`: Clear cached rates

### 4. Management Command
- **Location**: `quotes/management/commands/setup_hourly_rates.py`
- **Purpose**: Initialize default hourly rates

## Setup Instructions

### Step 1: Create and Apply Migrations
```bash
cd cleanhandy/cleanhandy
python manage.py makemigrations quotes
python manage.py migrate
```

### Step 2: Initialize Default Rates
```bash
python manage.py setup_hourly_rates
```

This will create the following default rates:
- **Office Cleaning**: $75.00/hour
- **Home Cleaning**: $58.00/hour
- **Post Renovation**: $63.00/hour
- **Construction**: $63.00/hour
- **Move In/Out**: $65.00/hour
- **Deep Cleaning**: $70.00/hour
- **Regular Cleaning**: $58.00/hour

### Step 3: Access Admin Interface
1. Go to `/admin/` in your browser
2. Navigate to "Quotes" → "Hourly Rates"
3. You can now edit rates, activate/deactivate them, and add descriptions

## How to Use

### For Developers

#### 1. Getting Hourly Rates in Views
```python
from quotes.utils import get_hourly_rate

# Get rate for office cleaning
hourly_rate = get_hourly_rate('office_cleaning')

# Get rate for home cleaning
home_rate = get_hourly_rate('home_cleaning')
```

#### 2. Calculating Labor Costs
```python
from quotes.utils import calculate_labor_cost

# Calculate cost for 2 cleaners working 3 hours
total_cost = calculate_labor_cost('office_cleaning', 2, 3)
```

#### 3. Getting All Rates
```python
from quotes.utils import get_all_hourly_rates

all_rates = get_all_hourly_rates()
# Returns: {'office_cleaning': Decimal('75.00'), 'home_cleaning': Decimal('58.00'), ...}
```

### For Administrators

#### 1. Updating Rates
1. Go to Admin → Quotes → Hourly Rates
2. Click on the rate you want to edit
3. Modify the hourly rate amount
4. Add or update the description
5. Save changes

#### 2. Activating/Deactivating Rates
- Use the "Active" checkbox in the list view
- Use bulk actions to activate/deactivate multiple rates at once

#### 3. Adding New Service Types
1. Edit the `SERVICE_TYPE_CHOICES` in `quotes/models.py`
2. Run migrations
3. Add the new rate through admin interface

## Service Types Available

The system supports these service types:
- `office_cleaning` - Office cleaning services
- `home_cleaning` - Home cleaning services
- `post_renovation` - Post-renovation cleaning
- `construction` - Construction site cleaning
- `move_in_out` - Move in/out cleaning
- `deep_cleaning` - Deep cleaning services
- `regular_cleaning` - Regular maintenance cleaning

## Caching

The system includes caching for performance:
- Rates are cached for 1 hour
- Cache is automatically cleared when rates are updated
- Use `clear_hourly_rate_cache()` to manually clear cache if needed

## Fallback Behavior

If a rate is not configured in the database:
1. The system will return the default rate for that service type
2. Default rates are defined in the `HourlyRate.get_rate_for_service()` method
3. This ensures the system continues to work even if rates are missing

## Updating Existing Code

### 1. Replace Hardcoded Rates
**Before:**
```javascript
const hourlyRate = 75;
```

**After:**
```javascript
const hourlyRate = window.officeCleaningHourlyRate || 75;
```

### 2. Update Template Context
**Before:**
```python
return render(request, "template.html", {"form": form})
```

**After:**
```python
from .utils import get_hourly_rate
hourly_rate = get_hourly_rate('office_cleaning')
return render(request, "template.html", {
    "form": form,
    "hourly_rate": hourly_rate
})
```

## Benefits

1. **Flexibility**: Rates can be changed without code deployment
2. **Consistency**: All rates are managed in one place
3. **Performance**: Caching ensures fast access to rates
4. **Maintainability**: No more hardcoded values scattered throughout the code
5. **Audit Trail**: Track when rates were changed and by whom

## Troubleshooting

### Common Issues

1. **Rate not updating**: Clear the cache using `clear_hourly_rate_cache()`
2. **Migration errors**: Ensure all previous migrations are applied
3. **Admin access**: Make sure you have admin permissions

### Debug Commands

```bash
# Check if rates exist
python manage.py shell
>>> from quotes.models import HourlyRate
>>> HourlyRate.objects.all()

# Test rate retrieval
>>> from quotes.utils import get_hourly_rate
>>> get_hourly_rate('office_cleaning')
```

## Future Enhancements

Potential improvements for the system:
1. **Rate History**: Track rate changes over time
2. **Effective Dates**: Set rates to take effect on specific dates
3. **Customer-Specific Rates**: Different rates for different customer tiers
4. **Seasonal Pricing**: Different rates for different seasons
5. **API Endpoints**: REST API for rate management

## Support

If you encounter any issues:
1. Check the Django logs for error messages
2. Verify the database migrations are applied
3. Ensure the admin user has proper permissions
4. Check that the HourlyRate model is properly imported in admin.py

# CleanHandy Booking System

A comprehensive multi-step booking engine for cleaning services built with Django.

## Features

### 🏠 Service Types
- **Home Cleaning**: Residential cleaning services
- **Office Cleaning**: Commercial cleaning services

### 📋 Multi-Step Booking Process
1. **Service Details**: Choose bedrooms, bathrooms, cleaning type, pet status
2. **Extra Services**: Select additional services (fridge, oven, windows, etc.)
3. **Frequency**: One-time, weekly (15% off), bi-weekly (10% off), monthly (5% off)
4. **Date & Time**: Interactive calendar with available time slots
5. **Contact Information**: Name, email, phone, access method
6. **Location**: Full address details
7. **Confirmation**: Review all details and accept terms

### 🎯 Key Features
- **Session Management**: Multi-step form with data persistence
- **Dynamic Pricing**: Automatic calculation based on service options
- **Time Slot Management**: Configurable availability for different service types
- **Responsive Design**: Mobile-friendly interface
- **Admin Interface**: Comprehensive booking management
- **Extra Services**: 16+ additional cleaning options

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations bookings
python manage.py migrate
```

### 3. Populate Initial Data
```bash
python manage.py populate_booking_data
```

### 4. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 5. Run Development Server
```bash
python manage.py runserver
```

## Usage

### For Customers
1. Visit `/bookings/` to start the booking process
2. Choose between Home Cleaning or Office Cleaning
3. Complete the 7-step booking form
4. Receive confirmation and booking details

### For Administrators
1. Access `/django-admin/` or `/admin/`
2. Manage bookings, service types, and extra services
3. View booking statistics and customer information
4. Update booking statuses and manage schedules

## Models

### ServiceType
- Defines available service categories (Home Cleaning, Office Cleaning)

### ExtraService
- Additional services with pricing and time requirements
- Includes icons and descriptions for UI display

### TimeSlot
- Available time slots for each service type and day of week
- Configurable availability and scheduling

### Booking
- Complete booking information with all customer details
- Automatic pricing calculation and discount application
- Status tracking and management

## Forms

The system uses separate forms for each step:
- `Step1ServiceDetailsForm`: Service type, bedrooms, bathrooms, cleaning type, pets
- `Step2ExtrasForm`: Extra services selection and additional details
- `Step3FrequencyForm`: Cleaning frequency with loyalty program discounts
- `Step4DateTimeForm`: Date and time selection with timezone options
- `Step5ContactForm`: Customer contact information and access method
- `Step6LocationForm`: Service location and address details
- `Step7ConfirmationForm`: Terms acceptance and final confirmation

## Templates

### Base Template
- Responsive design with Bootstrap 5
- Step indicator with progress bar
- Modern UI with smooth animations

### Step Templates
- Each step has its own template with specific styling
- Interactive elements (calendar, time slots, service selection)
- Form validation and error handling

### Confirmation Template
- Complete booking summary
- Next steps and contact information
- Professional receipt-style layout

## Admin Features

### Booking Management
- List view with search and filtering
- Detailed booking information
- Status updates and management actions
- Bulk operations (confirm, complete, cancel)

### Service Configuration
- Service type management
- Extra service pricing and configuration
- Time slot availability management

## Pricing System

### Base Pricing
- Starting at $50 for basic service
- Additional costs for bedrooms and bathrooms
- Deep cleaning multiplier (1.5x)
- Pet fee ($25)

### Extra Services
- Individual pricing for each service
- Time-based services with duration tracking
- Free upgrades available (e.g., Go Green)

### Loyalty Discounts
- Weekly: 15% off
- Bi-weekly: 10% off
- Monthly: 5% off

## Customization

### Adding New Services
1. Create new `ExtraService` objects in admin
2. Set pricing, description, and icon
3. Services automatically appear in step 2

### Modifying Time Slots
1. Update `TimeSlot` objects in admin
2. Configure availability for different days
3. Set service-specific scheduling

### Pricing Adjustments
1. Modify base pricing in `calculate_base_price()` method
2. Update extra service prices in admin
3. Adjust loyalty program discounts

## API Endpoints

### Available Times
- `GET /bookings/api/available-times/`
- Returns available time slots for a specific date and service type

### Session Management
- Session-based multi-step form
- Data persistence between steps
- Automatic cleanup after booking completion

## Security Features

- CSRF protection on all forms
- Session-based data storage
- Input validation and sanitization
- Admin-only access to sensitive operations

## Responsive Design

- Mobile-first approach
- Bootstrap 5 framework
- Custom CSS with CSS variables
- Touch-friendly interface elements

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Mobile)
- Responsive design for all screen sizes

## Future Enhancements

- Email notifications and confirmations
- SMS reminders and updates
- Payment integration
- Customer portal and booking history
- Integration with calendar systems
- Multi-language support
- Advanced scheduling algorithms

## Support

For technical support or questions about the booking system:
- Email: support@cleanhandy.com
- Documentation: Check this README and Django admin
- Issues: Use the Django admin interface for booking management

## License

This booking system is part of the CleanHandy project and follows the same licensing terms.

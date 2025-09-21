from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from datetime import date, timedelta
import json

from .models import Booking, ExtraService, ServiceType, TimeSlot
from .forms import (
    HomeCleaningForm, OfficeCleaningForm
)

def booking_home(request):
    """Home page for booking selection"""
    service_types = ServiceType.objects.all()
    return render(request, 'bookings/booking_home.html', {
        'service_types': service_types
    })


def calculate_base_price(booking):
    """Calculate base price based on service type and details"""
    if booking.service_type.name == 'Home Cleaning':
        return calculate_home_cleaning_price(booking)
    elif booking.service_type.name == 'Office Cleaning':
        return calculate_office_cleaning_price(booking)
    else:
        return 50.00  # Default price


def calculate_home_cleaning_price(booking):
    """Calculate base price for home cleaning"""
    base_price = 50.00  # Starting price
    
    # Add per bedroom
    if booking.bedrooms:
        if 'studio' in booking.bedrooms:
            base_price += 20.00
        elif '1_bedroom' in booking.bedrooms:
            base_price += 30.00
        elif '2_bedrooms' in booking.bedrooms:
            base_price += 40.00
        elif '3_bedrooms' in booking.bedrooms:
            base_price += 50.00
        elif '4_bedrooms' in booking.bedrooms:
            base_price += 60.00
        elif '5_plus_bedrooms' in booking.bedrooms:
            base_price += 70.00
    
    # Add per bathroom
    if booking.bathrooms:
        if '1_bathroom' in booking.bathrooms:
            base_price += 15.00
        elif '2_bathrooms' in booking.bathrooms:
            base_price += 25.00
        elif '3_bathrooms' in booking.bathrooms:
            base_price += 35.00
        elif '4_plus_bathrooms' in booking.bathrooms:
            base_price += 45.00
    
    # Add cleaning type multiplier
    if booking.cleaning_type == 'deep':
        base_price *= 1.5
    
    # Add pet fee
    if booking.has_pets == 'has_pets':
        base_price += 25.00
    
    return base_price


def calculate_office_cleaning_price(booking):
    """Calculate base price for office cleaning"""
    base_price = 75.00  # Starting price for office cleaning
    
    # Add per restroom
    if booking.num_restrooms:
        base_price += booking.num_restrooms * 15.00
    
    # Add per kitchen area
    if booking.num_kitchen_areas:
        base_price += booking.num_kitchen_areas * 25.00
    
    # Add per conference room
    if booking.num_conference_rooms:
        base_price += booking.num_conference_rooms * 20.00
    
    # Add per private office
    if booking.num_private_offices:
        base_price += booking.num_private_offices * 10.00
    
    # Adjust based on crew size and hours
    if booking.crew_size_hours:
        if '2_cleaners' in booking.crew_size_hours:
            base_price *= 1.5
        elif '3_cleaners' in booking.crew_size_hours:
            base_price *= 2.0
        elif 'custom' in booking.crew_size_hours:
            base_price *= 1.2  # Custom quote adjustment
    
    return base_price


def calculate_extra_services_price(booking):
    """Calculate total price for extra services"""
    total = 0.00
    for service in booking.extra_services.all():
        total += service.base_price
    return total


def booking_confirmation(request, booking_id):
    """Show booking confirmation"""
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'bookings/booking_confirmation.html', {
        'booking': booking
    })


def get_available_times(request):
    """AJAX endpoint to get available times for a specific date"""
    date_str = request.GET.get('date')
    service_type_id = request.GET.get('service_type')
    
    if not date_str or not service_type_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        selected_date = date.fromisoformat(date_str)
        service_type = ServiceType.objects.get(id=service_type_id)
        
        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = selected_date.weekday()
        
        # Get available time slots for this day and service type
        time_slots = TimeSlot.objects.filter(
            service_type=service_type,
            day_of_week=day_of_week,
            is_available=True
        ).order_by('start_time')
        
        times = [slot.start_time.strftime('%H:%M') for slot in time_slots]
        
        return JsonResponse({'times': times})
    except (ValueError, ServiceType.DoesNotExist):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)


class BookingListView(LoginRequiredMixin, ListView):
    """List all bookings (admin view)"""
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Add search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(street_address__icontains=search_query)
            )
        return queryset


class BookingDetailView(LoginRequiredMixin, DetailView):
    """Show booking details (admin view)"""
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'


def home_cleaning_booking(request):
    """Home cleaning booking form - show the comprehensive cleaning_booking.html template"""
    from quotes.models import ServiceCategory, SquareFeetOption, HomeType, CleaningExtra
    from quotes.forms import CleaningBookingForm
    
    try:
        # Get the cleaning service category
        service_cat = ServiceCategory.objects.filter(name__icontains='cleaning').first()
        
        # Get all required data for the comprehensive form
        square_feet_options = SquareFeetOption.objects.all()
        home_types = HomeType.objects.all()
        cleaning_extras = CleaningExtra.objects.all()
        
        # Create the form
        form = CleaningBookingForm()
        
        # Get all services for the banner
        all_services = []
        try:
            from quotes.models import Service
            all_services = Service.objects.all()
        except:
            pass
        
        return render(request, 'booking/cleaning_booking.html', {
            'form': form,
            'service_cat': service_cat,
            'square_feet_options': square_feet_options,
            'home_types': home_types,
            'cleaning_extras': cleaning_extras,
            'saved_addresses': [],  # Empty list since CustomerAddress doesn't exist
            'all_services': all_services,
        })
    except Exception as e:
        messages.error(request, f'There was an issue loading the booking form: {str(e)}')
        return redirect('bookings:booking_home')


def office_cleaning_booking(request):
    """Complete Office Cleaning booking in one form"""
    try:
        if request.method == 'POST':
            form = OfficeCleaningForm(request.POST)
            if form.is_valid():
                # Create the booking
                booking = form.save(commit=False)
                
                # Calculate pricing
                booking.base_price = calculate_base_price(booking)
                booking.extra_services_total = calculate_extra_services_price(booking)
                booking.calculate_total_price()
                booking.save()
                
                # Add extra services
                if form.cleaned_data.get('extra_services'):
                    booking.extra_services.set(form.cleaned_data['extra_services'])
                
                messages.success(request, 'Office Cleaning booking created successfully! You will receive a confirmation email shortly.')
                return redirect('bookings:booking_confirmation', booking_id=booking.id)
        else:
            try:
                form = OfficeCleaningForm()
            except Exception as form_error:
                # If the form can't be created, create a simple message form
                messages.error(request, f'There was an issue loading the booking form: {str(form_error)}')
                return redirect('bookings:booking_home')
        
        try:
            extra_services = ExtraService.objects.all()
        except:
            extra_services = []
        
        return render(request, 'bookings/office_cleaning_booking.html', {
            'form': form,
            'extra_services': extra_services
        })
    except Exception as e:
        # If there's an issue with the form (e.g., ExtraService model doesn't exist)
        messages.error(request, f'There was an issue loading the booking form: {str(e)}')
        return redirect('bookings:booking_home')

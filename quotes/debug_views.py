from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Booking
from decimal import Decimal

@csrf_exempt
def debug_booking_calculation(request, booking_id):
    """Debug endpoint to check booking calculation"""
    try:
        booking = Booking.objects.get(id=booking_id)
        
        debug_info = {
            'booking_id': booking.id,
            'square_feet_options': str(booking.square_feet_options) if booking.square_feet_options else None,
            'home_types': str(booking.home_types) if booking.home_types else None,
            'extras': [str(extra) for extra in booking.extras.all()],
            'hours_requested': booking.hours_requested,
            'num_cleaners': booking.num_cleaners,
            'gift_card_discount': str(booking.gift_card_discount) if booking.gift_card_discount else None,
            'is_large_home': booking.is_large_home(),
        }
        
        # Try to calculate total
        try:
            total = booking.calculate_total_price()
            debug_info['calculated_total'] = str(total)
            debug_info['total_is_valid'] = total is not None and total > 0
        except Exception as e:
            debug_info['calculation_error'] = str(e)
        
        # Try to create payment split with manual amount
        try:
            manual_total = 370.18  # Test amount
            split = booking.get_payment_split(manual_total=manual_total)
            debug_info['payment_split_created'] = True
            debug_info['payment_split_total'] = str(split.total_amount)
            debug_info['payment_split_deposit'] = str(split.deposit_amount)
            debug_info['payment_split_final'] = str(split.final_amount)
        except Exception as e:
            debug_info['payment_split_error'] = str(e)
        
        return JsonResponse(debug_info)
        
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

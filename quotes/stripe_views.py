import stripe
import json
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal
from .models import Booking
from .payment_models import Payment, PaymentSplit

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(request):
    """Create a Stripe Payment Intent for deposit or final payment"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        payment_type = data.get('payment_type')  # 'deposit' or 'final'
        
        if not booking_id or not payment_type:
            return JsonResponse({'error': 'Missing booking_id or payment_type'}, status=400)
        
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return JsonResponse({'error': 'Booking not found'}, status=404)
        
        # Get payment split
        print(f"Creating payment intent for booking {booking_id}, payment_type: {payment_type}")
        print(f"Booking total price: {booking.calculate_total_price()}")
        print(f"Booking gift_card_discount: {booking.gift_card_discount}")
        
        # Check if frontend provided a manual total amount
        frontend_total = data.get('frontend_total_amount')
        print(f"🔍 Frontend total received: {frontend_total}")
        print(f"🔍 Frontend total type: {type(frontend_total)}")
        
        if frontend_total and frontend_total > 0:
            print(f"✅ Using frontend total amount: {frontend_total}")
            try:
                split = booking.get_payment_split(manual_total=frontend_total)
            except Exception as e:
                print(f"❌ Error creating split with frontend total: {e}")
                # Fallback to calculated total
                split = booking.get_payment_split()
        else:
            print("⚠️ No valid frontend total, using backend calculated total")
            split = booking.get_payment_split()
            
        print(f"PaymentSplit total_amount: {split.total_amount}")
        print(f"PaymentSplit deposit_amount: {split.deposit_amount}")
        print(f"PaymentSplit final_amount: {split.final_amount}")
        
        # Safety check for None amounts
        if split.total_amount is None or split.deposit_amount is None or split.final_amount is None:
            print(f"❌ ERROR: PaymentSplit amounts are None, recreating with fallback")
            # Delete the invalid split and recreate
            split.delete()
            fallback_total = Decimal("100.00")
            split = booking.get_payment_split(manual_total=fallback_total)
            print(f"✅ Recreated PaymentSplit with fallback amounts")
            print(f"New PaymentSplit total_amount: {split.total_amount}")
            print(f"New PaymentSplit deposit_amount: {split.deposit_amount}")
            print(f"New PaymentSplit final_amount: {split.final_amount}")
        
        # Determine amount and payment intent ID
        if payment_type == 'deposit':
            amount = split.deposit_amount
            existing_intent_id = split.deposit_payment_intent_id
        elif payment_type == 'final':
            if not split.deposit_paid:
                return JsonResponse({'error': 'Deposit must be paid before final payment'}, status=400)
            amount = split.final_amount
            existing_intent_id = split.final_payment_intent_id
        else:
            return JsonResponse({'error': 'Invalid payment_type'}, status=400)
        
        # Check if payment already exists and is successful
        if payment_type == 'deposit' and split.deposit_paid:
            return JsonResponse({'error': 'Deposit already paid'}, status=400)
        elif payment_type == 'final' and split.final_paid:
            return JsonResponse({'error': 'Final payment already paid'}, status=400)
        
        # Convert to cents for Stripe
        amount_cents = int(amount * 100)
        
        # Create or retrieve existing payment intent
        if existing_intent_id:
            try:
                intent = stripe.PaymentIntent.retrieve(existing_intent_id)
                if intent.status == 'succeeded':
                    return JsonResponse({'error': 'Payment already completed'}, status=400)
            except stripe.error.InvalidRequestError:
                # Intent doesn't exist, create a new one
                existing_intent_id = None
        
        if not existing_intent_id:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=settings.STRIPE_CURRENCY,
                metadata={
                    'booking_id': booking_id,
                    'payment_type': payment_type,
                    'customer_name': booking.name,
                    'customer_email': booking.email,
                },
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            
            # Save payment intent ID
            if payment_type == 'deposit':
                split.deposit_payment_intent_id = intent.id
            else:
                split.final_payment_intent_id = intent.id
            split.save()
            
            # Create Payment record
            Payment.objects.create(
                booking=booking,
                stripe_payment_intent_id=intent.id,
                amount=amount,
                currency=settings.STRIPE_CURRENCY,
                payment_type=payment_type,
                status='pending'
            )
        else:
            intent = stripe.PaymentIntent.retrieve(existing_intent_id)
        
        return JsonResponse({
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id,
            'amount': amount,
            'payment_type': payment_type,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in create_payment_intent: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JsonResponse({'error': str(e), 'traceback': error_trace}, status=500)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks for payment status updates"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_payment_success(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_payment_failure(payment_intent)
    elif event['type'] == 'payment_intent.canceled':
        payment_intent = event['data']['object']
        handle_payment_cancellation(payment_intent)
    
    return HttpResponse(status=200)


def handle_payment_success(payment_intent):
    """Handle successful payment"""
    try:
        payment_intent_id = payment_intent['id']
        booking_id = payment_intent['metadata'].get('booking_id')
        payment_type = payment_intent['metadata'].get('payment_type')
        
        if not booking_id or not payment_type:
            print(f"Missing metadata in payment intent {payment_intent_id}")
            return
        
        # Update Payment record
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            payment.status = 'succeeded'
            payment.paid_at = timezone.now()
            payment.stripe_charge_id = payment_intent.get('latest_charge')
            payment.save()
        except Payment.DoesNotExist:
            print(f"Payment record not found for intent {payment_intent_id}")
            return
        
        # Update PaymentSplit
        try:
            booking = Booking.objects.get(id=booking_id)
            split = booking.get_payment_split()
            
            if payment_type == 'deposit':
                split.deposit_paid = True
            elif payment_type == 'final':
                split.final_paid = True
            
            split.save()
            
            # Update booking payment status
            booking.payment_method = 'stripe'
            booking.update_payment_status()
            
            print(f"Payment {payment_type} succeeded for booking {booking_id}")
            
        except Booking.DoesNotExist:
            print(f"Booking {booking_id} not found")
            
    except Exception as e:
        print(f"Error handling payment success: {e}")


def handle_payment_failure(payment_intent):
    """Handle failed payment"""
    try:
        payment_intent_id = payment_intent['id']
        
        # Update Payment record
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            payment.status = 'failed'
            payment.failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
            payment.save()
        except Payment.DoesNotExist:
            print(f"Payment record not found for intent {payment_intent_id}")
            
    except Exception as e:
        print(f"Error handling payment failure: {e}")


def handle_payment_cancellation(payment_intent):
    """Handle canceled payment"""
    try:
        payment_intent_id = payment_intent['id']
        
        # Update Payment record
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            payment.status = 'canceled'
            payment.save()
        except Payment.DoesNotExist:
            print(f"Payment record not found for intent {payment_intent_id}")
            
    except Exception as e:
        print(f"Error handling payment cancellation: {e}")


def get_payment_status(request, booking_id):
    """Get payment status for a booking"""
    try:
        booking = Booking.objects.get(id=booking_id)
        split = booking.get_payment_split()
        
        return JsonResponse({
            'booking_id': booking_id,
            'total_amount': float(split.total_amount),
            'deposit_amount': float(split.deposit_amount),
            'final_amount': float(split.final_amount),
            'deposit_paid': split.deposit_paid,
            'final_paid': split.final_paid,
            'payment_status': booking.payment_status,
            'can_make_final_payment': booking.can_make_final_payment(),
        })
        
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

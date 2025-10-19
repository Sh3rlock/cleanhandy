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
from django.urls import reverse

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
            
            # Use a reasonable fallback based on service type
            if booking.service_cat.name.lower() == 'commercial':
                if booking.num_cleaners and booking.hours_requested:
                    fallback_total = Decimal(str(booking.num_cleaners)) * Decimal(str(booking.hours_requested)) * Decimal("75.00")
                else:
                    fallback_total = Decimal("200.00")
            else:
                fallback_total = Decimal("150.00")
            
            split = booking.get_payment_split(manual_total=fallback_total)
            print(f"✅ Recreated PaymentSplit with fallback amounts: {fallback_total}")
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
        elif payment_type == 'full':
            # For full payment, use the total amount and check if any payment has been made
            if split.deposit_paid or split.final_paid:
                return JsonResponse({'error': 'Partial payments already made, cannot process full payment'}, status=400)
            amount = split.total_amount
            existing_intent_id = split.deposit_payment_intent_id  # Use deposit intent ID for full payments
        else:
            return JsonResponse({'error': 'Invalid payment_type'}, status=400)
        
        # Check if payment already exists and is successful
        if payment_type == 'deposit' and split.deposit_paid:
            return JsonResponse({'error': 'Deposit already paid'}, status=400)
        elif payment_type == 'final' and split.final_paid:
            return JsonResponse({'error': 'Final payment already paid'}, status=400)
        elif payment_type == 'full' and (split.deposit_paid or split.final_paid):
            return JsonResponse({'error': 'Payment already made'}, status=400)
        
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
            elif payment_type == 'final':
                split.final_payment_intent_id = intent.id
            elif payment_type == 'full':
                split.deposit_payment_intent_id = intent.id  # Store full payment in deposit intent ID
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


def create_checkout_session(request):
    """Create a Stripe Checkout Session for deposit or final payment"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        payment_type = data.get('payment_type')  # 'deposit', 'final', or 'full'
        
        if not booking_id or not payment_type:
            return JsonResponse({'error': 'Missing booking_id or payment_type'}, status=400)
        
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return JsonResponse({'error': 'Booking not found'}, status=404)
        
        # Get payment split
        print(f"🔍 Creating checkout session for booking {booking_id}, payment_type: {payment_type}")
        
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
                split = booking.get_payment_split()
        else:
            print("⚠️ No valid frontend total, using backend calculated total")
            split = booking.get_payment_split()
            
        print(f"🔍 PaymentSplit total_amount: {split.total_amount}")
        print(f"🔍 PaymentSplit deposit_amount: {split.deposit_amount}")
        print(f"🔍 PaymentSplit final_amount: {split.final_amount}")
        
        # Determine amount and check payment status
        if payment_type == 'deposit':
            amount = split.deposit_amount
            print(f"🔍 Using deposit amount: {amount}")
            if split.deposit_paid:
                return JsonResponse({'error': 'Deposit already paid'}, status=400)
        elif payment_type == 'final':
            if not split.deposit_paid:
                return JsonResponse({'error': 'Deposit must be paid before final payment'}, status=400)
            amount = split.final_amount
            print(f"🔍 Using final amount: {amount}")
            if split.final_paid:
                return JsonResponse({'error': 'Final payment already paid'}, status=400)
        elif payment_type == 'full':
            if split.deposit_paid or split.final_paid:
                return JsonResponse({'error': 'Partial payments already made, cannot process full payment'}, status=400)
            amount = split.total_amount
            print(f"🔍 Using full amount: {amount}")
        else:
            return JsonResponse({'error': 'Invalid payment_type'}, status=400)
        
        # Create success and cancel URLs
        success_url = request.build_absolute_uri(
            reverse('booking_confirmation', kwargs={'booking_id': booking_id})
        ) + '?payment=success&type=' + payment_type
        
        cancel_url = request.build_absolute_uri(
            reverse('office_cleaning_booking') if 'office' in request.path else reverse('cleaning_booking')
        ) + '?payment=cancelled'
        
        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': settings.STRIPE_CURRENCY,
                    'product_data': {
                        'name': f'Office Cleaning Service - {payment_type.title()} Payment',
                        'description': f'Booking ID: {booking_id} - {payment_type.title()} Payment',
                    },
                    'unit_amount': int(amount * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'booking_id': booking_id,
                'payment_type': payment_type,
                'customer_name': booking.name,
                'customer_email': booking.email,
            },
            customer_email=booking.email,
            billing_address_collection='required',
        )
        
        # Store checkout session ID in payment split for reference
        if payment_type == 'deposit':
            split.deposit_payment_intent_id = checkout_session.id
        elif payment_type == 'final':
            split.final_payment_intent_id = checkout_session.id
        elif payment_type == 'full':
            split.deposit_payment_intent_id = checkout_session.id
        split.save()
        
        # Create Payment record
        Payment.objects.create(
            booking=booking,
            stripe_payment_intent_id=checkout_session.id,
            amount=amount,
            currency=settings.STRIPE_CURRENCY,
            payment_type=payment_type,
            status='pending'
        )
        
        return JsonResponse({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id,
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
        print(f"Error in create_checkout_session: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JsonResponse({'error': str(e), 'traceback': error_trace}, status=500)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks for payment status updates"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    print(f"🔍 Webhook received - Event type: {request.META.get('HTTP_STRIPE_SIGNATURE', 'No signature')}")
    print(f"🔍 Webhook secret configured: {bool(settings.STRIPE_WEBHOOK_SECRET)}")
    print(f"🔍 Webhook secret length: {len(settings.STRIPE_WEBHOOK_SECRET) if settings.STRIPE_WEBHOOK_SECRET else 0}")
    print(f"🔍 Webhook secret starts with whsec_: {settings.STRIPE_WEBHOOK_SECRET.startswith('whsec_') if settings.STRIPE_WEBHOOK_SECRET else False}")
    print(f"🔍 Payload length: {len(payload)} bytes")
    print(f"🔍 Content-Type: {request.META.get('CONTENT_TYPE', 'Not set')}")
    print(f"🔍 User-Agent: {request.META.get('HTTP_USER_AGENT', 'Not set')}")
    print(f"🔍 Remote IP: {request.META.get('REMOTE_ADDR', 'Not set')}")
    
    # Handle test requests (no signature or invalid signature)
    if not sig_header:
        print("⚠️ No Stripe signature header - treating as test request")
        try:
            test_data = json.loads(payload)
            print(f"✅ Test webhook data received: {test_data}")
            return HttpResponse("Test webhook received", status=200)
        except json.JSONDecodeError:
            print("❌ Invalid JSON in test request")
            return HttpResponse("Invalid JSON", status=400)
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        print(f"✅ Webhook event verified: {event['type']}")
        print(f"✅ Event ID: {event.get('id', 'No ID')}")
        print(f"✅ Event created: {event.get('created', 'No timestamp')}")
    except ValueError as e:
        print(f"❌ Webhook ValueError: {e}")
        print(f"❌ This usually means the payload is not valid JSON")
        return HttpResponse(f"Invalid payload: {e}", status=400)
    except stripe.error.SignatureVerificationError as e:
        print(f"❌ Webhook SignatureVerificationError: {e}")
        print(f"❌ This means the webhook secret is wrong or the signature is invalid")
        print(f"❌ Expected webhook secret to start with 'whsec_'")
        print(f"❌ Current webhook secret: {settings.STRIPE_WEBHOOK_SECRET[:10] if settings.STRIPE_WEBHOOK_SECRET else 'None'}...")
        return HttpResponse(f"Invalid signature: {e}", status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_success(session)
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_payment_success(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_payment_failure(payment_intent)
    elif event['type'] == 'payment_intent.canceled':
        payment_intent = event['data']['object']
        handle_payment_cancellation(payment_intent)
    
    return HttpResponse(status=200)


def handle_checkout_success(session):
    """Handle successful checkout session completion"""
    try:
        session_id = session['id']
        booking_id = session['metadata'].get('booking_id')
        payment_type = session['metadata'].get('payment_type')
        
        if not booking_id or not payment_type:
            print(f"Missing metadata in checkout session {session_id}")
            return
        
        # Update Payment record
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=session_id)
            payment.status = 'succeeded'
            payment.paid_at = timezone.now()
            payment.stripe_charge_id = session.get('payment_intent')
            payment.save()
        except Payment.DoesNotExist:
            print(f"Payment record not found for session {session_id}")
            return
        
        # Update PaymentSplit
        try:
            booking = Booking.objects.get(id=booking_id)
            split = booking.get_payment_split()
            
            if payment_type == 'deposit':
                split.deposit_paid = True
            elif payment_type == 'final':
                split.final_paid = True
            elif payment_type == 'full':
                split.deposit_paid = True
                split.final_paid = True  # Full payment covers both
            
            split.save()
            
            # Update booking payment status
            booking.payment_method = 'stripe'
            booking.update_payment_status()
            
            print(f"Checkout payment {payment_type} succeeded for booking {booking_id}")
            
        except Booking.DoesNotExist:
            print(f"Booking {booking_id} not found")
            
    except Exception as e:
        print(f"Error handling checkout success: {e}")


def handle_payment_success(payment_intent):
    """Handle successful payment"""
    try:
        payment_intent_id = payment_intent['id']
        metadata = payment_intent.get('metadata', {})
        booking_id = metadata.get('booking_id')
        payment_type = metadata.get('payment_type')
        
        print(f"🔍 Processing payment success for intent {payment_intent_id}")
        print(f"🔍 Booking ID: {booking_id}, Payment Type: {payment_type}")
        print(f"🔍 Payment Intent metadata: {metadata}")
        print(f"🔍 All metadata keys: {list(metadata.keys())}")
        
        if not booking_id or not payment_type:
            print(f"❌ Missing metadata in payment intent {payment_intent_id}")
            print(f"❌ Available metadata: {metadata}")
            
            # Try to find the booking by payment intent ID in our database
            try:
                payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
                booking_id = payment.booking.id
                payment_type = payment.payment_type
                print(f"✅ Found booking {booking_id} and payment_type {payment_type} from Payment record")
            except Payment.DoesNotExist:
                print(f"❌ No Payment record found for intent {payment_intent_id}")
                return
            except Exception as e:
                print(f"❌ Error finding Payment record: {e}")
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
            
            print(f"🔍 Before update - Deposit paid: {split.deposit_paid}, Final paid: {split.final_paid}")
            print(f"🔍 Booking payment status before: {booking.payment_status}")
            
            if payment_type == 'deposit':
                split.deposit_paid = True
                print(f"✅ Set deposit_paid = True")
            elif payment_type == 'final':
                split.final_paid = True
                print(f"✅ Set final_paid = True")
            elif payment_type == 'full':
                split.deposit_paid = True
                split.final_paid = True  # Full payment covers both
                print(f"✅ Set both deposit_paid and final_paid = True")
            
            split.save()
            print(f"✅ PaymentSplit saved - Deposit: {split.deposit_paid}, Final: {split.final_paid}")
            
            # Update booking payment status
            booking.payment_method = 'stripe'
            booking.update_payment_status()
            print(f"✅ Booking payment status updated to: {booking.payment_status}")
            
            print(f"✅ Payment {payment_type} succeeded for booking {booking_id}")
            
        except Booking.DoesNotExist:
            print(f"❌ Booking {booking_id} not found")
            
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


def check_and_fix_payment_status(request):
    """Debug endpoint to check and fix payment status for a booking"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        
        if not booking_id:
            return JsonResponse({'error': 'Missing booking_id'}, status=400)
        
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return JsonResponse({'error': 'Booking not found'}, status=404)
        
        # Get current status
        current_status = booking.payment_status
        split = booking.get_payment_split()
        
        # Check Stripe payment status
        stripe_status = {}
        if split.deposit_payment_intent_id:
            try:
                intent = stripe.PaymentIntent.retrieve(split.deposit_payment_intent_id)
                stripe_status['deposit'] = {
                    'status': intent.status,
                    'amount': intent.amount / 100,
                    'paid': intent.status == 'succeeded'
                }
            except stripe.error.StripeError as e:
                stripe_status['deposit'] = {'error': str(e)}
        
        if split.final_payment_intent_id:
            try:
                intent = stripe.PaymentIntent.retrieve(split.final_payment_intent_id)
                stripe_status['final'] = {
                    'status': intent.status,
                    'amount': intent.amount / 100,
                    'paid': intent.status == 'succeeded'
                }
            except stripe.error.StripeError as e:
                stripe_status['final'] = {'error': str(e)}
        
        # Fix payment status if needed
        fixed = False
        if stripe_status.get('deposit', {}).get('paid') and not split.deposit_paid:
            split.deposit_paid = True
            fixed = True
        
        if stripe_status.get('final', {}).get('paid') and not split.final_paid:
            split.final_paid = True
            fixed = True
        
        if fixed:
            split.save()
            booking.update_payment_status()
        
        return JsonResponse({
            'booking_id': booking_id,
            'current_status': current_status,
            'new_status': booking.payment_status,
            'stripe_status': stripe_status,
            'split_status': {
                'deposit_paid': split.deposit_paid,
                'final_paid': split.final_paid,
                'is_fully_paid': split.is_fully_paid
            },
            'fixed': fixed
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def fix_payment_intent_metadata(request):
    """Fix a specific payment intent that's missing metadata"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return JsonResponse({'error': 'Missing payment_intent_id'}, status=400)
        
        # Try to find the payment in our database
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            booking = payment.booking
            payment_type = payment.payment_type
            
            print(f"🔍 Found payment record for intent {payment_intent_id}")
            print(f"🔍 Booking ID: {booking.id}, Payment Type: {payment_type}")
            
            # Update the Stripe payment intent with metadata
            stripe.PaymentIntent.modify(
                payment_intent_id,
                metadata={
                    'booking_id': str(booking.id),
                    'payment_type': payment_type,
                    'customer_name': booking.name,
                    'customer_email': booking.email,
                }
            )
            
            print(f"✅ Updated payment intent {payment_intent_id} with metadata")
            
            # Now trigger the payment success handler
            try:
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                if intent.status == 'succeeded':
                    handle_payment_success(intent)
                    print(f"✅ Triggered payment success handler for {payment_intent_id}")
                else:
                    print(f"⚠️ Payment intent {payment_intent_id} status is {intent.status}, not succeeded")
            except Exception as e:
                print(f"❌ Error triggering payment success handler: {e}")
            
            return JsonResponse({
                'success': True,
                'payment_intent_id': payment_intent_id,
                'booking_id': booking.id,
                'payment_type': payment_type,
                'message': 'Payment intent metadata updated and handler triggered'
            })
            
        except Payment.DoesNotExist:
            return JsonResponse({'error': f'No payment record found for intent {payment_intent_id}'}, status=404)
        except stripe.error.StripeError as e:
            return JsonResponse({'error': f'Stripe error: {str(e)}'}, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def webhook_test(request):
    """Test endpoint for webhook debugging"""
    if request.method == 'GET':
        return JsonResponse({
            'status': 'Webhook test endpoint is working',
            'webhook_secret_configured': bool(settings.STRIPE_WEBHOOK_SECRET),
            'webhook_url': '/quotes/api/webhook/stripe/',
            'instructions': {
                'test_without_signature': 'POST to /quotes/api/webhook/stripe/ with JSON data',
                'test_with_signature': 'POST with Stripe-Signature header (will fail with invalid signature)',
                'real_webhook': 'Configure in Stripe Dashboard with proper webhook secret'
            }
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def manual_webhook_trigger(request, booking_id):
    """Manually trigger webhook processing for a booking (for testing)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        booking = Booking.objects.get(id=booking_id)
        payments = Payment.objects.filter(booking=booking, status='pending')
        
        if not payments.exists():
            return JsonResponse({'error': 'No pending payments found for this booking'}, status=404)
        
        results = []
        for payment in payments:
            # Create mock payment intent data
            mock_payment_intent = {
                'id': payment.stripe_payment_intent_id,
                'metadata': {
                    'booking_id': str(booking.id),
                    'payment_type': payment.payment_type
                },
                'latest_charge': f'ch_manual_{payment.id}'
            }
            
            # Process the webhook
            try:
                handle_payment_success(mock_payment_intent)
                results.append({
                    'payment_id': payment.id,
                    'payment_type': payment.payment_type,
                    'status': 'success'
                })
            except Exception as e:
                results.append({
                    'payment_id': payment.id,
                    'payment_type': payment.payment_type,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Refresh booking status
        booking.refresh_from_db()
        split = booking.get_payment_split()
        
        return JsonResponse({
            'status': 'Webhook processing completed',
            'booking_id': booking_id,
            'booking_payment_status': booking.payment_status,
            'payment_split': {
                'deposit_paid': split.deposit_paid,
                'final_paid': split.final_paid
            },
            'results': results
        })
        
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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

# 🔧 Stripe Webhook Fix for Payment Status Issues

## 🚨 Problem Identified

The main issue causing payments to show as "unpaid" instead of "50%" or "100%" paid is:

**Incorrect Webhook Secret Configuration**: The `STRIPE_WEBHOOK_SECRET` in settings.py was set to `'we_1SEuTkLSdyC2HP6eQi6QoHiz'` which is a payment intent ID, not a webhook secret. This causes all webhook events to fail signature verification, so payment status updates never happen.

## ✅ What I Fixed

1. **Fixed Webhook Secret**: Changed from incorrect payment intent ID to empty string (will use environment variable)
2. **Added Debugging**: Added comprehensive logging to webhook handlers to track payment processing
3. **Enhanced Error Handling**: Better error messages for webhook signature verification

## 🔧 Setup Steps for Railway Production

### 1. Get Correct Webhook Secret from Stripe Dashboard

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Developers > Webhooks**
3. Find your webhook endpoint: `https://your-railway-domain.com/quotes/api/webhook/stripe/`
4. Click on the webhook endpoint
5. Copy the **Signing Secret** (starts with `whsec_`)

### 2. Update Railway Environment Variables

In your Railway project settings, add/update:

```bash
STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret_here
```

### 3. Verify Webhook Events

Make sure your Stripe webhook is configured to listen for these events:
- `payment_intent.succeeded`
- `payment_intent.payment_failed` 
- `payment_intent.canceled`
- `checkout.session.completed`

### 4. Test the Fix

1. Make a test payment
2. Check Railway logs for webhook debugging output:
   - Look for `🔍 Webhook received` messages
   - Look for `✅ Webhook event verified` messages
   - Look for `✅ Payment succeeded` messages

## 🔍 Debugging Commands

### Check Current Webhook Configuration
```bash
# In Railway console or local terminal
python manage.py shell
>>> from django.conf import settings
>>> print(f"Webhook secret configured: {bool(settings.STRIPE_WEBHOOK_SECRET)}")
>>> print(f"Webhook secret length: {len(settings.STRIPE_WEBHOOK_SECRET) if settings.STRIPE_WEBHOOK_SECRET else 0}")
```

### Check Recent Payments
```bash
python manage.py shell
>>> from quotes.models import Payment, Booking
>>> recent_payments = Payment.objects.filter(status='succeeded').order_by('-created_at')[:5]
>>> for p in recent_payments:
...     print(f"Payment {p.id}: {p.payment_type} - {p.status} - Booking {p.booking.id} - Status: {p.booking.payment_status}")
```

### Check Payment Splits
```bash
python manage.py shell
>>> from quotes.models import PaymentSplit
>>> recent_splits = PaymentSplit.objects.filter(booking__created_at__gte=timezone.now() - timedelta(days=1))
>>> for s in recent_splits:
...     print(f"Split {s.id}: Deposit: {s.deposit_paid}, Final: {s.final_paid}, Booking Status: {s.booking.payment_status}")
```

## 🎯 Expected Behavior After Fix

1. **50% Deposit Payment**: 
   - Payment status should show "partial" (50% paid)
   - `deposit_paid = True`, `final_paid = False`

2. **Full Payment**:
   - Payment status should show "paid" (100% paid)  
   - `deposit_paid = True`, `final_paid = True`

3. **Webhook Logs**:
   - Should see successful webhook verification
   - Should see payment status updates in logs

## 🚨 Common Issues

1. **Webhook Secret Wrong**: Must start with `whsec_`, not `we_`
2. **Webhook URL Wrong**: Must be exact URL with trailing slash
3. **Events Not Selected**: Must include `payment_intent.succeeded`
4. **Environment Variable Not Set**: Check Railway environment variables

## 📝 Next Steps

1. Update the webhook secret in Railway
2. Test with a small payment
3. Check logs for debugging output
4. Verify payment status updates correctly

The debugging output will help identify exactly where the process is failing if issues persist.

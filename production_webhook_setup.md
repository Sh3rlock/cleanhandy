# 🌐 Production Webhook Setup for thecleanhandy.com

## 🎯 **Your Production Webhook Endpoint**

**URL**: `https://thecleanhandy.com/quotes/api/webhook/stripe/`

## 📋 **Step-by-Step Stripe Dashboard Setup**

### 1. Go to Stripe Dashboard
- Visit: https://dashboard.stripe.com/
- Navigate to: **Developers > Webhooks**

### 2. Add New Endpoint
- Click: **"Add endpoint"**
- **Endpoint URL**: `https://thecleanhandy.com/quotes/api/webhook/stripe/`
- **Description**: "CleanHandy Payment Webhooks"

### 3. Select Events
Click **"Select events"** and add these events:
```
payment_intent.succeeded
payment_intent.payment_failed
payment_intent.canceled
checkout.session.completed
```

### 4. Create Endpoint
- Click: **"Add endpoint"**
- **Copy the webhook signing secret** (starts with `whsec_`)

## 🔧 **Railway Environment Variables**

Add this to your Railway project environment variables:

```bash
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_from_stripe_dashboard
```

## 🧪 **Test Your Webhook**

### 1. Test with Stripe CLI (Recommended)
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login to your Stripe account
stripe login

# Test webhook endpoint
stripe listen --forward-to https://thecleanhandy.com/quotes/api/webhook/stripe/
```

### 2. Test with Stripe Dashboard
1. Go to your webhook in Stripe Dashboard
2. Click **"Send test webhook"**
3. Select **"payment_intent.succeeded"**
4. Click **"Send test webhook"**

### 3. Check Railway Logs
Look for these debug messages in your Railway logs:
```
🔍 Webhook received - Event type: payment_intent.succeeded
✅ Webhook event verified: payment_intent.succeeded
🔍 Processing payment success for intent pi_...
✅ Payment deposit succeeded for booking 123
✅ Booking payment status updated to: partial
```

## 🔍 **Verify Webhook is Working**

### Check Webhook Status in Stripe Dashboard
1. Go to **Developers > Webhooks**
2. Click on your webhook endpoint
3. Check **"Recent deliveries"** tab
4. Look for successful deliveries (green checkmarks)

### Test Payment Flow
1. Go to https://thecleanhandy.com
2. Make a test booking with payment
3. Use test card: `4242 4242 4242 4242`
4. Check that payment status updates correctly

## 🚨 **Troubleshooting**

### If Webhook Fails
1. **Check URL**: Must be exactly `https://thecleanhandy.com/quotes/api/webhook/stripe/`
2. **Check Secret**: Must start with `whsec_`
3. **Check Events**: Must include `payment_intent.succeeded`
4. **Check SSL**: Your site must have valid SSL certificate

### Common Issues
- **404 Error**: Check that the URL path is correct
- **Signature Verification Error**: Check webhook secret
- **No Events Received**: Check that events are selected in Stripe Dashboard

## 📊 **Monitor Webhook Health**

### In Stripe Dashboard
- Go to **Developers > Webhooks**
- Click on your webhook
- Check **"Recent deliveries"** for success/failure rates
- Look for error messages in failed deliveries

### In Railway Logs
- Check for webhook debug messages
- Look for payment status updates
- Monitor for any error messages

## ✅ **Expected Results**

After setup, when customers make payments:
1. **Deposit Payment**: Status should show "partial" (50% paid)
2. **Full Payment**: Status should show "paid" (100% paid)
3. **Webhook Logs**: Should show successful processing
4. **Stripe Dashboard**: Should show successful webhook deliveries

## 🔄 **Webhook Endpoint Details**

**Full URL**: `https://thecleanhandy.com/quotes/api/webhook/stripe/`

**Method**: POST

**Authentication**: Stripe signature verification

**Events Handled**:
- `payment_intent.succeeded` → Updates payment status to succeeded
- `payment_intent.payment_failed` → Updates payment status to failed
- `payment_intent.canceled` → Updates payment status to canceled
- `checkout.session.completed` → Handles checkout session completion

This endpoint will fix your "unpaid" status issue and properly update payment statuses to "partial" or "paid" based on the payment type!

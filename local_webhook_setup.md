# 🔧 Local Stripe Webhook Testing Setup

## Option 1: Stripe CLI (Recommended)

### 1. Install Stripe CLI
```bash
# macOS
brew install stripe/stripe-cli/stripe

# Or download from: https://github.com/stripe/stripe-cli/releases
```

### 2. Login to Stripe
```bash
stripe login
```

### 3. Start webhook forwarding
```bash
stripe listen --forward-to localhost:8000/quotes/api/webhook/stripe/
```

This will output something like:
```
> Ready! Your webhook signing secret is whsec_1234567890abcdef...
```

### 4. Update your local environment
Add to your `.env` file or set as environment variable:
```bash
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_from_above
```

### 5. Test payments
- Make a test payment on your local site
- Watch the Stripe CLI output for webhook events
- Check your Django logs for the debugging output

## Option 2: ngrok (Alternative)

### 1. Install ngrok
```bash
# macOS
brew install ngrok

# Or download from: https://ngrok.com/
```

### 2. Start your Django server
```bash
cd /Users/sandormatyas/Desktop/Projects/cleanhandy/cleanhandy
python manage.py runserver
```

### 3. Expose with ngrok
```bash
ngrok http 8000
```

This will give you a URL like: `https://abc123.ngrok.io`

### 4. Add webhook in Stripe Dashboard
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/) > Developers > Webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://abc123.ngrok.io/quotes/api/webhook/stripe/`
4. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `payment_intent.canceled`
   - `checkout.session.completed`
5. Copy the webhook signing secret

### 5. Update your local environment
```bash
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_from_dashboard
```

## Testing Your Setup

### 1. Start your Django server
```bash
cd /Users/sandormatyas/Desktop/Projects/cleanhandy/cleanhandy
python manage.py runserver
```

### 2. Make a test payment
- Go to your local booking form
- Use Stripe test card: `4242 4242 4242 4242`
- Complete the payment

### 3. Check the logs
You should see output like:
```
🔍 Webhook received - Event type: payment_intent.succeeded
🔍 Webhook secret configured: True
✅ Webhook event verified: payment_intent.succeeded
🔍 Processing payment success for intent pi_...
✅ Payment deposit succeeded for booking 123
✅ Booking payment status updated to: partial
```

### 4. Verify in Django admin
- Go to `/admin/quotes/booking/`
- Check that the payment status is updated correctly

## Troubleshooting

### Webhook not receiving events
- Check that the URL is correct (must end with `/`)
- Verify the webhook secret is set correctly
- Check that your local server is running

### Signature verification errors
- Make sure you're using the correct webhook secret
- Check that the secret starts with `whsec_`

### Payment status not updating
- Check Django logs for error messages
- Verify the booking ID and payment type in metadata
- Check that the Payment and PaymentSplit records exist

## Quick Test Commands

```bash
# Check webhook secret
python manage.py shell
>>> from django.conf import settings
>>> print(f"Webhook secret: {settings.STRIPE_WEBHOOK_SECRET}")

# Check recent payments
>>> from quotes.models import Payment
>>> Payment.objects.filter(status='succeeded').order_by('-created_at')[:3]

# Check payment splits
>>> from quotes.models import PaymentSplit
>>> PaymentSplit.objects.filter(booking__created_at__gte=timezone.now() - timedelta(hours=1))
```

## Benefits of Local Testing

1. **Immediate feedback**: See webhook events in real-time
2. **Debug easily**: All logs are local and accessible
3. **Test safely**: Use test mode without affecting production
4. **Iterate quickly**: Make changes and test immediately

Choose the Stripe CLI method for the best development experience!

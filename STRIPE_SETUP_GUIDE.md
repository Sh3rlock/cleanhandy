# 🚀 Stripe Payment Integration Setup Guide

## ✅ What's Been Implemented

I've successfully integrated Stripe payments directly into both booking forms with the following features:

### **Payment Features:**
- **Direct Card Input**: Users can enter card details directly in the booking form
- **50/50 Payment Split**: Option to pay 50% deposit now, 50% after service
- **Full Payment Option**: Option to pay the full amount upfront
- **Real-time Validation**: Card validation happens as users type
- **Secure Processing**: Uses Stripe's secure payment processing

### **User Experience:**
- Payment form appears at the bottom of booking forms
- Seamless integration with existing form validation
- Loading states and success messages
- Automatic redirect to confirmation page after payment

## 🔧 Setup Steps

### **1. Install Stripe Package**
```bash
cd /Users/sandormatyas/Desktop/Projects/cleanhandy/cleanhandy
pip install stripe==10.0.0
```

### **2. Database Migration**
```bash
python manage.py makemigrations quotes
python manage.py migrate
```

### **3. Configure Stripe API Keys**
Add these environment variables to your `.env` file or set them in your deployment environment:

```bash
# Test mode keys (get from Stripe Dashboard > Developers > API keys)
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

### **4. Get Your Stripe API Keys**

1. **Go to Stripe Dashboard**: https://dashboard.stripe.com/
2. **Navigate to**: Developers > API keys
3. **Copy your keys**:
   - Publishable key (starts with `pk_test_`)
   - Secret key (starts with `sk_test_`)

### **5. Configure Stripe Webhooks**

1. **Go to Stripe Dashboard**: Developers > Webhooks
2. **Add endpoint**: `https://yourdomain.com/quotes/api/webhook/stripe/`
3. **Select events**:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
4. **Copy webhook secret** (starts with `whsec_`)

## 🎯 How It Works

### **Payment Flow:**
1. User fills out booking form
2. User selects payment option (50% deposit or full payment)
3. User enters card details directly in the form
4. Form creates booking first
5. Payment is processed through Stripe
6. User is redirected to confirmation page

### **Payment Split Logic:**
- **Deposit Option**: Charges 50% immediately, holds 50% for later
- **Full Payment**: Charges 100% immediately
- **Remaining Payment**: Can be collected after service completion

### **Security Features:**
- Card details never touch your server
- PCI compliant through Stripe
- Real-time card validation
- Secure payment intent creation

## 🧪 Testing

### **Test Card Numbers:**
```
Success: 4242 4242 4242 4242
Declined: 4000 0000 0000 0002
Requires 3D Secure: 4000 0025 0000 3155
```

### **Test Details:**
- **Expiry**: Any future date (e.g., 12/25)
- **CVC**: Any 3 digits (e.g., 123)
- **ZIP**: Any 5 digits (e.g., 12345)

## 📁 Files Modified

### **New Files:**
- `quotes/payment_models.py` - Payment tracking models
- `quotes/stripe_views.py` - Stripe API integration
- `STRIPE_SETUP_GUIDE.md` - This setup guide

### **Modified Files:**
- `requirements.txt` - Added Stripe dependency
- `cleanhandy/settings.py` - Added Stripe configuration
- `quotes/models.py` - Added payment fields to Booking model
- `quotes/views.py` - Updated booking views for AJAX support
- `quotes/urls.py` - Added Stripe API endpoints
- `templates/booking/cleaning_booking.html` - Added payment form
- `templates/partials/office_cleaning_booking_form.html` - Added payment form

## 🚨 Important Notes

### **Before Going Live:**
1. **Switch to live keys** in production
2. **Update webhook URL** to production domain
3. **Test thoroughly** with real payment methods
4. **Set up proper error handling** for failed payments

### **Security Considerations:**
- Never commit API keys to version control
- Use environment variables for all sensitive data
- Enable Stripe's fraud protection features
- Monitor payment logs regularly

## 🆘 Troubleshooting

### **Common Issues:**

**"ModuleNotFoundError: No module named 'stripe'"**
- Run: `pip install stripe==10.0.0`

**"Invalid API key"**
- Check your Stripe API keys are correct
- Ensure you're using test keys in test mode

**"Webhook signature verification failed"**
- Check your webhook secret is correct
- Ensure webhook URL is accessible

**Payment form not showing**
- Check browser console for JavaScript errors
- Verify Stripe publishable key is set correctly

### **Need Help?**
- Check Stripe documentation: https://stripe.com/docs
- Review browser console for errors
- Test with Stripe's test card numbers

## 🎉 You're Ready!

Once you've completed the setup steps, your booking forms will have integrated Stripe payments with a professional, secure payment experience for your customers!

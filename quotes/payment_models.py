from django.db import models
from django.utils import timezone
from decimal import Decimal, ROUND_DOWN
from .models import Booking


class Payment(models.Model):
    """Track individual payments for bookings"""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('deposit', 'Deposit (50%)'),
        ('final', 'Final Payment (50%)'),
        ('full', 'Full Payment'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Stripe metadata
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Error handling
    failure_reason = models.TextField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Payment {self.id} - {self.payment_type} - ${self.amount} ({self.status})"
    
    @property
    def is_successful(self):
        return self.status == 'succeeded'
    
    @property
    def is_pending(self):
        return self.status in ['pending', 'processing']
    
    @property
    def is_failed(self):
        return self.status in ['failed', 'canceled']


class PaymentSplit(models.Model):
    """Track the 50/50 payment split for bookings"""
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment_split')
    
    # Payment amounts
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment status
    deposit_paid = models.BooleanField(default=False)
    final_paid = models.BooleanField(default=False)
    
    # Stripe Payment Intents
    deposit_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    final_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PaymentSplit for Booking {self.booking.id} - Deposit: {self.deposit_paid}, Final: {self.final_paid}"
    
    @property
    def is_fully_paid(self):
        return self.deposit_paid and self.final_paid
    
    @property
    def is_deposit_paid(self):
        return self.deposit_paid
    
    @property
    def remaining_amount(self):
        if self.deposit_paid and not self.final_paid:
            return self.final_amount
        elif not self.deposit_paid and not self.final_paid:
            return self.total_amount
        else:
            return Decimal('0.00')
    
    def create_split(self, total_amount):
        """Create a 50/50 split from total amount"""
        print(f"🔍 create_split called with total_amount: {total_amount}")
        print(f"🔍 total_amount type: {type(total_amount)}")

        # Ensure total_amount is valid
        if not total_amount or total_amount <= 0:
            print(f"❌ ERROR: Invalid total_amount {total_amount}, using fallback")
            total_amount = Decimal("100.00")

        # Convert to Decimal if needed
        if not isinstance(total_amount, Decimal):
            try:
                total_amount = Decimal(str(total_amount))
            except:
                print(f"❌ ERROR: Cannot convert {total_amount} to Decimal, using fallback")
                total_amount = Decimal("100.00")

        print(f"🔍 Setting total_amount to: {total_amount}")
        self.total_amount = total_amount
        
        # Calculate 50/50 split with proper rounding
        half_amount = total_amount / 2
        self.deposit_amount = half_amount.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        self.final_amount = total_amount - self.deposit_amount

        print(f"🔍 Before save - total: {self.total_amount}, deposit: {self.deposit_amount}, final: {self.final_amount}")
        
        try:
            self.save()
            print(f"✅ PaymentSplit saved successfully")
            # Verify the save worked
            self.refresh_from_db()
            print(f"🔍 After save - total: {self.total_amount}, deposit: {self.deposit_amount}, final: {self.final_amount}")
        except Exception as e:
            print(f"❌ ERROR saving PaymentSplit: {e}")
            raise e
        
        return self
    
    @classmethod
    def create_split_with_amount(cls, booking, total_amount):
        """Create a payment split with a specific total amount (from frontend summary)"""
        print(f"🔍 Creating PaymentSplit for booking {booking.id} with manual total: {total_amount}")
        print(f"🔍 Manual total type: {type(total_amount)}")
        
        # Ensure total_amount is valid
        if not total_amount or total_amount <= 0:
            print(f"❌ ERROR: Invalid manual total_amount {total_amount}, using fallback")
            total_amount = Decimal("100.00")
        
        # Convert to Decimal if it's not already
        if not isinstance(total_amount, Decimal):
            try:
                total_amount = Decimal(str(total_amount))
            except:
                print(f"❌ ERROR: Cannot convert {total_amount} to Decimal, using fallback")
                total_amount = Decimal("100.00")
        
        print(f"🔍 Final total_amount for PaymentSplit: {total_amount}")
        
        try:
            # Calculate amounts directly
            deposit_amount = total_amount / 2
            final_amount = total_amount / 2
            
            # Handle odd cents by adding to deposit
            if total_amount % 2 != 0:
                deposit_amount += Decimal('0.01')
            
            print(f"🔍 Creating PaymentSplit with calculated amounts:")
            print(f"🔍 total_amount: {total_amount}")
            print(f"🔍 deposit_amount: {deposit_amount}")
            print(f"🔍 final_amount: {final_amount}")
            
            # Create with all amounts at once
            payment_split = cls.objects.create(
                booking=booking,
                total_amount=total_amount,
                deposit_amount=deposit_amount,
                final_amount=final_amount
            )
            print(f"✅ PaymentSplit created successfully with ID: {payment_split.id}")
            return payment_split
            
        except Exception as e:
            print(f"❌ ERROR creating PaymentSplit: {e}")
            # Try with fallback amount using the old method
            payment_split = cls.objects.create(booking=booking)
            return payment_split.create_split(Decimal("100.00"))

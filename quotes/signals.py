from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Booking
from .stripe_views import create_final_payment_link, send_final_payment_email
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Booking)
def handle_booking_status_change(sender, instance, created, **kwargs):
    """Handle booking status changes, particularly when status changes to 'completed'"""
    
    # Skip if this is a new booking (created=True)
    if created:
        return
    
    # Check if status changed to 'completed'
    if instance.status == 'completed':
        logger.info(f"Booking {instance.id} status changed to 'completed'")
        
        # Check if this is a partial payment booking that needs final payment
        try:
            split = instance.get_payment_split()
            
            # Only create payment link if deposit is paid but final payment is not
            if split.deposit_paid and not split.final_paid:
                logger.info(f"Creating final payment link for booking {instance.id}")
                
                # Create payment link
                payment_link_result = create_final_payment_link(instance)
                
                if payment_link_result and payment_link_result.get('payment_link_url'):
                    # Send email with payment link
                    email_sent = send_final_payment_email(
                        instance, 
                        payment_link_result['payment_link_url']
                    )
                    
                    if email_sent:
                        logger.info(f"Final payment email sent for booking {instance.id}")
                    else:
                        logger.error(f"Failed to send final payment email for booking {instance.id}")
                else:
                    logger.error(f"Failed to create payment link for booking {instance.id}")
            else:
                logger.info(f"Booking {instance.id} does not need final payment link (deposit_paid: {split.deposit_paid}, final_paid: {split.final_paid})")
                
        except Exception as e:
            logger.error(f"Error handling booking status change for booking {instance.id}: {e}")


@receiver(post_save, sender=Booking)
def log_booking_status_changes(sender, instance, created, **kwargs):
    """Log all booking status changes for debugging"""
    if not created:
        logger.info(f"Booking {instance.id} status: {instance.status}")

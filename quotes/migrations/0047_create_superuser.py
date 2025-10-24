# Generated manually for Railway deployment

from django.db import migrations
from django.contrib.auth import get_user_model
import os

def create_superuser(apps, schema_editor):
    """Create a superuser if one doesn't exist"""
    User = get_user_model()
    
    # Only create if no superuser exists
    if not User.objects.filter(is_superuser=True).exists():
        # Get credentials from environment variables or use defaults
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@thecleanhandy.com')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        
        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f"✅ Superuser created: {username}")
        except Exception as e:
            print(f"❌ Failed to create superuser: {e}")

def reverse_create_superuser(apps, schema_editor):
    """Remove the superuser (optional)"""
    User = get_user_model()
    username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
    try:
        User.objects.filter(username=username, is_superuser=True).delete()
        print(f"🗑️  Superuser removed: {username}")
    except Exception as e:
        print(f"❌ Failed to remove superuser: {e}")

class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0046_paymentsplit_final_payment_link_created_at_and_more'),
    ]

    operations = [
        migrations.RunPython(create_superuser, reverse_create_superuser),
    ]

# Generated by Django 5.1.7 on 2025-04-14 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0025_booking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='email',
            field=models.EmailField(max_length=100),
        ),
    ]

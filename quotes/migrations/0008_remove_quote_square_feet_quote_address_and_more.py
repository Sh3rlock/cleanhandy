# Generated by Django 5.1.7 on 2025-03-26 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0007_cleaningextra_quote_home_type_quote_is_recurring_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quote',
            name='square_feet',
        ),
        migrations.AddField(
            model_name='quote',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='quote',
            name='apartment',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='quote',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='quote',
            name='recurrence_pattern',
            field=models.CharField(choices=[('one_time', 'One Time'), ('weekly', 'Weekly'), ('biweekly', 'Biweekly'), ('monthly', 'Monthly')], default='one_time', max_length=20),
        ),
        migrations.AddField(
            model_name='quote',
            name='square_feet_range',
            field=models.CharField(blank=True, choices=[('under_1000', 'Under 1000 sq. ft'), ('1000_1500', '1001–1500 sq. ft'), ('1500_2000', '1500–2000 sq. ft'), ('custom', 'Custom Cleaning'), ('post_renovation', 'Post Renovation Cleaning')], max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='quote',
            name='state',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='service',
            name='base_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=8),
        ),
    ]

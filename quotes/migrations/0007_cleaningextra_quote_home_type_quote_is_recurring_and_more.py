# Generated by Django 5.1.7 on 2025-03-25 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0006_quote_approval_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='CleaningExtra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('price', models.DecimalField(decimal_places=2, max_digits=6)),
            ],
        ),
        migrations.AddField(
            model_name='quote',
            name='home_type',
            field=models.CharField(blank=True, choices=[('apartment', 'Apartment'), ('house', 'House'), ('studio', 'Studio'), ('other', 'Other')], max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='quote',
            name='is_recurring',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quote',
            name='num_bathrooms',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='quote',
            name='num_bedrooms',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='quote',
            name='square_feet',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='quote',
            name='extras',
            field=models.ManyToManyField(blank=True, to='quotes.cleaningextra'),
        ),
    ]

# Generated by Django 5.1.7 on 2025-04-09 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0018_newslettersubscriber'),
    ]

    operations = [
        migrations.AddField(
            model_name='cleaningextra',
            name='extra_minutes',
            field=models.PositiveIntegerField(default=0, help_text='Add time in minutes (e.g. 30, 60)'),
        ),
    ]

# Generated by Django 5.1.7 on 2025-03-26 19:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0012_quote_pdf_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quote',
            name='is_recurring',
        ),
    ]

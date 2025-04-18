# Generated by Django 5.1.7 on 2025-03-26 16:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0010_remove_squarefeetoption_estimated_sqft_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quote',
            name='home_types',
        ),
        migrations.RemoveField(
            model_name='quote',
            name='square_feet_options',
        ),
        migrations.AddField(
            model_name='quote',
            name='home_types',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='quotes.hometype'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='quote',
            name='square_feet_options',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='quotes.squarefeetoption'),
            preserve_default=False,
        ),
    ]

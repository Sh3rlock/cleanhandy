# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0058_alter_officequote_job_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='homecleaningquoterequest',
            name='payment_status',
            field=models.CharField(
                choices=[('unpaid', 'Unpaid'), ('paid', 'Paid')],
                default='unpaid',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='officequote',
            name='payment_status',
            field=models.CharField(
                choices=[('unpaid', 'Unpaid'), ('paid', 'Paid')],
                default='unpaid',
                max_length=20
            ),
        ),
    ]

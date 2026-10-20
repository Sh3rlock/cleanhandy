from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0004_quote_parking_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="quoterequest",
            name="email_note",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="quoterequest",
            name="quote_email_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

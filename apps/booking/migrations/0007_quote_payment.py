from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0006_property_area_choices"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuotePayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("deposit", "Deposit (50%)"), ("full", "Full amount")], max_length=16)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("stripe_payment_link_id", models.CharField(blank=True, max_length=255)),
                ("stripe_payment_link_url", models.URLField(blank=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid")], default="pending", max_length=16)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "quote",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="booking.quoterequest"),
                ),
            ],
            options={"ordering": ["kind"]},
        ),
        migrations.AddConstraint(
            model_name="quotepayment",
            constraint=models.UniqueConstraint(fields=("quote", "kind"), name="uniq_quote_payment_kind"),
        ),
    ]

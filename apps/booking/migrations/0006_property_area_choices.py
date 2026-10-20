from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0005_quote_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="property",
            name="borough",
            field=models.CharField(
                choices=[
                    ("manhattan", "Manhattan"),
                    ("brooklyn", "Brooklyn"),
                    ("queens", "Queens"),
                    ("bronx", "Bronx"),
                    ("staten_island", "Staten Island"),
                    ("long_island", "Long Island"),
                    ("new_jersey", "New Jersey"),
                ],
                max_length=32,
            ),
        ),
    ]

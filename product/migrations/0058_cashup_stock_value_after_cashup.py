# Generated by Django 4.2.6 on 2024-03-26 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0057_cashup_stock_value_before_cashup'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashup',
            name='stock_value_after_cashup',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]

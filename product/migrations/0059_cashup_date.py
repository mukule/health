# Generated by Django 4.2.6 on 2024-03-26 11:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0058_cashup_stock_value_after_cashup'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashup',
            name='date',
            field=models.DateField(default=datetime.date(2024, 3, 26)),
        ),
    ]

# Generated by Django 4.2.5 on 2023-09-13 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0006_alter_cartitem_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='total_cost',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]

# Generated by Django 4.2.5 on 2023-09-13 20:29

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_sale_saleitem_sale_products_sold_sale_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='sale_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]

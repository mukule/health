# Generated by Django 4.2.5 on 2023-11-25 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0042_remove_dispatch_products_remove_dispatch_quantities_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dispatchedproduct',
            name='product_quantity',
            field=models.PositiveIntegerField(null=True),
        ),
    ]

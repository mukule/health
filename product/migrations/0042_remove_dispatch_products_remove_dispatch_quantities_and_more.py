# Generated by Django 4.2.5 on 2023-11-25 11:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0041_dispatch_dispatchedproduct_dispatch_quantities'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dispatch',
            name='products',
        ),
        migrations.RemoveField(
            model_name='dispatch',
            name='quantities',
        ),
        migrations.RemoveField(
            model_name='dispatchedproduct',
            name='product',
        ),
        migrations.RemoveField(
            model_name='dispatchedproduct',
            name='product_quantity',
        ),
        migrations.AddField(
            model_name='dispatch',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='product.product'),
        ),
        migrations.AddField(
            model_name='dispatch',
            name='product_quantity',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
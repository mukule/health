# Generated by Django 4.2.5 on 2023-10-08 12:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0027_cart_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='buyer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='product.buyer'),
        ),
    ]
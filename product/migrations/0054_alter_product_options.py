# Generated by Django 4.2.6 on 2024-03-24 09:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0053_remove_receiving_products_receiving_product'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['title']},
        ),
    ]

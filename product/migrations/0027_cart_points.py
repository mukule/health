# Generated by Django 4.2.5 on 2023-10-08 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0026_sale_buyer'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='points',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
# Generated by Django 4.2.5 on 2023-09-09 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='access_level',
            field=models.CharField(blank=True, choices=[('cashier', 'Cashier'), ('manager', 'Manager'), ('admin', 'Admin')], max_length=20, null=True),
        ),
    ]

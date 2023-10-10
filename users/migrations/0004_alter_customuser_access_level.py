# Generated by Django 4.2.5 on 2023-10-10 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_customuser_date_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='access_level',
            field=models.IntegerField(blank=True, choices=[(1, 'Admin'), (2, 'Manager'), (3, 'Cashier')], null=True),
        ),
    ]

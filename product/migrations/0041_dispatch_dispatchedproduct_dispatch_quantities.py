# Generated by Django 4.2.5 on 2023-11-25 11:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0040_receivedproduct_total_amount'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dispatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destination', models.CharField(max_length=255)),
                ('reason', models.TextField()),
                ('dispatch_date', models.DateTimeField(auto_now_add=True)),
                ('dispatcher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('products', models.ManyToManyField(to='product.product')),
            ],
        ),
        migrations.CreateModel(
            name='DispatchedProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_quantity', models.PositiveIntegerField()),
                ('dispatch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.dispatch')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.product')),
            ],
        ),
        migrations.AddField(
            model_name='dispatch',
            name='quantities',
            field=models.ManyToManyField(related_name='dispatched_quantities', through='product.DispatchedProduct', to='product.product'),
        ),
    ]

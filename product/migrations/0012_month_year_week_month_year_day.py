# Generated by Django 4.2.5 on 2023-09-22 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0011_alter_sale_total_amount'),
    ]

    operations = [
        migrations.CreateModel(
            name='Month',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Year',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Week',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_number', models.PositiveIntegerField()),
                ('month', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.month')),
            ],
        ),
        migrations.AddField(
            model_name='month',
            name='year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.year'),
        ),
        migrations.CreateModel(
            name='Day',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.CharField(max_length=10)),
                ('sales_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('sales', models.ManyToManyField(to='product.sale')),
                ('week', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.week')),
            ],
        ),
    ]

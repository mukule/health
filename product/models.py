from django.db import models
from django.contrib.auth.models import User
from users.models import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import *

class Product(models.Model):
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True, default='default/user.jpg')
    category = models.ForeignKey('Category', on_delete=models.CASCADE)  # Change on_delete to CASCADE
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)  # Use the custom user model
    products = models.ManyToManyField(Product, through='CartItem')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.user:
            self.user_name = self.user.username

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=True)

class Sale(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    products_sold = models.ManyToManyField(Product, through='SaleItem')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Updated default value
    sale_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Sale by {self.user.username}"
    
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_sold = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.product.title 

class Year(models.Model):
    year = models.PositiveIntegerField(unique=True)
    sales_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return str(self.year)

class Month(models.Model):
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    month = models.PositiveIntegerField()
    sales_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    def __str__(self):
        return f"{self.month} {self.year}"

class Week(models.Model):
    month = models.ForeignKey(Month, on_delete=models.CASCADE)
    week_number = models.PositiveIntegerField()
    sales_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Week {self.week_number}, {self.month}"
    

class Day(models.Model):
    week = models.ForeignKey(Week, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=10)
    sales_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    sales = models.ManyToManyField(Sale)
    date = models.DateField(null=True)

    def __str__(self):
        return self.day_of_week


class StockTake(models.Model):
    stock_date = models.DateField(default=timezone.now)
    products = models.ManyToManyField(Product, through='StockTakeItem')
    stock_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)
    stock_balanced = models.BooleanField(default=False)  # Add this field

    def __str__(self):
        return f"Stock Take on {self.stock_date} by {self.user}"


    
class StockTakeItem(models.Model):
    stock_take = models.ForeignKey(StockTake, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_counted = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.product}"

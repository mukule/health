from django.db import models
from django.contrib.auth.models import User
from users.models import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import *

from django.db import models
from django.db.models import Q, UniqueConstraint


class Product(models.Model):
    product_code = models.CharField(max_length=50, unique=True, null=True)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(
        upload_to='products/', null=True, blank=True, default='default/user.jpg')
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    quantity = models.IntegerField(default=0)
    units = models.CharField(max_length=50, null=True)
    brand = models.CharField(max_length=50, null=True)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['product_code'],
                condition=Q(product_code__isnull=False),
                name='unique_product_code'
            )
        ]

class Promotion(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='promotion')
    initial_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    current_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Promotion for {self.product.title}"

    class Meta:
        verbose_name = 'Promotion'
        verbose_name_plural = 'Promotions'


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    products_supplied = models.ManyToManyField(
        Category, related_name='suppliers', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Buyer(models.Model):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name_plural = "Buyers"


class Cart(models.Model):
    # Use the custom user model
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='CartItem')
    total_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    add_vat = models.BooleanField(default=False)  # Add this field
    total_payable = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    buyer = models.ForeignKey(
        Buyer, on_delete=models.SET_NULL, null=True, blank=True)  # Add buyer field
    points = models.IntegerField(null=True, blank=True)
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)

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
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_paid = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    sale_date = models.DateTimeField(default=timezone.now)
    buyer = models.ForeignKey(
        Buyer, on_delete=models.SET_NULL, null=True, blank=True)  # Add buyer field

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
    sales_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return str(self.year)


class Month(models.Model):
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    month = models.PositiveIntegerField()
    sales_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.month} {self.year}"


class Week(models.Model):
    month = models.ForeignKey(Month, on_delete=models.CASCADE)
    week_number = models.PositiveIntegerField()
    sales_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Week {self.week_number}, {self.month}"


class Day(models.Model):
    week = models.ForeignKey(Week, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=10)
    sales_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    sales = models.ManyToManyField(Sale)
    date = models.DateField(null=True)

    def __str__(self):
        return self.day_of_week


class StockTake(models.Model):
    stock_date = models.DateField(default=timezone.now)
    products = models.ManyToManyField(Product, through='StockTakeItem')
    stock_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    # New field for the difference
    difference = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)
    stock_balanced = models.BooleanField(default=False)

    def __str__(self):
        return f"Stock Take on {self.stock_date} by {self.user}"


class StockTakeItem(models.Model):
    stock_take = models.ForeignKey(StockTake, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_counted = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product}"


class PaymentMethod(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount_paid} on {self.payment_date}"


class Receiving(models.Model):
    receiver = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    received_date = models.DateTimeField(auto_now_add=True)
    products = models.ManyToManyField(Product, through='ReceivedProduct')

    def __str__(self):
        return f"Receiving #{self.id} - {self.received_date}"


class ReceivedProduct(models.Model):
    receiving = models.ForeignKey(Receiving, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate total_amount before saving
        self.total_amount = self.product_quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.title} - {self.product_quantity} units"

    class Meta:
        unique_together = ('receiving', 'product')


class Supply(models.Model):
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.supplier} - {self.product} - Ksh.{self.total_amount} {'(Paid)' if self.paid else '(Unpaid)'}"


class Dispatch(models.Model):
    destination = models.CharField(max_length=255)
    reason = models.TextField()
    dispatcher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    dispatch_date = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    product_quantity = models.PositiveIntegerField(null=True)

    def __str__(self):
        return f"Dispatch #{self.id} - {self.dispatch_date}"


class DispatchedProduct(models.Model):
    dispatch = models.ForeignKey(Dispatch, on_delete=models.CASCADE)
    product_quantity = models.PositiveIntegerField(null=True)

    def __str__(self):
        return f"{self.dispatch.product.title} - {self.product_quantity} units"

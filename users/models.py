from django.db import models
from django.contrib.auth.models import AbstractUser
import os

# Create your models here.

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    ACCESS_LEVEL_CHOICES = (
        ('cashier', 'Cashier'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
    )

    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.username
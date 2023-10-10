from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    ACCESS_LEVEL_CHOICES = (
        (1, 'Admin'),
        (2, 'Manager'),
        (3, 'Cashier'),
    )

    access_level = models.IntegerField(
        choices=ACCESS_LEVEL_CHOICES,
        null=True,
        blank=True
    )
    
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.username

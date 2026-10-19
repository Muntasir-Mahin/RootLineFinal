from datetime import date
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )

    seller_requested = models.BooleanField(default=False)
    seller_requested_at = models.DateTimeField(null=True, blank=True)
    seller_approved = models.BooleanField(default=False)

    @property
    def age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None

    def __str__(self):
        return self.username
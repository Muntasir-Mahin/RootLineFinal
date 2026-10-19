from datetime import date
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_resized import ResizedImageField


class User(AbstractUser):
    age = models.PositiveIntegerField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = ResizedImageField(
        size=[300, 300],
        crop=['middle', 'center'],
        quality=85,
        upload_to='profile_pics/',
        blank=True,
        null=True,
        force_format='JPEG',
    )

    seller_requested = models.BooleanField(default=False)
    seller_approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.birth_date:
            today = date.today()
            self.age = today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
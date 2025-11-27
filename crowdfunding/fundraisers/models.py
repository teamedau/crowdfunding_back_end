from django.conf import settings
from django.db import models
import secrets

class Fundraiser(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    goal = models.PositiveIntegerField()
    image = models.URLField(blank=True)
    is_open = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_fundraisers'
    )
    supporters = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='supported_fundraisers'
    )
    invite_code = models.CharField(max_length=32, blank=True, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = secrets.token_urlsafe(8)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Pledge(models.Model):
    PLEDGE_TYPE = (
        ('time', 'Time'),
        ('words', 'Words'),
    )
    fundraiser = models.ForeignKey(
        'Fundraiser',
        on_delete=models.CASCADE,
        related_name='pledges'
    ) 
    supporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pledges'
    )
    type = models.CharField(max_length=10, choices=PLEDGE_TYPE, default='time')
    amount = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        supporter = getattr(self, 'supporter', None)
        return f"Pledge {self.pk} by {supporter}" if supporter else f"Pledge {self.pk}"
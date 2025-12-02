from django.conf import settings
from django.db import models


class Fundraiser(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    goal_text = models.CharField(max_length=255, blank=True)
    goal_number = models.PositiveIntegerField(default=1)
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

    def __str__(self):
        return self.title
    
    @property
    def progress(self):
        total_pledges = self.pledges.count()
        if self.goal_number:
            return min(100, int((total_pledges / self.goal_number) * 100))
        return 0

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

    # if chooses time as pledge type
    hours = models.PositiveIntegerField(null=True, blank=True)

    # if chooses words as pledge type
    action = models.CharField(max_length=100, blank=True)

    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pledge {self.pk} ({self.type})"
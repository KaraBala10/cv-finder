from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    verification_code = models.CharField(max_length=8, blank=True, null=True)
    failed_attempts = models.IntegerField(default=0)  # Track failed attempts
    verification_code_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                name="unique_email_active",
                condition=Q(is_active=True),
            )
        ]

    def clean(self):
        """
        Custom validation to ensure only one active user with the same email exists.
        """
        if self.is_active:
            if (
                CustomUser.objects.filter(email=self.email, is_active=True)
                .exclude(id=self.id)
                .exists()
            ):
                raise ValidationError(
                    f"An active user with the email {self.email} already exists."
                )

    def __str__(self):
        return self.username

    def is_verification_code_expired(self):
        if self.verification_code_sent_at:
            return timezone.now() > self.verification_code_sent_at + timedelta(
                minutes=10
            )
        return False


@receiver(pre_save, sender=CustomUser)
def deactivate_other_users_with_same_email(sender, instance, **kwargs):
    """
    Deactivates other users with the same email when a user is being activated.
    """
    if instance.is_active:
        CustomUser.objects.filter(email=instance.email, is_active=False).delete()


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100, blank=True)
    governorate = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="resumes/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

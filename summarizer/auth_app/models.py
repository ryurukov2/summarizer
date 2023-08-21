from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from summarizer.auth_app.managers import AccountsManager


# Create your models here.
class Account(AbstractBaseUser, PermissionsMixin):
    google_account_id = models.CharField(max_length=255, unique=True, null=False)
    email = models.EmailField(max_length=255, unique=True, null=True)
    daily_usage = models.IntegerField(default=0)
    usage_reset_date = models.DateTimeField()
    is_subscribed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = AccountsManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['google_account_id']

    def __str__(self):
        return str(self.id)

    def get_full_name(self):
        # Implement if needed
        return self.email

    def get_short_name(self):
        # Implement if needed
        return self.email

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def update_usage_reset_date(self):
        self.usage_reset_date = timezone.now()
        self.save()

    def reset_usage(self):
        self.daily_usage = 0
        self.update_usage_reset_date()

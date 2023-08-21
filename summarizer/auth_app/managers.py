from django.contrib.auth.base_user import BaseUserManager


class AccountsManager(BaseUserManager):
    def create_user(self, email, google_account_id, auth_provider, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, google_account_id=google_account_id, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, google_account_id, auth_provider, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, google_account_id, auth_provider, password, **extra_fields)
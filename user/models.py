from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class user_data(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    user_otp = models.CharField(default=0, max_length=100)
    usr_verify = models.CharField(default=0, max_length=100)
    expire_otp = models.CharField(default=0, max_length=100)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


# ✅ Add this new model at the bottom (to store location, device info)
class UserDeviceInfo(models.Model):
    user = models.ForeignKey(user_data, on_delete=models.CASCADE, related_name='devices',db_column="user_id")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    isp = models.CharField(max_length=200, null=True, blank=True)
    system = models.CharField(max_length=100, null=True, blank=True)
    machine = models.CharField(max_length=100, null=True, blank=True)
    device_name = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"

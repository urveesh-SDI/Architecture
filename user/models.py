from django.db import models

# Create your models here.
# models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models



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
    user_otp = models.CharField(default=0,max_length=100)
    is_verified = models.CharField(default=0,max_length=100)
    expire_otp = models.CharField(default=0,max_length=100)
    ip_address = models.CharField(max_length=100, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'   # email primary login field
    REQUIRED_FIELDS = []       # no other required fields

    def __str__(self):
        return self.email
    
    
class UserDeviceInfo(models.Model):
    user = models.OneToOneField(user_data,on_delete=models.CASCADE,related_name="devices")
#    user = models.ForeignKey(user_data, on_delete=models.CASCADE, related_name="devices")
    ip_address = models.CharField(max_length=45, blank=True, null=True)   
    location = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    isp = models.CharField(max_length=200, blank=True, null=True)
    system = models.CharField(max_length=100, blank=True, null=True)
    machine = models.CharField(max_length=100, blank=True, null=True)
    device_name = models.CharField(max_length=200, blank=True, null=True)
    raw_info = models.JSONField(blank=True, null=True)   # stores the full dict
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.ip_address} ({self.created_at:%Y-%m-%d %H:%M})"

from django.contrib import admin            # this  code is added to convert the user name into email.   # becouse there is defoult username is saved.
# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import user_data,UserDeviceInfo

@admin.register(user_data)
class CustomUserAdmin(UserAdmin):
    model = user_data
    list_display = ('email', 'is_staff', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
admin.site.register(UserDeviceInfo)
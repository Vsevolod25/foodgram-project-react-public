from django.contrib import admin

from .models import User, Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'is_active', 'last_login', 'date_joined'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email', 'is_staff', 'is_active')
    empty_value_display = '-пусто-'


admin.site.register(Subscription)

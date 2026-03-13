from django.contrib import admin

from .models import UserActivities, Users, Subscription, BalanceHistory, Banner



@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_banned', 'created_at')
    list_filter = ('is_banned',)
    search_fields = ('name', 'username', 'phone')
    
admin.site.register(UserActivities)
admin.site.register(Subscription)
admin.site.register(Banner)
admin.site.register(BalanceHistory)

from django.contrib import admin
from .models import SystemSettings, SystemLog, AdmissionGuide

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('university_name', 'college_name', 'header_color')
    
    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_action_display', 'timestamp', 'details')
    list_filter = ('action', 'timestamp')
    search_fields = ('details', 'user__username')
    readonly_fields = ('user', 'action', 'details', 'timestamp')

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(AdmissionGuide)
class AdmissionGuideAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at')
    search_fields = ('title', 'content')

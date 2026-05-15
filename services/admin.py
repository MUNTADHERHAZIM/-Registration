from django.contrib import admin
from .models import StudentRequest, FAQ


@admin.register(StudentRequest)
class StudentRequestAdmin(admin.ModelAdmin):
    list_display = [
        'tracking_number', 'student_name', 'request_type',
        'status', 'phone', 'created_at'
    ]
    list_filter = ['status', 'request_type', 'created_at']
    search_fields = [
        'tracking_number', 'student_name',
        'student_id_number', 'national_id', 'phone'
    ]
    readonly_fields = ['tracking_number', 'created_at', 'updated_at']
    list_editable = ['status']
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('معلومات التتبع', {
            'fields': ('tracking_number', 'request_type', 'status')
        }),
        ('بيانات الطالب', {
            'fields': (
                'student_name', 'student_id_number', 'national_id',
                'phone', 'email', 'department', 'level'
            )
        }),
        ('تفاصيل الطلب', {
            'fields': ('description', 'attachment', 'webcam_photo')
        }),
        ('المراجعة', {
            'fields': ('admin_notes', 'reviewed_by')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    search_fields = ('question', 'answer')
    list_filter = ('is_active',)

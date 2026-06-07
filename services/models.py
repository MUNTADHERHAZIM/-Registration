from django.db import models
from django.utils import timezone
from students.models import Department
import uuid
import datetime


class StudentRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('confirmation', 'تأييد دراسي'),
        ('graduation_doc', 'وثيقة تخرج'),
        ('transcript', 'كشف درجات'),
        ('certificate', 'إفادة طالب'),
        ('postpone', 'طلب تأجيل'),
        ('withdrawal', 'طلب انسحاب'),
        ('transfer', 'طلب نقل'),
        ('re_enrollment', 'طلب إعادة قيد'),
        ('excuse', 'طلب عذر'),
        ('other', 'أخرى'),
    ]

    STATUS_CHOICES = [
        ('new', 'جديد'),
        ('reviewing', 'قيد المراجعة'),
        ('approved', 'مقبول'),
        ('rejected', 'مرفوض'),
        ('completed', 'مكتمل'),
    ]

    LEVEL_CHOICES = [
        ('1', 'المرحلة الأولى'),
        ('2', 'المرحلة الثانية'),
        ('3', 'المرحلة الثالثة'),
        ('4', 'المرحلة الرابعة'),
        ('5', 'المرحلة الخامسة'),
    ]

    # Tracking
    tracking_number = models.CharField(
        max_length=20, unique=True, verbose_name='رقم التتبع', editable=False
    )

    # Request info
    request_type = models.CharField(
        max_length=20, choices=REQUEST_TYPE_CHOICES, verbose_name='نوع الطلب'
    )

    # Student info
    student_name = models.CharField(max_length=300, verbose_name='الاسم الرباعي')
    student_id_number = models.CharField(
        max_length=20, verbose_name='الرقم الجامعي', blank=True
    )
    national_id = models.CharField(
        max_length=20, verbose_name='رقم الهوية الوطنية', blank=True
    )
    phone = models.CharField(max_length=20, verbose_name='رقم الهاتف')
    email = models.EmailField(verbose_name='البريد الإلكتروني', blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='requests', verbose_name='القسم', null=True
    )
    level = models.CharField(
        max_length=1, choices=LEVEL_CHOICES, verbose_name='المرحلة', blank=True
    )

    # Details
    description = models.TextField(verbose_name='تفاصيل الطلب', blank=True)
    attachment = models.FileField(
        upload_to='service_requests/attachments/',
        verbose_name='ملف مرفق',
        blank=True, null=True
    )
    webcam_photo = models.ImageField(
        upload_to='service_requests/webcam/',
        verbose_name='صورة من الكاميرا',
        blank=True, null=True
    )

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='new', verbose_name='حالة الطلب'
    )
    assigned_to = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_requests', verbose_name='المكلف بالمهمة'
    )
    admin_notes = models.TextField(verbose_name='ملاحظات الإدارة', blank=True)
    reviewed_by = models.CharField(
        max_length=200, verbose_name='تمت المراجعة بواسطة', blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التقديم')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'طلب طالب'
        verbose_name_plural = 'طلبات الطلاب'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tracking_number} - {self.student_name} ({self.get_request_type_display()})"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            year = timezone.now().year
            last = StudentRequest.objects.filter(
                tracking_number__startswith=f'REQ-{year}'
            ).order_by('-tracking_number').first()
            if last:
                try:
                    num = int(last.tracking_number.split('-')[-1]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.tracking_number = f"REQ-{year}-{num:04d}"
        super().save(*args, **kwargs)

    def get_status_color(self):
        colors = {
            'new': 'info',
            'reviewing': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'completed': 'primary',
        }
        return colors.get(self.status, 'secondary')

    def get_status_icon(self):
        icons = {
            'new': 'fa-inbox',
            'reviewing': 'fa-hourglass-half',
            'approved': 'fa-check-circle',
            'rejected': 'fa-times-circle',
            'completed': 'fa-flag-checkered',
        }
        return icons.get(self.status, 'fa-question')


class FAQ(models.Model):
    question = models.CharField(max_length=500, verbose_name='السؤال')
    answer = models.TextField(verbose_name='الإجابة')
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سؤال شائع'
        verbose_name_plural = 'الأسئلة الشائعة'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.question

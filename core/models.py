from django.db import models

class SystemSettings(models.Model):
    university_name = models.CharField(max_length=200, verbose_name="اسم الجامعة/الكلية", default="الجامعة التقنية")
    college_name = models.CharField(max_length=200, verbose_name="اسم الكلية", blank=True)
    logo = models.ImageField(upload_to='system/', verbose_name="شعار الجامعة", blank=True, null=True)
    header_color = models.CharField(max_length=20, default="#1a237e", verbose_name="لون الهوية الأساسي")
    contact_email = models.EmailField(blank=True, verbose_name="بريد التواصل")
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, verbose_name="العنوان")
    
    class Meta:
        verbose_name = "إعدادات النظام"
        verbose_name_plural = "إعدادات النظام"

    def __str__(self):
        return "إعدادات النظام"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SystemSettings.objects.exists():
            return
        super().save(*args, **kwargs)

class SystemLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('create', 'إضافة'),
        ('update', 'تعديل'),
        ('delete', 'حذف'),
        ('other', 'أخرى'),
    ]
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name="المستخدم")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="نوع الإجراء")
    details = models.TextField(verbose_name="التفاصيل")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="الوقت")

    class Meta:
        verbose_name = "سجل النظام"
        verbose_name_plural = "سجل النظام"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.timestamp}"

class AdmissionGuide(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان الدليل")
    content = models.TextField(verbose_name="تعليمات القبول", help_text="يمكنك استخدام HTML لتنسيق النص")
    pdf_file = models.FileField(upload_to='guides/', blank=True, null=True, verbose_name="ملف الدليل (PDF)")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ آخر تحديث")

    class Meta:
        verbose_name = "دليل وضوابط القبول"
        verbose_name_plural = "أدلة وضوابط القبول"

    def __str__(self):
        return self.title

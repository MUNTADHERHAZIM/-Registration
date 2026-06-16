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


class DynamicChoice(models.Model):
    CATEGORY_CHOICES = [
        ('governorate', 'المحافظات'),
        ('religion', 'الأديان'),
        ('health_status', 'الحالة الصحية'),
        ('branch', 'الفروع الدراسية'),
        ('origin_status', 'حالة الطالب أصيل/وافد'),
        ('admission_channel', 'قنوات القبول'),
        ('marital_status', 'الحالة الزوجية'),
        ('gender', 'الجنس'),
        ('level', 'المراحل الدراسية'),
        ('study_type', 'نوع الدراسة'),
        ('status', 'حالة الطالب (نشط/موقوف/إلخ)'),
        ('citizenship', 'الجنسية'),
        ('birth_place', 'محل الولادة'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name="الفئة")
    value = models.CharField(max_length=100, verbose_name="القيمة (بالقاعدة)")
    display_name = models.CharField(max_length=150, verbose_name="الاسم المعروض")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    class Meta:
        verbose_name = "خيار ديناميكي"
        verbose_name_plural = "الخيارات الديناميكية"
        unique_together = ['category', 'value']
        ordering = ['category', 'display_name']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.display_name}"


def get_dynamic_choices(category, default_choices):
    try:
        db_choices = list(DynamicChoice.objects.filter(category=category))
        if not db_choices:
            return default_choices
            
        db_map = {choice.value: choice for choice in db_choices}
        final_choices = []
        
        for val, display in default_choices:
            if val == '':
                final_choices.append((val, display))
                continue
                
            if val in db_map:
                choice = db_map[val]
                if choice.is_active:
                    final_choices.append((val, choice.display_name))
            else:
                final_choices.append((val, display))
                
        default_vals = {c[0] for c in default_choices}
        for choice in db_choices:
            if choice.value not in default_vals and choice.is_active:
                final_choices.append((choice.value, choice.display_name))
                
        return final_choices
    except Exception:
        pass
    return default_choices


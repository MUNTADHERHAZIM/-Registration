from django.db import models
from django.utils import timezone
import datetime


class Department(models.Model):
    name = models.CharField(max_length=200, verbose_name='اسم القسم')
    code = models.CharField(max_length=20, unique=True, verbose_name='رمز القسم')
    description = models.TextField(blank=True, null=True, verbose_name='الوصف')
    head_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='رئيس القسم')
    email = models.EmailField(blank=True, null=True, verbose_name='البريد الإلكتروني')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='الهاتف')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'قسم'
        verbose_name_plural = 'الأقسام'
        ordering = ['name']

    def __str__(self):
        return self.name

    def student_count(self):
        return self.students.filter(status='active').count()


class AcademicYear(models.Model):
    year = models.CharField(max_length=20, unique=True, verbose_name='السنة الدراسية')
    is_active = models.BooleanField(default=False, verbose_name='نشطة')
    start_date = models.DateField(verbose_name='تاريخ البدء')
    end_date = models.DateField(verbose_name='تاريخ الانتهاء')

    class Meta:
        verbose_name = 'سنة دراسية'
        verbose_name_plural = 'السنوات الدراسية'
        ordering = ['-year']

    def __str__(self):
        return self.year

    def save(self, *args, **kwargs):
        if self.is_active:
            AcademicYear.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Semester(models.Model):
    SEMESTER_CHOICES = [
        ('first', 'الفصل الأول'),
        ('second', 'الفصل الثاني'),
        ('summer', 'الدورة الصيفية'),
    ]
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters', verbose_name='السنة الدراسية')
    name = models.CharField(max_length=20, choices=SEMESTER_CHOICES, verbose_name='الفصل')
    start_date = models.DateField(verbose_name='تاريخ البدء')
    end_date = models.DateField(verbose_name='تاريخ الانتهاء')
    is_active = models.BooleanField(default=False, verbose_name='نشط')
    registration_open = models.BooleanField(default=False, verbose_name='التسجيل مفتوح')

    class Meta:
        verbose_name = 'فصل دراسي'
        verbose_name_plural = 'الفصول الدراسية'
        unique_together = ['academic_year', 'name']
        ordering = ['-academic_year__year', 'name']

    def __str__(self):
        return f"{self.get_name_display()} - {self.academic_year.year}"

    def save(self, *args, **kwargs):
        if self.is_active:
            Semester.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


def student_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'students/{instance.student_id}.{ext}'


class Student(models.Model):
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('initial', 'تقديم أولي'),
        ('suspended', 'موقوف'),
        ('graduated', 'متخرج'),
        ('withdrawn', 'منسحب'),
        ('transferred', 'محول'),
    ]
    GENDER_CHOICES = [
        ('male', 'ذكر'),
        ('female', 'أنثى'),
    ]
    LEVEL_CHOICES = [
        ('1', 'المرحلة الأولى'),
        ('2', 'المرحلة الثانية'),
        ('3', 'المرحلة الثالثة'),
        ('4', 'المرحلة الرابعة'),
        ('5', 'المرحلة الخامسة'),
    ]
    STUDY_TYPE_CHOICES = [
        ('morning', 'صباحي'),
        ('evening', 'مسائي'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('single', 'أعزب/عزباء'),
        ('married', 'متزوج/متزوجة'),
        ('divorced', 'مطلق/مطلقة'),
        ('widowed', 'أرمل/أرملة'),
    ]
    GOVERNORATE_CHOICES = [
        ('بغداد', 'بغداد'),
        ('البصرة', 'البصرة'),
        ('نينوى', 'نينوى'),
        ('أربيل', 'أربيل'),
        ('النجف الأشرف', 'النجف الأشرف'),
        ('كربلاء المقدسة', 'كربلاء المقدسة'),
        ('ذي قار', 'ذي قار'),
        ('بابل', 'بابل'),
        ('السليمانية', 'السليمانية'),
        ('الأنبار', 'الأنبار'),
        ('ديالى', 'ديالى'),
        ('كركوك', 'كركوك'),
        ('صلاح الدين', 'صلاح الدين'),
        ('المثنى', 'المثنى'),
        ('ميسان', 'ميسان'),
        ('واسط', 'واسط'),
        ('القادسية', 'القادسية'),
        ('دهوك', 'دهوك'),
        ('حلبجة', 'حلبجة'),
    ]
    RELIGION_CHOICES = [
        ('muslim', 'مسلم'),
        ('christian', 'مسيحي'),
        ('sabean', 'صابئي مندائي'),
        ('yazidi', 'إيزيدي'),
        ('other', 'أخرى'),
    ]
    HEALTH_STATUS_CHOICES = [
        ('healthy', 'سليم'),
        ('special_needs', 'ذوي الاحتياجات الخاصة'),
        ('chronic', 'مرض مزمن'),
    ]
    BRANCH_CHOICES = [
        ('علمي', 'علمي'),
        ('أدبي', 'أدبي'),
        ('احيائي', 'احيائي'),
        ('تطبيقي', 'تطبيقي'),
        ('مهني', 'مهني'),
        ('تجاري', 'تجاري'),
        ('فنون', 'فنون'),
        ('تمريض', 'تمريض'),
        ('زراعي', 'زراعي'),
        ('حاسوب تقنيات المعلومات', 'حاسوب تقنيات المعلومات'),
        ('فنون تطبيقية', 'فنون تطبيقية'),
        ('معهد اعداد معلمين', 'معهد اعداد معلمين'),
        ('مفوضيه الشرطه', 'مفوضيه الشرطه'),
        ('معهد السياحه والفندقه', 'معهد السياحه والفندقه'),
        ('فنون جميله ابطال', 'فنون جميله ابطال'),
        ('خريج تدريب مهني معهد سكك', 'خريج تدريب مهني معهد سكك'),
    ]
    ROUND_CHOICES = [
        ('1', 'الدور الأول'),
        ('2', 'الدور الثاني'),
        ('3', 'الدور الثالث'),
        ('تكميلي', 'تكميلي'),
    ]
    ORIGIN_CHOICES = [
        ('اصيل', 'أصيل'),
        ('وافد', 'وافد'),
    ]

    ADMISSION_CHANNEL_CHOICES = [
        ('central', 'مركزي'),
        ('parallel', 'موازي'),
        ('private', 'أهلي'),
        ('evening', 'مسائي'),
        ('direct', 'مباشر'),
        ('martyrs', 'ذوي الشهداء'),
        ('talented', 'المتميزين'),
        ('other', 'أخرى'),
    ]

    student_id = models.CharField(max_length=20, unique=True, verbose_name='الرقم الجامعي', editable=False)
    first_name = models.CharField(max_length=100, verbose_name='الاسم الأول')
    second_name = models.CharField(max_length=100, verbose_name='اسم الأب')
    third_name = models.CharField(max_length=100, verbose_name='اسم الجد')
    last_name = models.CharField(max_length=100, verbose_name='الكنية')
    
    # New fields requested
    exam_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='الرقم الامتحاني')
    grad_year_str = models.CharField(max_length=20, blank=True, null=True, verbose_name='سنة التخرج')
    student_category = models.CharField(max_length=100, blank=True, null=True, verbose_name='نوع الطالب')
    admission_round = models.CharField(max_length=10, choices=ROUND_CHOICES, blank=True, null=True, verbose_name='الدور')
    avg_no_additions = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, verbose_name='المعدل بدون اضافات')
    admission_avg = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, verbose_name='معدل القبول')
    branch = models.CharField(max_length=100, choices=BRANCH_CHOICES, blank=True, null=True, verbose_name='الفرع')
    specialization = models.CharField(max_length=100, blank=True, null=True, verbose_name='التخصص')
    has_foreign_language = models.BooleanField(default=False, verbose_name='يملك لغة أجنبية')
    admission_channel = models.CharField(max_length=100, choices=ADMISSION_CHANNEL_CHOICES, blank=True, null=True, verbose_name='القناة')
    institute = models.CharField(max_length=100, blank=True, null=True, verbose_name='المعهد')
    registration_code = models.CharField(max_length=50, blank=True, null=True, verbose_name='كود التسجيل')
    receipt_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='رقم الوصل')
    receipt_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الوصل')
    registration_date = models.DateField(null=True, blank=True, verbose_name='تاريخ التسجيل')
    archive_locker = models.CharField(max_length=100, blank=True, null=True, verbose_name='موقع الأرشيف الورقي (الوكر/الدرج)')
    
    # New Fields
    guardian_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='رقم ولي الأمر')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name='نسبة التخفيض (%)')
    
    school_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='اسم المدرسة')
    origin_status = models.CharField(max_length=50, choices=ORIGIN_CHOICES, blank=True, null=True, verbose_name='حالة الطالب (اصيل او وافد)')
    marital_status = models.CharField(max_length=50, choices=MARITAL_STATUS_CHOICES, blank=True, null=True, verbose_name='الحالة الزوجية')
    health_status = models.CharField(max_length=100, choices=HEALTH_STATUS_CHOICES, blank=True, null=True, verbose_name='الحالة الصحية')
    mother_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='اسم الأم الثلاثي')
    surname = models.CharField(max_length=100, blank=True, null=True, verbose_name='اللقب')
    religion = models.CharField(max_length=50, choices=RELIGION_CHOICES, blank=True, null=True, verbose_name='الديانة')
    
    national_id = models.CharField(max_length=20, unique=True, verbose_name='رقم الهوية/الجواز')
    date_of_birth = models.DateField(verbose_name='تاريخ الميلاد')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='الجنس')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='رقم الهاتف')
    email = models.EmailField(blank=True, null=True, verbose_name='البريد الإلكتروني')
    address = models.TextField(blank=True, null=True, verbose_name='العنوان')
    governorate = models.CharField(max_length=100, choices=GOVERNORATE_CHOICES, blank=True, null=True, verbose_name='المحافظة')
    photo = models.ImageField(upload_to=student_photo_path, blank=True, null=True, verbose_name='الصورة الشخصية')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='students', verbose_name='القسم')
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default='1', verbose_name='المرحلة')
    study_type = models.CharField(max_length=10, choices=STUDY_TYPE_CHOICES, default='morning', verbose_name='نوع الدراسة')
    entry_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='entrants', verbose_name='سنة القبول')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initial', verbose_name='الحالة')

    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')
    gpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00, verbose_name='المعدل التراكمي')
    total_credits = models.IntegerField(default=0, verbose_name='الساعات المكتسبة')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'طالب'
        verbose_name_plural = 'الطلاب'
        ordering = ['student_id']

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.second_name} {self.third_name} {self.last_name}"

    @property
    def short_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = datetime.date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def save(self, *args, **kwargs):
        if not self.student_id:
            year = timezone.now().year
            last = Student.objects.filter(student_id__startswith=str(year)).order_by('-student_id').first()
            if last:
                num = int(last.student_id[-4:]) + 1
            else:
                num = 1
            self.student_id = f"{year}{num:04d}"
        super().save(*args, **kwargs)

    def get_gpa_color(self):
        if self.gpa >= 3.5:
            return 'success'
        elif self.gpa >= 2.5:
            return 'primary'
        elif self.gpa >= 1.5:
            return 'warning'
        else:
            return 'danger'


class StudentDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('id', 'صورة الهوية'),
        ('graduation', 'شهادة التخرج'),
        ('transcript', 'كشف الدرجات'),
        ('medical', 'التقرير الطبي'),
        ('residence', 'وثيقة السكن'),
        ('discount', 'وثيقة التخفيض'),
        ('other', 'أخرى'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents', verbose_name='الطالب')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, verbose_name='نوع الوثيقة')
    title = models.CharField(max_length=200, verbose_name='عنوان الوثيقة')
    file = models.FileField(upload_to='student_docs/', verbose_name='الملف')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'وثيقة طالب'
        verbose_name_plural = 'وثائق الطلاب'

    def __str__(self):
        return f"{self.student.short_name} - {self.get_doc_type_display()}"


class StudentNote(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_notes', verbose_name='الطالب')
    text = models.TextField(verbose_name='الملاحظة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')
    author = models.CharField(max_length=100, blank=True, verbose_name='بواسطة')

    class Meta:
        verbose_name = 'ملاحظة طالب'
        verbose_name_plural = 'ملاحظات الطلاب'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.short_name} - {self.created_at.strftime('%Y/%m/%d')}"


class StudentPromotion(models.Model):
    RESULT_CHOICES = [
        ('success', 'ناجح'),
        ('referred', 'مكمل'),
        ('failed', 'راسب'),
        ('decision', 'ناجح بقرار'),
        ('carry_over', 'تحميل'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='promotions', verbose_name='الطالب')
    from_level = models.CharField(max_length=1, choices=Student.LEVEL_CHOICES, verbose_name='من المرحلة')
    to_level = models.CharField(max_length=1, choices=Student.LEVEL_CHOICES, verbose_name='إلى المرحلة')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, verbose_name='السنة الدراسية')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, verbose_name='النتيجة')
    promotion_date = models.DateField(auto_now_add=True, verbose_name='تاريخ الترحيل')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')

    class Meta:
        verbose_name = 'ترحيل طالب'
        verbose_name_plural = 'ترحيلات الطلاب'
        ordering = ['-promotion_date']

    def __str__(self):
        return f"{self.student.short_name} - {self.from_level} -> {self.to_level} ({self.get_result_display()})"

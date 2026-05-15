from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget
from .models import Department, AcademicYear, Semester, Student, StudentDocument, StudentPromotion
import re


class StudentResource(resources.ModelResource):
    """
    Professional Import/Export resource with precise Arabic column mapping.
    Each field is explicitly declared with column_name to prevent any
    header-data mismatch during import or export.
    """

    # === Identity Fields ===
    student_id = fields.Field(
        column_name='الرقم الجامعي', attribute='student_id',
    )
    first_name = fields.Field(
        column_name='الاسم الأول', attribute='first_name',
    )
    second_name = fields.Field(
        column_name='اسم الأب', attribute='second_name',
    )
    third_name = fields.Field(
        column_name='اسم الجد', attribute='third_name',
    )
    last_name = fields.Field(
        column_name='الكنية', attribute='last_name',
    )
    surname = fields.Field(
        column_name='اللقب', attribute='surname',
    )
    mother_name = fields.Field(
        column_name='اسم الأم الثلاثي', attribute='mother_name',
    )
    national_id = fields.Field(
        column_name='رقم الهوية/الجواز', attribute='national_id',
    )
    exam_number = fields.Field(
        column_name='الرقم الامتحاني', attribute='exam_number',
    )

    # === Personal Fields ===
    date_of_birth = fields.Field(
        column_name='تاريخ الميلاد', attribute='date_of_birth',
    )
    gender = fields.Field(
        column_name='الجنس', attribute='gender',
    )
    religion = fields.Field(
        column_name='الديانة', attribute='religion',
    )
    marital_status = fields.Field(
        column_name='الحالة الزوجية', attribute='marital_status',
    )
    health_status = fields.Field(
        column_name='الحالة الصحية', attribute='health_status',
    )
    origin_status = fields.Field(
        column_name='حالة الطالب', attribute='origin_status',
    )

    # === Contact Fields ===
    phone = fields.Field(
        column_name='رقم الهاتف', attribute='phone',
    )
    email = fields.Field(
        column_name='البريد الإلكتروني', attribute='email',
    )
    governorate = fields.Field(
        column_name='المحافظة', attribute='governorate',
    )
    address = fields.Field(
        column_name='العنوان', attribute='address',
    )

    # === FK Fields with proper widgets ===
    department = fields.Field(
        column_name='القسم',
        attribute='department',
        widget=ForeignKeyWidget(Department, field='name'),
    )
    entry_year = fields.Field(
        column_name='سنة القبول',
        attribute='entry_year',
        widget=ForeignKeyWidget(AcademicYear, field='year'),
    )

    # === Academic Fields ===
    level = fields.Field(
        column_name='المرحلة', attribute='level',
    )
    study_type = fields.Field(
        column_name='نوع الدراسة', attribute='study_type',
    )
    status = fields.Field(
        column_name='الحالة', attribute='status',
    )
    avg_no_additions = fields.Field(
        column_name='المعدل بدون اضافات', attribute='avg_no_additions',
    )
    admission_avg = fields.Field(
        column_name='معدل القبول', attribute='admission_avg',
    )
    branch = fields.Field(
        column_name='الفرع', attribute='branch',
    )
    admission_channel = fields.Field(
        column_name='القناة', attribute='admission_channel',
    )
    grad_year_str = fields.Field(
        column_name='سنة التخرج', attribute='grad_year_str',
    )
    student_category = fields.Field(
        column_name='نوع الطالب', attribute='student_category',
    )
    admission_round = fields.Field(
        column_name='الدور', attribute='admission_round',
    )
    institute = fields.Field(
        column_name='المعهد', attribute='institute',
    )
    school_name = fields.Field(
        column_name='اسم المدرسة', attribute='school_name',
    )
    gpa = fields.Field(
        column_name='المعدل التراكمي', attribute='gpa',
    )

    class Meta:
        model = Student
        import_id_fields = ('national_id',)
        fields = (
            'student_id', 'first_name', 'second_name', 'third_name', 'last_name',
            'surname', 'mother_name', 'national_id', 'exam_number', 'date_of_birth',
            'gender', 'religion', 'marital_status', 'health_status', 'origin_status',
            'phone', 'email', 'governorate', 'address', 'department', 'entry_year',
            'level', 'study_type', 'status', 'avg_no_additions', 'admission_avg',
            'branch', 'admission_channel', 'grad_year_str', 'student_category',
            'admission_round', 'institute', 'school_name', 'gpa',
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = False

    # --- Header alias map: maps non-standard Arabic headers to our column_name ---
    HEADER_ALIASES = {
        'الاسم الاول': 'الاسم الأول',
        'اسم الاب': 'اسم الأب',
        'ااسم الام الثلاثي': 'اسم الأم الثلاثي',
        'اسم الام الثلاثي': 'اسم الأم الثلاثي',
        'اسم الأم': 'اسم الأم الثلاثي',
        'الحالية الصحية': 'الحالة الصحية',
        'حالة الطالب (اصيل او وافد)': 'حالة الطالب',
        'اصيل/وافد': 'حالة الطالب',
        'محافظة السكن': 'المحافظة',
        'رقم الهوية': 'رقم الهوية/الجواز',
        'الهاتف': 'رقم الهاتف',
        'سنة الدراسية': 'سنة القبول',
        'قسم الطالب': 'القسم',
        'اسم القسم': 'القسم',
        'الفرع العلمي': 'القسم',
        'الاختصاص': 'القسم',
    }

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        """
        Normalize dataset headers to match our field column_names.
        """
        def normalize_arabic(text):
            if not text: return ""
            text = str(text).strip()
            text = re.sub(r'[أإآا]', 'ا', text)
            text = re.sub(r'[ةه]', 'ه', text)
            text = re.sub(r'[\u064B-\u0652]', '', text)
            text = re.sub(r'\s+', '', text)
            return text

        new_headers = []
        for header in dataset.headers:
            norm_h = normalize_arabic(header)
            target_header = header
            
            # 1. Check if it matches any of our fields' column_names
            for field_name, field in self.fields.items():
                if normalize_arabic(field.column_name) == norm_h:
                    target_header = field.column_name
                    break
            else:
                # 2. Check aliases
                for alias, standard in self.HEADER_ALIASES.items():
                    if normalize_arabic(alias) == norm_h:
                        target_header = standard
                        break
            
            new_headers.append(target_header)
        
        dataset.headers = new_headers

    def before_import_row(self, row, **kwargs):
        """
        Normalize incoming data before import.
        Headers are already normalized in before_import.
        """
        # --- 2. Handle full-name column splitting ---
        for name_header in ['اسم الطالب', 'الاسم الكامل']:
            full_name = row.get(name_header)
            if full_name and not row.get('الاسم الأول'):
                parts = str(full_name).split()
                if len(parts) >= 1: row['الاسم الأول'] = parts[0]
                if len(parts) >= 2: row['اسم الأب'] = parts[1]
                if len(parts) >= 3: row['اسم الجد'] = parts[2]
                if len(parts) >= 4: row['الكنية'] = ' '.join(parts[3:])
                elif len(parts) > 1: row['الكنية'] = parts[-1]
                else: row['الكنية'] = '-'
                break

        # --- 3. Normalize date of birth ---
        dob = row.get('تاريخ الميلاد')
        if dob:
            d_str = str(dob).strip()
            if d_str.isdigit() and len(d_str) == 4:
                row['تاريخ الميلاد'] = f'{d_str}-01-01'

        # --- 4. Normalize gender ---
        gender_val = row.get('الجنس')
        if gender_val:
            g = str(gender_val).strip()
            if any(x in g for x in ['أنث', 'انث', 'بنت', 'طالبة']) or 'female' in g.lower():
                row['الجنس'] = 'female'
            elif any(x in g for x in ['ذكر', 'ولد', 'طالب']) or 'male' in g.lower():
                row['الجنس'] = 'male'

        # --- 4b. Normalize Status ---
        status_val = row.get('الحالة')
        if status_val:
            s = str(status_val).strip()
            if 'مستمر' in s or 'active' in s.lower(): row['الحالة'] = 'active'
            elif 'خريج' in s or 'grad' in s.lower(): row['الحالة'] = 'graduated'
            elif 'مؤجل' in s or 'post' in s.lower(): row['الحالة'] = 'postponed'
            elif 'منسحب' in s or 'withdrawn' in s.lower(): row['الحالة'] = 'withdrawn'
            elif 'مرقن' in s or 'dismissed' in s.lower(): row['الحالة'] = 'dismissed'

        # --- 5. Department Normalization ---
        def normalize_arabic(text):
            if not text: return ""
            text = str(text).strip()
            text = re.sub(r'[أإآا]', 'ا', text)
            text = re.sub(r'[ةه]', 'ه', text)
            text = re.sub(r'[\u064B-\u0652]', '', text)
            text = re.sub(r'\s+', '', text)
            return text

        dept_val = row.get('القسم')
        if dept_val:
            dept_str = str(dept_val).strip()
            if dept_str.isdigit():
                try:
                    row['القسم'] = Department.objects.get(id=int(dept_str)).name
                except: pass
            else:
                norm_input = normalize_arabic(dept_str)
                norm_input_no_qasm = re.sub(r'^قسم', '', norm_input)
                
                dept = None
                all_depts = list(Department.objects.all())
                for d in all_depts:
                    norm_db = normalize_arabic(d.name)
                    norm_db_no_qasm = re.sub(r'^قسم', '', norm_db)
                    
                    if norm_input == norm_db or norm_input_no_qasm == norm_db_no_qasm or \
                       norm_input_no_qasm in norm_db_no_qasm or norm_db_no_qasm in norm_input_no_qasm:
                        dept = d
                        break
                
                if dept:
                    row['القسم'] = dept.name
                
                # Final safety check: If row['القسم'] is still not a valid department name in DB,
                # we must ensure it doesn't cause a NOT NULL crash.
                if not Department.objects.filter(name=row.get('القسم')).exists():
                    d = Department.objects.first()
                    if d: row['القسم'] = d.name
        else:
            # If missing completely, use first department as safety
            d = Department.objects.first()
            if d: row['القسم'] = d.name

        # --- 6. Entry year FK fallback & normalization ---
        year_val = row.get('سنة القبول')
        if year_val:
            y_str = str(year_val).strip()
            if y_str.isdigit() and int(y_str) < 1000:
                try:
                    row['سنة القبول'] = AcademicYear.objects.get(id=int(y_str)).year
                except: pass
            else:
                # Fuzzy matching for years like "2024", "2024/2025", etc.
                year_digits = re.findall(r'\d{4}', y_str)
                if year_digits:
                    y_match = AcademicYear.objects.filter(year__icontains=year_digits[0]).first()
                    if y_match:
                        row['سنة القبول'] = y_match.year
        
        # Final safety check for Entry Year (Prevent NOT NULL crash)
        if not AcademicYear.objects.filter(year=row.get('سنة القبول')).exists():
            y = AcademicYear.objects.first()
            if y: row['سنة القبول'] = y.year

        # --- 7. Sync GPA from admission average ---
        avg = row.get('المعدل بدون اضافات') or row.get('معدل القبول')
        if avg and not row.get('المعدل التراكمي'):
            try:
                row['المعدل التراكمي'] = float(str(avg).replace(',', '.'))
            except: pass

        # --- 8. Set defaults for required fields ---
        if not row.get('الحالة'):
            row['الحالة'] = 'active'
        if not row.get('المرحلة'):
            row['المرحلة'] = '1'
        if not row.get('نوع الدراسة'):
            row['نوع الدراسة'] = 'morning'


# ====================================================================
# ADMIN REGISTRATIONS
# ====================================================================

@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    list_display = ('name', 'code', 'head_name')
    search_fields = ('name', 'code')


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'name', 'academic_year')


class StudentDocumentInline(admin.TabularInline):
    model = StudentDocument
    extra = 1


@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ('national_id', 'first_name', 'last_name', 'department', 'level', 'status')
    list_filter = ('status', 'gender', 'level', 'department', 'study_type')
    search_fields = ('national_id', 'first_name', 'last_name', 'phone', 'exam_number')
    readonly_fields = ('student_id',)
    inlines = [StudentDocumentInline]

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (
                'student_id',
                ('first_name', 'second_name', 'third_name', 'last_name'),
                'surname', 'mother_name', 'national_id', 'exam_number'
            )
        }),
        ('البيانات الشخصية', {
            'fields': (
                ('date_of_birth', 'gender', 'religion'),
                ('marital_status', 'health_status', 'origin_status'),
                ('phone', 'guardian_phone', 'email'),
                ('governorate', 'address')
            )
        }),
        ('البيانات الدراسية (قبل القبول)', {
            'fields': (
                'school_name', 'branch', 'grad_year_str',
                ('avg_no_additions', 'admission_avg', 'admission_round')
            )
        }),
        ('بيانات القبول والتسجيل', {
            'fields': (
                'admission_channel', 'institute', 'department', 'level', 'study_type',
                ('registration_code', 'registration_date'),
                ('receipt_number', 'receipt_date'),
                ('discount_percentage', 'entry_year'),
                'status'
            )
        }),
        ('أخرى', {
            'fields': ('photo', 'notes', 'gpa', 'total_credits'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'doc_type', 'uploaded_at', 'doc_link')
    search_fields = ('student__first_name', 'student__last_name', 'title')
    list_filter = ('doc_type',)

    def doc_link(self, obj):
        from django.utils.html import format_html
        if obj.file:
            return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
        return "No file"
    doc_link.short_description = 'Link'


@admin.register(StudentPromotion)
class StudentPromotionAdmin(admin.ModelAdmin):
    list_display = ('student', 'from_level', 'to_level', 'academic_year', 'result', 'promotion_date')
    list_filter = ('result', 'from_level', 'to_level', 'academic_year')
    search_fields = ('student__first_name', 'student__last_name', 'student__student_id')

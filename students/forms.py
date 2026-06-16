from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Div, Field, HTML
from .models import Student, Department, AcademicYear, Semester, StudentDocument, StudentPromotion
from core.models import get_dynamic_choices


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'first_name', 'second_name', 'third_name', 'last_name', 'surname',
            'mother_name', 'national_id', 'exam_number', 'date_of_birth', 'gender',
            'religion', 'ethnicity', 'birth_place', 'citizenship', 'marital_status', 'health_status', 'origin_status',
            'phone', 'guardian_phone', 'email', 'governorate', 'address', 'photo',
            'school_name', 'branch', 'specialization', 'has_foreign_language', 'grad_year_str', 'avg_no_additions',
            'admission_avg', 'total_score', 'admission_round', 'admission_channel', 'institute',
            'department', 'level', 'study_type', 'registration_code',
            'registration_date', 'receipt_number', 'receipt_date', 'archive_locker', 'entry_year',
            'status', 'discount_percentage', 'notes',
            
            # Document receipt status and checklist
            'document_receipt', 'document_auth',
            'doc_national_id_student', 'doc_national_id_father', 'doc_national_id_mother',
            'doc_death_certificate', 'doc_residence_card', 'doc_personal_photos',
            'doc_sponsor', 'doc_medical_exam', 'doc_grade_confirmation'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'registration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'receipt_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically load choices from settings/DB
        self.fields['governorate'].choices = get_dynamic_choices('governorate', Student.GOVERNORATE_CHOICES)
        self.fields['religion'].choices = get_dynamic_choices('religion', Student.RELIGION_CHOICES)
        self.fields['admission_channel'].choices = get_dynamic_choices('admission_channel', Student.ADMISSION_CHANNEL_CHOICES)
        self.fields['branch'].choices = get_dynamic_choices('branch', Student.BRANCH_CHOICES)
        self.fields['origin_status'].choices = get_dynamic_choices('origin_status', Student.ORIGIN_CHOICES)
        self.fields['marital_status'].choices = get_dynamic_choices('marital_status', Student.MARITAL_STATUS_CHOICES)
        self.fields['health_status'].choices = get_dynamic_choices('health_status', Student.HEALTH_STATUS_CHOICES)
        self.fields['birth_place'].choices = get_dynamic_choices('birth_place', Student.BIRTH_PLACE_CHOICES)
        self.fields['citizenship'].choices = get_dynamic_choices('citizenship', Student.CITIZENSHIP_CHOICES)
        self.fields['gender'].choices = get_dynamic_choices('gender', Student.GENDER_CHOICES)
        self.fields['level'].choices = get_dynamic_choices('level', Student.LEVEL_CHOICES)
        self.fields['study_type'].choices = get_dynamic_choices('study_type', Student.STUDY_TYPE_CHOICES)
        self.fields['status'].choices = get_dynamic_choices('status', Student.STATUS_CHOICES)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            HTML('<div class="alert alert-info py-2 mb-3" style="font-size:12px"><i class="fas fa-info-circle me-1"></i>الحقول الملحقة بعلامة <span class="text-danger fw-bold">*</span> هي حقول إجبارية.</div>'),
            HTML('<h6 class="fw-bold text-primary mb-3"><i class="fas fa-user me-2"></i>البيانات الشخصية والأساسية</h6>'),
            Row(
                Column('first_name', css_class='col-md-3'),
                Column('second_name', css_class='col-md-3'),
                Column('third_name', css_class='col-md-3'),
                Column('last_name', css_class='col-md-3'),
            ),
            Row(
                Column('surname', css_class='col-md-3'),
                Column('mother_name', css_class='col-md-5'),
                Column('religion', css_class='col-md-2'),
                Column('ethnicity', css_class='col-md-2'),
            ),
            Row(
                Column('birth_place', css_class='col-md-4'),
                Column('citizenship', css_class='col-md-4'),
                Column('national_id', css_class='col-md-4'),
            ),
            Row(
                Column('exam_number', css_class='col-md-4'),
                Column('date_of_birth', css_class='col-md-4'),
                Column('gender', css_class='col-md-4'),
            ),
            Row(
                Column('marital_status', css_class='col-md-4'),
                Column('health_status', css_class='col-md-4'),
                Column('origin_status', css_class='col-md-4'),
            ),
            Row(
                Column('phone', css_class='col-md-4'),
                Column('guardian_phone', css_class='col-md-4'),
                Column('email', css_class='col-md-4'),
            ),
            Row(
                Column('governorate', css_class='col-md-4'),
                Column('address', css_class='col-md-8'),
            ),
            HTML('<hr><h6 class="fw-bold text-primary mb-3"><i class="fas fa-school me-2"></i>البيانات الدراسية والقبول</h6>'),
            Row(
                Column('school_name', css_class='col-md-3'),
                Column('branch', css_class='col-md-3'),
                Column('specialization', css_class='col-md-3'),
                Column('grad_year_str', css_class='col-md-3'),
            ),
            Row(
                Column('avg_no_additions', css_class='col-md-4'),
                Column('admission_avg', css_class='col-md-4'),
                Column('total_score', css_class='col-md-4'),
            ),
            Row(
                Column('admission_round', css_class='col-md-3'),
                Column('admission_channel', css_class='col-md-3'),
                Column('institute', css_class='col-md-3'),
                Column('department', css_class='col-md-3'),
            ),
            Row(
                Column('level', css_class='col-md-3'),
                Column('study_type', css_class='col-md-3'),
                Column('entry_year', css_class='col-md-3'),
                Column('status', css_class='col-md-3'),
            ),
            HTML('<hr><h6 class="fw-bold text-primary mb-3"><i class="fas fa-file-invoice me-2"></i>بيانات التسجيل والوصل</h6>'),
            Row(
                Column('registration_code', css_class='col-md-3'),
                Column('registration_date', css_class='col-md-3'),
                Column('archive_locker', css_class='col-md-6'),
            ),
            Row(
                Column('receipt_number', css_class='col-md-4'),
                Column('receipt_date', css_class='col-md-4'),
                Column('discount_percentage', css_class='col-md-4'),
            ),
            Row(
                Column('photo', css_class='col-md-12'),
            ),
            HTML('<hr><h6 class="fw-bold text-primary mb-3"><i class="fas fa-file-signature me-2"></i>تدقيق الوثائق والمستندات الورقية</h6>'),
            Row(
                Column('document_receipt', css_class='col-md-6'),
                Column('document_auth', css_class='col-md-6'),
            ),
            Row(
                Column('doc_national_id_student', css_class='col-md-4'),
                Column('doc_national_id_father', css_class='col-md-4'),
                Column('doc_national_id_mother', css_class='col-md-4'),
            ),
            Row(
                Column('doc_death_certificate', css_class='col-md-4'),
                Column('doc_residence_card', css_class='col-md-4'),
                Column('doc_personal_photos', css_class='col-md-4'),
            ),
            Row(
                Column('doc_sponsor', css_class='col-md-4'),
                Column('doc_medical_exam', css_class='col-md-4'),
                Column('doc_grade_confirmation', css_class='col-md-4'),
            ),
            Row(
                Column('has_foreign_language', css_class='col-md-4'),
            ),
            'notes',
            Div(
                Submit('submit', 'حفظ البيانات', css_class='btn btn-primary btn-lg px-5'),
                HTML('<a href="javascript:history.back()" class="btn btn-outline-secondary btn-lg px-4 ms-2">إلغاء</a>'),
                css_class='d-flex justify-content-end mt-3'
            )
        )
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.setdefault('class', 'form-control')


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'head_name', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-8'), Column('code', css_class='col-md-4')),
            'description',
            Row(Column('head_name', css_class='col-md-4'), Column('email', css_class='col-md-4'), Column('phone', css_class='col-md-4')),
            Div(
                Submit('submit', 'حفظ', css_class='btn btn-primary px-4'),
                HTML('<a href="{% url \'department_list\' %}" class="btn btn-outline-secondary px-4 ms-2">إلغاء</a>'),
                css_class='d-flex justify-content-end mt-3'
            )
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['year', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'year',
            Row(
                Column('start_date', css_class='col-md-6'),
                Column('end_date', css_class='col-md-6'),
            ),
            'is_active',
            Div(
                Submit('submit', 'حفظ', css_class='btn btn-primary px-4'),
                HTML('<a href="{% url \'academic_year_list\' %}" class="btn btn-outline-secondary px-4 ms-2">إلغاء</a>'),
                css_class='d-flex justify-content-end mt-3'
            )
        )
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-control')


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['academic_year', 'name', 'start_date', 'end_date', 'is_active', 'registration_open']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'academic_year',
            'name',
            Row(
                Column('start_date', css_class='col-md-6'),
                Column('end_date', css_class='col-md-6'),
            ),
            Row(
                Column('is_active', css_class='col-md-6'),
                Column('registration_open', css_class='col-md-6'),
            ),
            Div(
                Submit('submit', 'حفظ', css_class='btn btn-primary px-4'),
                HTML('<a href="{% url \'semester_list\' %}" class="btn btn-outline-secondary px-4 ms-2">إلغاء</a>'),
                css_class='d-flex justify-content-end mt-3'
            )
        )
        for fname, field in self.fields.items():
            if fname not in ('is_active', 'registration_open'):
                field.widget.attrs['class'] = 'form-control'


class StudentDocumentForm(forms.ModelForm):
    class Meta:
        model = StudentDocument
        fields = ['doc_type', 'title', 'file', 'notes']
        widgets = {
            'doc_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: الهوية الوطنية'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'ملاحظات إضافية...'}),
        }


class StudentPromotionForm(forms.ModelForm):
    class Meta:
        model = StudentPromotion
        fields = ['from_level', 'to_level', 'academic_year', 'result', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('from_level', css_class='col-md-6'),
                Column('to_level', css_class='col-md-6'),
            ),
            Row(
                Column('academic_year', css_class='col-md-6'),
                Column('result', css_class='col-md-6'),
            ),
            'notes',
            Div(
                Submit('submit', 'تنفيذ الترحيل', css_class='btn btn-success px-4'),
                css_class='d-flex justify-content-end'
            )
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

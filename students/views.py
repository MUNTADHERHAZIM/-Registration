from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from .models import Student, Department, AcademicYear, Semester, StudentDocument, StudentPromotion, StudentNote
from core.models import SystemLog
from .forms import StudentForm, DepartmentForm, AcademicYearForm, SemesterForm, StudentDocumentForm
from .admin import StudentResource
from import_export.formats.base_formats import XLSX, CSV
import os
import tablib
import base64
from django.conf import settings


@login_required
@permission_required('students.view_student', raise_exception=True)
def dashboard(request):
    # Statistics
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='active').count()
    graduated_students = Student.objects.filter(status='graduated').count()
    suspended_students = Student.objects.filter(status='suspended').count()
    total_departments = Department.objects.count()
    
    current_semester = Semester.objects.filter(is_active=True).first()
    
    # Students by department
    dept_stats = Department.objects.annotate(
        student_count=Count('students', filter=Q(students__status='active'))
    ).values('name', 'student_count').order_by('-student_count')
    
    # Students by level
    level_stats = Student.objects.filter(status='active').values('level').annotate(
        count=Count('id')
    ).order_by('level')
    
    # Students by gender
    male_count = Student.objects.filter(gender='male', status='active').count()
    female_count = Student.objects.filter(gender='female', status='active').count()
    
    # Recent students
    recent_students = Student.objects.order_by('-created_at')[:8]
    
    # Monthly registration stats
    from django.db.models.functions import TruncMonth
    from django.utils import timezone
    import datetime
    
    six_months_ago = timezone.now() - datetime.timedelta(days=180)
    monthly_stats = Student.objects.filter(
        created_at__gte=six_months_ago
    ).annotate(month=TruncMonth('created_at')).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    context = {
        'total_students': total_students,
        'active_students': active_students,
        'graduated_students': graduated_students,
        'suspended_students': suspended_students,
        'total_departments': total_departments,
        'current_semester': current_semester,
        'dept_stats': list(dept_stats),
        'level_stats': list(level_stats),
        'male_count': male_count,
        'female_count': female_count,
        'recent_students': recent_students,
        'monthly_stats': list(monthly_stats),
    }
    return render(request, 'base/dashboard.html', context)


@login_required
@permission_required('students.view_student', raise_exception=True)
def student_list(request):
    students = Student.objects.select_related('department', 'entry_year').all()
    
    # Search
    search = request.GET.get('q', '')
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(second_name__icontains=search) |
            Q(third_name__icontains=search) |
            Q(student_id__icontains=search) |
            Q(national_id__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Filters
    dept_filter = request.GET.get('department', '')
    if dept_filter:
        students = students.filter(department_id=dept_filter)
    
    level_filter = request.GET.get('level', '')
    if level_filter:
        students = students.filter(level=level_filter)
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        students = students.filter(status=status_filter)
    
    gender_filter = request.GET.get('gender', '')
    if gender_filter:
        students = students.filter(gender=gender_filter)
    
    study_filter = request.GET.get('study_type', '')
    if study_filter:
        students = students.filter(study_type=study_filter)

    doc_receipt_filter = request.GET.get('doc_receipt', '')
    if doc_receipt_filter:
        students = students.filter(document_receipt=doc_receipt_filter)

    doc_auth_filter = request.GET.get('doc_auth', '')
    if doc_auth_filter:
        students = students.filter(document_auth=doc_auth_filter)

    # Document Checklist Filters
    doc_student_filter = request.GET.get('doc_student', '')
    if doc_student_filter == 'true':
        students = students.filter(doc_national_id_student=True)
    elif doc_student_filter == 'false':
        students = students.filter(doc_national_id_student=False)

    doc_father_filter = request.GET.get('doc_father', '')
    if doc_father_filter == 'true':
        students = students.filter(doc_national_id_father=True)
    elif doc_father_filter == 'false':
        students = students.filter(doc_national_id_father=False)

    doc_mother_filter = request.GET.get('doc_mother', '')
    if doc_mother_filter == 'true':
        students = students.filter(doc_national_id_mother=True)
    elif doc_mother_filter == 'false':
        students = students.filter(doc_national_id_mother=False)

    doc_residence_filter = request.GET.get('doc_residence', '')
    if doc_residence_filter == 'true':
        students = students.filter(doc_residence_card=True)
    elif doc_residence_filter == 'false':
        students = students.filter(doc_residence_card=False)

    doc_photos_filter = request.GET.get('doc_photos', '')
    if doc_photos_filter == 'true':
        students = students.filter(doc_personal_photos=True)
    elif doc_photos_filter == 'false':
        students = students.filter(doc_personal_photos=False)

    doc_sponsor_filter = request.GET.get('doc_sponsor', '')
    if doc_sponsor_filter == 'true':
        students = students.filter(doc_sponsor=True)
    elif doc_sponsor_filter == 'false':
        students = students.filter(doc_sponsor=False)

    doc_medical_filter = request.GET.get('doc_medical', '')
    if doc_medical_filter == 'true':
        students = students.filter(doc_medical_exam=True)
    elif doc_medical_filter == 'false':
        students = students.filter(doc_medical_exam=False)

    doc_grade_filter = request.GET.get('doc_grade', '')
    if doc_grade_filter == 'true':
        students = students.filter(doc_grade_confirmation=True)
    elif doc_grade_filter == 'false':
        students = students.filter(doc_grade_confirmation=False)

    doc_death_filter = request.GET.get('doc_death', '')
    if doc_death_filter == 'true':
        students = students.filter(doc_death_certificate=True)
    elif doc_death_filter == 'false':
        students = students.filter(doc_death_certificate=False)
    
    # Sorting
    sort = request.GET.get('sort', 'student_id')
    sort_options = {
        'student_id': ['student_id'],
        'name': ['first_name', 'second_name', 'third_name', 'last_name'],
        'gpa': ['gpa'],
        '-gpa': ['-gpa'],
        'created_at': ['created_at'],
        '-created_at': ['-created_at'],
    }
    
    if sort in sort_options:
        students = students.order_by(*sort_options[sort])
    else:
        students = students.order_by('student_id')
    
    total_count = students.count()
    
    # Pagination
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    departments = Department.objects.all()
    
    context = {
        'page_obj': page_obj,
        'students': page_obj,
        'departments': departments,
        'search': search,
        'dept_filter': dept_filter,
        'level_filter': level_filter,
        'status_filter': status_filter,
        'gender_filter': gender_filter,
        'study_filter': study_filter,
        'doc_receipt_filter': doc_receipt_filter,
        'doc_auth_filter': doc_auth_filter,
        'doc_student_filter': doc_student_filter,
        'doc_father_filter': doc_father_filter,
        'doc_mother_filter': doc_mother_filter,
        'doc_residence_filter': doc_residence_filter,
        'doc_photos_filter': doc_photos_filter,
        'doc_sponsor_filter': doc_sponsor_filter,
        'doc_medical_filter': doc_medical_filter,
        'doc_grade_filter': doc_grade_filter,
        'doc_death_filter': doc_death_filter,
        'sort': sort,
        'total_count': total_count,
        'sort_filter': sort,
        'title': 'قائمة الطلاب',
    }
    return render(request, 'students/student_list.html', context)


@login_required
@permission_required('students.view_student', raise_exception=True)
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    documents = student.documents.all().order_by('-uploaded_at')
    doc_form = StudentDocumentForm()
    
    # Get previous and next students based on student_id ordering
    prev_student = Student.objects.filter(student_id__lt=student.student_id).order_by('-student_id').first()
    next_student = Student.objects.filter(student_id__gt=student.student_id).order_by('student_id').first()
    
    # Get all students for the dropdown search selector
    all_students = Student.objects.all().order_by('student_id').only('id', 'first_name', 'second_name', 'third_name', 'last_name', 'student_id')
    
    context = {
        'student': student,
        'documents': documents,
        'doc_form': doc_form,
        'prev_student': prev_student,
        'next_student': next_student,
        'all_students': all_students,
        'title': f'ملف الطالب - {student.short_name}',
    }
    return render(request, 'students/student_detail.html', context)


@login_required
def add_student_document(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.student = student
            doc.save()
            full_user_name = request.user.get_full_name() or request.user.username
            SystemLog.objects.create(
                user=request.user,
                action='create',
                details=f"قام [{full_user_name}] بإضافة وثيقة جديدة بعنوان ({doc.title}) للطالب: {student.short_name}"
            )
            messages.success(request, 'تمت إضافة الوثيقة بنجاح')
        else:
            messages.error(request, 'خطأ في إضافة الوثيقة')
    return redirect('student_detail', pk=pk)


@login_required
@permission_required('students.add_student', raise_exception=True)
def student_add(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            full_user_name = request.user.get_full_name() or request.user.username
            SystemLog.objects.create(
                user=request.user,
                action='create',
                details=f"قام [{full_user_name}] بإضافة الطالب الجديد: {student.full_name} (رقم: {student.student_id})"
            )
            messages.success(request, f'تم إضافة الطالب {student.full_name} بنجاح. الرقم الجامعي: {student.student_id}')
            return redirect('student_detail', pk=student.pk)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = StudentForm()
    
    return render(request, 'students/student_form.html', {
        'form': form,
        'title': 'إضافة طالب جديد',
        'action': 'إضافة',
    })


@login_required
@permission_required('students.change_student', raise_exception=True)
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            full_user_name = request.user.get_full_name() or request.user.username
            SystemLog.objects.create(
                user=request.user,
                action='update',
                details=f"قام [{full_user_name}] بتحديث بيانات الطالب: {student.full_name} (رقم: {student.student_id})"
            )
            messages.success(request, 'تم تحديث بيانات الطالب بنجاح')
            return redirect('student_detail', pk=student.pk)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'students/student_form.html', {
        'form': form,
        'student': student,
        'title': f'تعديل بيانات: {student.short_name}',
        'action': 'حفظ التعديلات',
    })


@login_required
@permission_required('students.delete_student', raise_exception=True)
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        sid = student.student_id
        full_user_name = request.user.get_full_name() or request.user.username
        student.delete()
        SystemLog.objects.create(
            user=request.user,
            action='delete',
            details=f"قام [{full_user_name}] بحذف سجل الطالب بشكل نهائي: {name} (رقم: {sid})"
        )
        messages.success(request, f'تم حذف الطالب {name} بنجاح')
        return redirect('student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})


# Department views
@login_required
def department_list(request):
    departments = Department.objects.annotate(
        student_count=Count('students'),
        active_count=Count('students', filter=Q(students__status='active')),
    )
    return render(request, 'students/department_list.html', {
        'departments': departments,
        'title': 'الأقسام الدراسية',
    })


@login_required
def department_add(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f'تم إضافة القسم {dept.name} بنجاح')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'students/department_form.html', {'form': form, 'title': 'إضافة قسم'})


@login_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات القسم بنجاح')
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'students/department_form.html', {'form': form, 'dept': dept, 'title': f'تعديل: {dept.name}'})


@login_required
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        if dept.students.exists():
            messages.error(request, 'لا يمكن حذف القسم لوجود طلاب مرتبطين به')
        else:
            dept.delete()
            messages.success(request, 'تم حذف القسم بنجاح')
        return redirect('department_list')
    return render(request, 'students/department_confirm_delete.html', {'dept': dept})


# Academic Year views
@login_required
def academic_year_list(request):
    years = AcademicYear.objects.prefetch_related('semesters').annotate(
        student_count=Count('entrants')
    )
    return render(request, 'students/academic_year_list.html', {
        'years': years,
        'title': 'السنوات الدراسية',
    })


@login_required
def academic_year_add(request):
    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة السنة الدراسية بنجاح')
            return redirect('academic_year_list')
    else:
        form = AcademicYearForm()
    return render(request, 'students/academic_year_form.html', {'form': form, 'title': 'إضافة سنة دراسية'})


@login_required
def semester_list(request):
    semesters = Semester.objects.select_related('academic_year').all()
    return render(request, 'students/semester_list.html', {
        'semesters': semesters,
        'title': 'الفصول الدراسية',
    })


@login_required
def semester_add(request):
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الفصل الدراسي بنجاح')
            return redirect('semester_list')
    else:
        form = SemesterForm()
    return render(request, 'students/semester_form.html', {'form': form, 'title': 'إضافة فصل دراسي'})


@login_required
def student_print(request, pk):
    student = get_object_or_404(Student, pk=pk)
    import datetime
    return render(request, 'students/student_print.html', {
        'student': student,
        'today': datetime.date.today(),
        'title': f'تأييد قيد - {student.full_name}',
    })


@login_required
def api_students_search(request):
    """Ajax search for students"""
    q = request.GET.get('q', '')
    students = Student.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q) |
        Q(student_id__icontains=q)
    ).values('id', 'student_id', 'first_name', 'last_name', 'second_name', 'third_name')[:10]
    data = [{'id': s['id'], 'text': f"{s['student_id']} - {s['first_name']} {s['last_name']}"} for s in students]
    return JsonResponse({'results': data})


@login_required
def preliminary_registration_list(request):
    """View for students with status 'initial'"""
    students = Student.objects.filter(status='initial').select_related('department', 'entry_year')
    
    # Re-use search logic from student_list if possible, but for simplicity here:
    search = request.GET.get('q', '')
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(student_id__icontains=search)
        )
    
    context = {
        'students': students,
        'search': search,
        'title': 'التقديم الأولي',
    }
    return render(request, 'students/preliminary_list.html', context)


@login_required
def activate_students(request):
    """Bulk change status from 'initial' to 'active' (المباشرة)"""
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        if not student_ids:
            messages.error(request, 'يرجى تحديد الطلاب للمباشرة')
            return redirect('preliminary_list')
        
        count = Student.objects.filter(id__in=student_ids, status='initial').update(status='active')
        messages.success(request, f'تم تفعيل مباشرة {count} طلاب بنجاح')
        return redirect('student_list')
    return redirect('preliminary_list')


@login_required
def student_promote(request):
    """View to promote students to next level"""
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        to_level = request.POST.get('to_level')
        academic_year_id = request.POST.get('academic_year')
        result = request.POST.get('result')
        
        if not student_ids:
            messages.error(request, 'يرجى تحديد الطلاب للترحيل')
            return redirect('student_promote')
            
        academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
        
        count = 0
        for student_id in student_ids:
            student = get_object_or_404(Student, pk=student_id)
            from_level = student.level
            
            # Update student level
            student.level = to_level
            if result == 'graduated':
                student.status = 'graduated'
            student.save()
            
            # Create promotion record
            StudentPromotion.objects.create(
                student=student,
                from_level=from_level,
                to_level=to_level,
                academic_year=academic_year,
                result=result
            )
            count += 1
            
        messages.success(request, f'تم ترحيل {count} طلاب بنجاح')
        return redirect('student_list')
        
    # GET request: show promotion interface
    students = Student.objects.filter(status='active')
    
    # Filters for selection
    dept_id = request.GET.get('department')
    level = request.GET.get('level')
    
    if dept_id:
        students = students.filter(department_id=dept_id)
    if level:
        students = students.filter(level=level)
        
    departments = Department.objects.all()
    academic_years = AcademicYear.objects.all()
    
    context = {
        'students': students,
        'departments': departments,
        'academic_years': academic_years,
        'level_choices': Student.LEVEL_CHOICES,
        'result_choices': StudentPromotion.RESULT_CHOICES,
        'title': 'ترحيل الطلاب',
    }
    return render(request, 'students/promotion_list.html', context)


@login_required
def add_student_note(request, pk):
    """Add a new note to a student"""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            note = StudentNote.objects.create(
                student=student,
                text=text,
                author=request.user.get_full_name() or request.user.username
            )
            SystemLog.objects.create(
                user=request.user,
                action='create',
                details=f"قام [{request.user.username}] بإضافة ملاحظة إدارية جديدة لملف الطالب: {student.short_name}"
            )
            messages.success(request, 'تم إضافة الملاحظة بنجاح')
        else:
            messages.error(request, 'لا يمكن إضافة ملاحظة فارغة')
    return redirect(reverse('student_detail', kwargs={'pk': pk}) + '#notesTab')


@login_required
def delete_student_note(request, pk):
    """Delete a student note"""
    note = get_object_or_404(StudentNote, pk=pk)
    student_pk = note.student.pk
    student_name = note.student.short_name
    note.delete()
    SystemLog.objects.create(
        user=request.user,
        action='delete',
        details=f"حذف ملاحظة للطالب: {student_name}"
    )
    messages.success(request, 'تم حذف الملاحظة بنجاح')
    return redirect(reverse('student_detail', kwargs={'pk': student_pk}) + '#notesTab')


@login_required
def delete_student_document(request, pk):
    """Delete a student document"""
    doc = get_object_or_404(StudentDocument, pk=pk)
    student_pk = doc.student.pk
    student_name = doc.student.short_name
    doc_title = doc.title
    doc.delete()
    SystemLog.objects.create(
        user=request.user,
        action='delete',
        details=f"حذف وثيقة '{doc_title}' للطالب: {student_name}"
    )
    messages.success(request, 'تم حذف الوثيقة بنجاح')
    return redirect(reverse('student_detail', kwargs={'pk': student_pk}) + '#docsTab')


def decode_zip_filename(zipinfo):
    """
    Decodes zipfile filename correctly with support for Arabic encodings.
    """
    filename_str = zipinfo.filename
    try:
        # zipfile decodes filenames in CP437. We encode back to get raw bytes.
        raw_bytes = filename_str.encode('cp437')
        return raw_bytes.decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        try:
            return raw_bytes.decode('cp1256')  # Arabic Windows encoding
        except Exception:
            return filename_str


def guess_doc_type(filename):
    filename_lower = filename.lower()
    if any(keyword in filename_lower for keyword in ['grad', 'graduation', 'تخرج', 'شهادة']):
        return 'graduation'
    elif any(keyword in filename_lower for keyword in ['trans', 'transcript', 'درجات', 'كشف', 'وثيقة']):
        return 'transcript'
    elif any(keyword in filename_lower for keyword in ['id', 'هوية', 'بطاقة', 'جنسية', 'هويه']):
        return 'id'
    elif any(keyword in filename_lower for keyword in ['medical', 'طبي', 'فحص', 'تقرير']):
        return 'medical'
    elif any(keyword in filename_lower for keyword in ['residence', 'سكن', 'بطاقة السكن']):
        return 'residence'
    elif any(keyword in filename_lower for keyword in ['discount', 'تخفيض']):
        return 'discount'
    return None


def find_matching_student(filename_clean):
    """
    Attempts to find a student whose:
    1. student_id matches a number in the filename
    2. exam_number matches a number in the filename
    3. full name (fuzzy search) matches the filename
    """
    import re
    from django.db.models import Q
    from students.models import Student
    
    # 1. Try exact student_id or exam_number from numbers in filename
    numbers = re.findall(r'\d+', filename_clean)
    for num in numbers:
        if len(num) >= 3:  # Ignore short numbers like 1, 2, etc.
            student = Student.objects.filter(Q(student_id=num) | Q(exam_number=num)).first()
            if student:
                return student
                
            student = Student.objects.filter(Q(student_id__icontains=num) | Q(exam_number__icontains=num)).first()
            if student:
                return student

    # 2. Try matching name
    cleaned_name = filename_clean
    # Remove common extension/doc words
    for word in ['graduation', 'transcript', 'medical', 'residence', 'discount', 'other', 'وثيقة', 'تخرج', 'كشف', 'هوية', 'طبي', 'سكن', 'تخفيض', 'درجات', 'شهادة', 'صورة', 'بطاقة', 'جنسية', 'ملف', 'طالب', 'pdf', 'jpg', 'png', 'jpeg']:
        cleaned_name = re.sub(word, '', cleaned_name, flags=re.IGNORECASE)
    
    cleaned_name = cleaned_name.strip('_ -')
    
    if len(cleaned_name) >= 3:
        # Split into parts
        parts = cleaned_name.split()
        if len(parts) >= 2:
            # Let's search using Q
            q = Q()
            for part in parts:
                if len(part) >= 2:
                    q &= (Q(first_name__icontains=part) | Q(second_name__icontains=part) | Q(third_name__icontains=part) | Q(last_name__icontains=part))
            student = Student.objects.filter(q).first()
            if student:
                return student
                
        # Try full string search
        student = Student.objects.filter(
            Q(first_name__icontains=cleaned_name) |
            Q(last_name__icontains=cleaned_name)
        ).first()
        if student:
            return student
            
    return None


@login_required
def batch_upload_documents(request):
    if not request.user.is_superuser:
        messages.error(request, 'عذراً، هذه الصفحة مخصصة لمدير النظام فقط!')
        return redirect('dashboard')

    import zipfile
    import uuid
    import os
    import shutil
    from django.conf import settings
    from django.db.models import Q
    from students.models import Student, StudentDocument

    if request.method == 'POST' and request.FILES.get('zip_file'):
        zip_file = request.FILES['zip_file']
        fallback_doc_type = request.POST.get('fallback_doc_type', 'other')
        batch_notes = request.POST.get('batch_notes', '')

        # Generate a unique session ID and temporary extraction path
        upload_session_id = str(uuid.uuid4())
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_batch_uploads', upload_session_id)
        os.makedirs(temp_dir, exist_ok=True)

        # Extract ZIP file
        files_data = []
        try:
            with zipfile.ZipFile(zip_file) as zf:
                for zip_info in zf.infolist():
                    # Skip directories
                    if zip_info.is_dir():
                        continue
                    
                    # Skip metadata files (like __MACOSX or .DS_Store)
                    if '__MACOSX' in zip_info.filename or zip_info.filename.split('/')[-1].startswith('.'):
                        continue
                    
                    # Clean/decode zip filename
                    filename = decode_zip_filename(zip_info)
                    basename = os.path.basename(filename)
                    if not basename:
                        continue
                    
                    # Check allowed extension (e.g. pdf, jpg, jpeg, png, doc, docx)
                    ext = basename.split('.')[-1].lower()
                    if ext not in ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']:
                        continue
                    
                    # Generate a unique temp name to prevent collisions but keep track of original basename
                    temp_filename = f"{uuid.uuid4().hex}.{ext}"
                    temp_filepath = os.path.join(temp_dir, temp_filename)
                    
                    # Write extracted file
                    with open(temp_filepath, 'wb') as f:
                        f.write(zf.read(zip_info))
                    
                    # Clean filename for matching
                    filename_clean, _ = os.path.splitext(basename)
                    
                    # Match student
                    matched_student = find_matching_student(filename_clean)
                    
                    # Guess document type
                    guessed_type = guess_doc_type(filename_clean) or fallback_doc_type
                    
                    # Document title
                    doc_title = filename_clean.replace('_', ' ').replace('-', ' ').strip()
                    
                    files_data.append({
                        'temp_filename': temp_filename,
                        'original_name': basename,
                        'matched_student_id': matched_student.id if matched_student else '',
                        'matched_student_name': matched_student.short_name if matched_student else '',
                        'matched_student_uid': matched_student.student_id if matched_student else '',
                        'guessed_type': guessed_type,
                        'doc_title': doc_title,
                    })
        except Exception as e:
            # Clean up if failed
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            messages.error(request, f'خطأ أثناء معالجة ملف ZIP: {str(e)}')
            return redirect('batch_upload_documents')

        if not files_data:
            # Clean up empty dir
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            messages.warning(request, 'لم يتم العثور على أي ملفات صالحة (صور أو مستندات PDF) داخل ملف ZIP.')
            return redirect('batch_upload_documents')

        # Store critical parameters in session
        request.session['batch_upload_session'] = upload_session_id
        request.session['batch_notes'] = batch_notes

        # Get list of all students for the dropdown search in review table
        all_students = list(Student.objects.all().order_by('first_name'))
        
        context = {
            'title': 'مراجعة ومطابقة الوثائق بالدفعة',
            'step': 2,
            'files_data': files_data,
            'all_students': all_students,
            'DOC_TYPE_CHOICES': StudentDocument.DOC_TYPE_CHOICES,
            'upload_session_id': upload_session_id,
        }
        return render(request, 'students/batch_upload_documents.html', context)

    # GET request: render upload page (Step 1)
    context = {
        'title': 'رفع وثائق الطلاب بالدفعة',
        'step': 1,
        'DOC_TYPE_CHOICES': StudentDocument.DOC_TYPE_CHOICES,
    }
    return render(request, 'students/batch_upload_documents.html', context)


@login_required
def confirm_batch_upload(request):
    if not request.user.is_superuser:
        messages.error(request, 'عذراً، هذه الصفحة مخصصة لمدير النظام فقط!')
        return redirect('dashboard')

    import os
    import shutil
    from django.conf import settings
    from students.models import Student, StudentDocument
    from core.models import SystemLog

    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        session_id_stored = request.session.get('batch_upload_session')

        if not session_id or session_id != session_id_stored:
            messages.error(request, 'جلسة رفع غير صالحة أو منتهية الصلاحية.')
            return redirect('batch_upload_documents')

        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_batch_uploads', session_id)
        if not os.path.exists(temp_dir):
            messages.error(request, 'لم يتم العثور على الملفات المؤقتة. يرجى إعادة المحاولة.')
            return redirect('batch_upload_documents')

        temp_files = os.listdir(temp_dir)
        import_count = 0
        skipped_count = 0

        for temp_filename in temp_files:
            # Check if included
            is_included = request.POST.get(f'include_{temp_filename}') == 'on'
            student_pk = request.POST.get(f'student_{temp_filename}')
            doc_type = request.POST.get(f'doc_type_{temp_filename}')
            title = request.POST.get(f'title_{temp_filename}')
            
            if not is_included or not student_pk:
                skipped_count += 1
                continue

            try:
                student = Student.objects.get(pk=student_pk)
                temp_filepath = os.path.join(temp_dir, temp_filename)
                
                with open(temp_filepath, 'rb') as f:
                    doc = StudentDocument(
                        student=student,
                        doc_type=doc_type,
                        title=title or temp_filename,
                        notes=request.session.get('batch_notes', '')
                    )
                    from django.core.files import File
                    doc.file.save(temp_filename, File(f), save=True)
                
                import_count += 1
            except Exception as e:
                skipped_count += 1
                continue

        # Clean up temp folder completely
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

        # Clear session
        if 'batch_upload_session' in request.session:
            del request.session['batch_upload_session']
        if 'batch_notes' in request.session:
            del request.session['batch_notes']

        # Log system action
        full_user_name = request.user.get_full_name() or request.user.username
        SystemLog.objects.create(
            user=request.user,
            action='create',
            details=f"قام [{full_user_name}] برفع مستندات للطلاب بالدفعة (استيراد ناجح: {import_count}، متجاوز: {skipped_count})"
        )

        messages.success(request, f'تم إكمال استيراد المستندات بالدفعة بنجاح! تم حفظ ({import_count}) وثيقة، وتخطي ({skipped_count}) وثيقة.')
        return redirect('student_list')

    return redirect('batch_upload_documents')


from .whatsapp_utils import generate_whatsapp_link

@login_required
def student_whatsapp_redirect(request, pk):
    """Generate WhatsApp link for a student based on action"""
    student = get_object_or_404(Student, pk=pk)
    action = request.GET.get('action')
    
    # Try student phone first, then guardian phone
    phone = student.phone
    if not phone:
        phone = student.guardian_phone
        
    if not phone:
        messages.error(request, 'لا يوجد رقم هاتف مسجل لهذا الطالب.')
        return redirect('student_detail', pk=pk)
        
    message = ""
    if action == 'admission':
        message = f"عزيزي الطالب {student.first_name} {student.last_name}،\nنود إعلامك بأنه تم قبولك في قسم ({student.department.name}).\nرقمك الجامعي هو: {student.student_id}\n\nيرجى مراجعة القسم لإكمال إجراءات المباشرة.\nنتمنى لك عاماً دراسياً موفقاً."
    elif action == 'missing_docs':
        message = f"عزيزي الطالب {student.first_name} {student.last_name}،\nيرجى مراجعة قسم التسجيل لاستكمال الوثائق الناقصة في ملفك بأقرب وقت ممكن.\n\nقسم التسجيل."
    elif action == 'attendance':
        message = f"عزيزي الطالب {student.first_name} {student.last_name}،\nتم تسجيل مباشرتك بالدوام بنجاح.\n\nمع التحية."
    elif action == 'send_docs':
        docs = student.documents.all()
        if not docs.exists():
            messages.warning(request, 'لا توجد وثائق مرفوعة لهذا الطالب لإرسالها.')
            return redirect('student_detail', pk=pk)
        
        message = f"عزيزي الطالب {student.first_name} {student.last_name}،\nمرفق روابط الوثائق الخاصة بك:\n\n"
        for doc in docs:
            doc_url = request.build_absolute_uri(doc.file.url)
            message += f"- {doc.title}:\n{doc_url}\n\n"
        message += "مع التحية."
        
    link = generate_whatsapp_link(phone, message)
    return redirect(link)


@login_required
@staff_member_required
def student_import_export(request):
    if not request.user.is_superuser:
        messages.error(request, 'عذراً، هذه الصفحة مخصصة لمدير النظام فقط!')
        return redirect('dashboard')
    import uuid
    import re
    resource = StudentResource()
    formats = {
        'xlsx': XLSX(),
        'csv': CSV(),
    }
    
    # Declare expected fields dynamically from StudentResource
    mappable_fields = []
    for field_name, field in resource.fields.items():
        if field.attribute and field_name != 'student_id':
            mappable_fields.append((field.attribute, field.column_name))
            
    # Sort alphabetically by column name
    mappable_fields.sort(key=lambda x: x[1])
    
    step = 1
    file_headers = []
    preview_rows = []
    stats = {}
    import_error = None
    
    # Check temp directory exists
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_imports')
    os.makedirs(temp_dir, exist_ok=True)
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        # --- EXPORT ACTION ---
        if action == 'export':
            file_format = request.POST.get('format', 'xlsx')
            fmt = formats.get(file_format, XLSX())
            dataset = resource.export()
            export_data = fmt.export_data(dataset)
            response = HttpResponse(export_data, content_type=fmt.get_content_type())
            response['Content-Disposition'] = f'attachment; filename="students_export.{file_format}"'
            return response
            
        # --- UPLOAD ACTION (STEP 1) ---
        elif action == 'import_upload':
            import_file = request.FILES.get('import_file')
            if not import_file:
                messages.error(request, 'يرجى اختيار ملف للاستيراد')
            else:
                file_ext = os.path.splitext(import_file.name)[1][1:].lower()
                if file_ext not in ['xlsx', 'csv']:
                    messages.error(request, 'صيغة الملف غير مدعومة. يرجى رفع ملف Excel (xlsx) أو CSV')
                else:
                    # Save file to temp folder
                    temp_filename = f"{uuid.uuid4().hex}.{file_ext}"
                    temp_filepath = os.path.join(temp_dir, temp_filename)
                    with open(temp_filepath, 'wb') as f:
                        for chunk in import_file.chunks():
                            f.write(chunk)
                            
                    # Load headers using tablib
                    try:
                        dataset = tablib.Dataset()
                        with open(temp_filepath, 'rb') as f:
                            data_bytes = f.read()
                        if file_ext == 'csv':
                            dataset.load(data_bytes.decode('utf-8-sig', errors='ignore'), format='csv')
                        else:
                            dataset.load(data_bytes, format='xlsx')
                            
                        # Save details in session
                        request.session['import_temp_file'] = temp_filename
                        request.session['import_file_ext'] = file_ext
                        
                        file_headers = dataset.headers
                        
                        # Match uploaded columns fuzzy-style to expected fields as defaults
                        synonyms = {
                            'first_name': ['الاسم الأول', 'الاسم الاول', 'الاسم', 'اسم الطالب', 'الاسم الكامل', 'الاسم الثلاثي', 'اسم الطالب الثلاثي', 'الاسم الرباعي', 'الاسم الكامل للطالب', 'name', 'full name', 'first name', 'student name'],
                            'second_name': ['اسم الأب', 'اسم الاب', 'الأب', 'الاب', 'father', 'father name', 'second name'],
                            'third_name': ['اسم الجد', 'الجد', 'grandfather', 'third name'],
                            'last_name': ['الاسم الرابع', 'الاسم الاخير', 'الاسم الأخير', 'last name', 'fourth name'],
                            'surname': ['اللقب', 'العشيرة', 'العشيره', 'surname', 'family name'],
                            'mother_name': ['اسم الأم', 'اسم الام', 'اسم الأم الثلاثي', 'اسم الام الثلاثي', 'الأم', 'الام', 'mother', 'mother name'],
                            'national_id': ['رقم الهوية', 'رقم الهويه', 'الهوية', 'الهويه', 'الجواز', 'رقم الجواز', 'رقم الهوية/الجواز', 'رقم الهويه/الجواز', 'national id', 'passport', 'id number'],
                            'exam_number': ['الرقم الامتحاني', 'رقم الامتحان', 'الامتحاني', 'exam number'],
                            'date_of_birth': ['تاريخ الميلاد', 'التولد', 'تاريخ الولادة', 'تاريخ الولاده', 'تولد', 'date of birth', 'dob', 'birth date'],
                            'gender': ['الجنس', 'نوع', 'gender', 'sex'],
                            'religion': ['الديانة', 'الديانه', 'religion'],
                            'marital_status': ['الحالة الزوجية', 'الحاله الزوجيه', 'الحالة الاجتماعية', 'الحاله الاجتماعيه', 'الزوجية', 'الزوجيه', 'marital status'],
                            'health_status': ['الحالة الصحية', 'الحاله الصحيه', 'الصحة', 'الصحه', 'health status'],
                            'governorate': ['المحافظة', 'المحافظه', 'governorate', 'province'],
                            'address': ['العنوان', 'السكن', 'محل السكن', 'عنوان السكن', 'address'],
                            'ethnicity': ['القومية', 'القوميه', 'ethnicity'],
                            'birth_place': ['مكان الولادة', 'مكان الولاده', 'مكان الميلاد', 'محل الولادة', 'محل الولاده', 'birth place'],
                            'school_name': ['المدرسة', 'المدرسه', 'المدارس', 'اسم المدرسة', 'اسم المدرسه', 'school'],
                            'branch': ['الفرع', 'فرع الدراسة', 'فرع الدراسه', 'branch'],
                            'specialization': ['التخصص', 'الاختصاص', 'specialization'],
                            'admission_channel': ['قناة القبول', 'قناه القبول', 'قناة التقديم', 'قناه التقديم', 'القبول', 'admission channel'],
                            'institute': ['المعهد', 'الكلية', 'الكليه', 'الجامعة', 'الجامعه', 'institute', 'college', 'university'],
                            'registration_code': ['رمز التسجيل', 'كود التسجيل', 'registration code'],
                            'receipt_number': ['رقم الوصل', 'الوصل', 'receipt number'],
                            'archive_locker': ['دولاب الأرشيف', 'دولاب الارشيف', 'الأرشيف', 'الارشيف', 'الموقع', 'archive'],
                            'department': ['القسم', 'القسم العلمي', 'قسم', 'department'],
                            'entry_year': ['سنة القبول', 'سنه القبول', 'العام الدراسي', 'العام الدراسى', 'entry year', 'academic year'],
                            'phone': ['الهاتف', 'رقم الهاتف', 'رقم الجوال', 'الموبايل', 'رقم الموبايل', 'الجوال', 'تلفون', 'phone', 'mobile'],
                            'citizenship': ['الجنسية', 'الجنسيه', 'المواطنة', 'المواطنه', 'التابع', 'citizenship', 'nationality'],
                            'gpa': ['المعدل', 'المعدل التراكمي', 'معدل التخرج', 'معدل السادس', 'المجموع', 'gpa', 'average', 'grade'],
                        }
                        
                        column_matches = {}
                        for col in file_headers:
                            col_clean = col.strip().lower()
                            best_match = ''
                            
                            # 1. Exact match in synonyms options
                            for attr, options in synonyms.items():
                                if any(opt.strip().lower() == col_clean for opt in options):
                                    best_match = attr
                                    break
                                    
                            # 2. Substring match fallback
                            if not best_match:
                                for attr, options in synonyms.items():
                                    if any((opt.strip().lower() in col_clean) or (col_clean in opt.strip().lower()) for opt in options if len(opt) > 3):
                                        best_match = attr
                                        break
                                        
                            # 3. Last fallback: check mappable_fields original names
                            if not best_match:
                                for attr, col_name in mappable_fields:
                                    if col_clean == col_name.strip().lower() or col_clean == attr.lower():
                                        best_match = attr
                                        break
                                        
                            column_matches[col] = best_match
                            
                        request.session['import_column_matches'] = column_matches
                        step = 2
                    except Exception as e:
                        if os.path.exists(temp_filepath):
                            os.remove(temp_filepath)
                        messages.error(request, f'فشل في قراءة الملف: {str(e)}')
                        
        # --- MAPPING ACTION (STEP 2) ---
        elif action == 'import_map':
            temp_filename = request.session.get('import_temp_file')
            file_ext = request.session.get('import_file_ext')
            if not temp_filename:
                messages.error(request, 'انتهت صلاحية جلسة الاستيراد. يرجى رفع الملف مرة أخرى.')
                return redirect('student_import_export')
                
            temp_filepath = os.path.join(temp_dir, temp_filename)
            try:
                # Read file
                dataset = tablib.Dataset()
                with open(temp_filepath, 'rb') as f:
                    data_bytes = f.read()
                if file_ext == 'csv':
                    dataset.load(data_bytes.decode('utf-8-sig', errors='ignore'), format='csv')
                else:
                    dataset.load(data_bytes, format='xlsx')
                    
                # Reconstruct mapping dict
                # key: Excel Header, value: System field attribute name
                column_mapping = {}
                for col in dataset.headers:
                    mapped_attr = request.POST.get(f'map_{col}', '')
                    if mapped_attr:
                        column_mapping[col] = mapped_attr
                        
                # Save mapping to session
                request.session['import_mapping'] = column_mapping
                
                # Perform cleaning and validation for preview
                new_dataset = tablib.Dataset()
                reverse_mappable = {attr: col_name for attr, col_name in mappable_fields}
                
                # Build target headers
                target_headers = []
                for col in dataset.headers:
                    attr = column_mapping.get(col)
                    if attr and attr in reverse_mappable:
                        target_headers.append(reverse_mappable[attr])
                    else:
                        target_headers.append(col)
                        
                new_dataset.headers = target_headers
                for row in dataset:
                    new_dataset.append(row)
                    
                # Store mapped dataset
                mapped_filename = f"mapped_{temp_filename}"
                mapped_filepath = os.path.join(temp_dir, mapped_filename)
                with open(mapped_filepath, 'wb') as f:
                    f.write(new_dataset.export(file_ext))
                request.session['import_mapped_file'] = mapped_filename
                
                # Preview rows
                preview_rows = []
                new_count = 0
                update_count = 0
                error_count = 0
                
                for idx, row in enumerate(new_dataset, 1):
                    row_dict = {}
                    for col in dataset.headers:
                        attr = column_mapping.get(col)
                        if attr:
                            val = row[dataset.headers.index(col)]
                            row_dict[attr] = val
                            
                    cleaned_dict, row_errors = clean_and_validate_row(row_dict, idx)
                    
                    nat_id = cleaned_dict.get('national_id')
                    is_update = False
                    if nat_id:
                        is_update = Student.objects.filter(national_id=nat_id).exists()
                        
                    status = 'error' if row_errors else ('update' if is_update else 'new')
                    if status == 'new': new_count += 1
                    elif status == 'update': update_count += 1
                    else: error_count += 1
                    
                    preview_rows.append({
                        'index': idx,
                        'original': dict(zip(dataset.headers, row)),
                        'cleaned': cleaned_dict,
                        'status': status,
                        'errors': row_errors,
                    })
                    
                stats = {
                    'total': len(new_dataset),
                    'new': new_count,
                    'update': update_count,
                    'error': error_count,
                }
                
                request.session['import_stats'] = stats
                step = 3
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء معالجة المطابقة: {str(e)}')
                step = 2
                
        # --- CONFIRM ACTION (STEP 3) ---
        elif action == 'import_confirm':
            mapped_filename = request.session.get('import_mapped_file')
            file_ext = request.session.get('import_file_ext')
            column_mapping = request.session.get('import_mapping')
            skip_errors = request.POST.get('skip_errors') == 'on'
            
            if not mapped_filename or not file_ext or not column_mapping:
                messages.error(request, 'انتهت صلاحية جلسة الاستيراد. يرجى رفع الملف مرة أخرى.')
                return redirect('student_import_export')
                
            mapped_filepath = os.path.join(temp_dir, mapped_filename)
            try:
                dataset = tablib.Dataset()
                with open(mapped_filepath, 'rb') as f:
                    data_bytes = f.read()
                if file_ext == 'csv':
                    dataset.load(data_bytes.decode('utf-8-sig', errors='ignore'), format='csv')
                else:
                    dataset.load(data_bytes, format='xlsx')
                    
                from django.db import transaction
                import_count = 0
                update_count = 0
                skipped_count = 0
                
                with transaction.atomic():
                    for idx, row in enumerate(dataset, 1):
                        row_dict = {}
                        for col in dataset.headers:
                            for attr, col_name in mappable_fields:
                                if col_name == col:
                                    row_dict[attr] = row[dataset.headers.index(col)]
                                    break
                                    
                        cleaned_dict, row_errors = clean_and_validate_row(row_dict, idx)
                        
                        if row_errors:
                            if skip_errors:
                                skipped_count += 1
                                continue
                            else:
                                raise Exception(f"السطر {idx}: {row_errors[0]}")
                                
                        dept_name = cleaned_dict.get('department')
                        dept = None
                        if dept_name:
                            dept = normalize_department(dept_name, auto_create=True)
                        if not dept:
                            dept = Department.objects.first()
                            
                        year_val = cleaned_dict.get('entry_year')
                        entry_year = None
                        if year_val:
                            entry_year = normalize_academic_year(year_val, auto_create=True)
                        if not entry_year:
                            entry_year = AcademicYear.objects.first()
                            
                        nat_id = cleaned_dict.get('national_id')
                        student = Student.objects.filter(national_id=nat_id).first()
                        
                        student_data = cleaned_dict.copy()
                        if 'department' in student_data: del student_data['department']
                        if 'entry_year' in student_data: del student_data['entry_year']
                        
                        if student:
                            for k, v in student_data.items():
                                if v is not None:
                                    setattr(student, k, v)
                            if dept: student.department = dept
                            if entry_year: student.entry_year = entry_year
                            student.save()
                            update_count += 1
                        else:
                            student = Student(**student_data)
                            if dept: student.department = dept
                            if entry_year: student.entry_year = entry_year
                            if not student.status: student.status = 'active'
                            if not student.level: student.level = '1'
                            if not student.study_type: student.study_type = 'morning'
                            student.save()
                            import_count += 1
                            
                cleanup_import_temp_files(request, temp_dir)
                clear_import_session_vars(request)
                
                messages.success(request, f'تم استيراد الطلاب بنجاح! تم إضافة {import_count} طلاب جدد، وتحديث {update_count} طلاب، وتخطي {skipped_count} سجلات تحتوي على أخطاء.')
                return redirect('student_list')
                
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حفظ البيانات: {str(e)}')
                step = 3
                
    else:
        cleanup_import_temp_files(request, temp_dir)
        clear_import_session_vars(request)
        
    context = {
        'title': 'استيراد وتصدير الطلاب',
        'step': step,
        'mappable_fields': mappable_fields,
        'file_headers': request.session.get('import_column_matches', {}).keys() if step == 2 else file_headers,
        'column_matches': request.session.get('import_column_matches', {}) if step == 2 else {},
        'preview_rows': preview_rows[:20],
        'stats': stats,
        'import_error': import_error,
    }
    return render(request, 'students/import_export.html', context)


def normalize_department(dept_str, auto_create=False):
    import re
    if not dept_str:
        return None
    dept_str = str(dept_str).strip()
    
    # 1. Try exact match
    d = Department.objects.filter(name__iexact=dept_str).first()
    if d:
        return d
        
    # Helper to clean Arabic text for normalization
    def clean_text(text):
        if not text:
            return ""
        # Normalize Alif variants
        text = re.sub(r'[أإآا]', 'ا', text)
        # Normalize Ta Marbuta
        text = re.sub(r'ة', 'ه', text)
        # Normalize Ya/Alef Maksura
        text = re.sub(r'[ىي]', 'ي', text)
        # Remove spacing and split
        words = text.split()
        cleaned_words = []
        for w in words:
            if w.startswith('ال') and len(w) > 3:
                w = w[2:]
            cleaned_words.append(w)
        if cleaned_words and cleaned_words[0] == 'قسم':
            cleaned_words = cleaned_words[1:]
        return "".join(cleaned_words)
        
    cleaned_dept = clean_text(dept_str)
    if not cleaned_dept:
        return None
        
    # 2. Try match after cleaning
    for d in Department.objects.all():
        if clean_text(d.name) == cleaned_dept:
            return d
            
    # 3. Try fallback substring match
    for d in Department.objects.all():
        db_clean = clean_text(d.name)
        if cleaned_dept in db_clean or db_clean in cleaned_dept:
            return d
            
    # 4. Auto-create if requested
    if auto_create:
        # Generate a unique code based on the department name
        words = [w for w in dept_str.replace('قسم', '').split() if w]
        code_prefix = "".join(w[0] for w in words)[:5].upper()
        if not code_prefix:
            code_prefix = "DEPT"
            
        # Ensure code is unique in DB
        code = code_prefix
        counter = 1
        while Department.objects.filter(code=code).exists():
            code = f"{code_prefix}_{counter}"
            counter += 1
            
        d = Department.objects.create(
            name=dept_str,
            code=code,
            description="تم إنشاؤه تلقائياً أثناء استيراد البيانات"
        )
        return d
        
    return None


def normalize_academic_year(year_str, auto_create=False):
    import re
    if not year_str:
        return None
    year_str = str(year_str).strip()
    y = AcademicYear.objects.filter(year=year_str).first()
    if y:
        return y
    digits = re.findall(r'\d{4}', year_str)
    if digits:
        # If there are two years, e.g. 2025 and 2026
        if len(digits) >= 2:
            start_yr, end_yr = digits[0], digits[1]
            y = AcademicYear.objects.filter(year__icontains=start_yr).filter(year__icontains=end_yr).first()
            if y:
                return y
        else:
            # Only one year digit (e.g. "2025") - match starts with 2025
            y = AcademicYear.objects.filter(year__startswith=digits[0]).first()
            if y:
                return y
            y = AcademicYear.objects.filter(year__icontains=digits[0]).first()
            if y:
                return y
                
        # Auto-create if requested
        if auto_create:
            start_year = int(digits[0])
            if len(digits) >= 2:
                formatted_year = f"{digits[0]}/{digits[1]}"
                end_year = int(digits[1])
            else:
                formatted_year = f"{start_year}/{start_year + 1}"
                end_year = start_year + 1
                
            # Check if this formatted year exists
            y = AcademicYear.objects.filter(year=formatted_year).first()
            if y:
                return y
                
            y = AcademicYear.objects.create(
                year=formatted_year,
                start_date=f"{start_year}-09-01",
                end_date=f"{end_year}-06-30",
                is_active=False
            )
            return y
            
    return None
def split_arabic_name(full_name_str):
    """
    Splits an Arabic full name string into parts, taking into account
    common compound names and prefixes/suffixes.
    """
    if not full_name_str:
        return []
        
    # Clean the string from extra spaces, normalizing spacing
    words = [w for w in full_name_str.strip().split() if w]
    
    always_merge = {
        'عبد', 'ابو', 'أبو', 'ام', 'أم', 'بن', 'ابن', 'بنت', 'آل', 'ذو', 'امة', 'أمة', 
        'محي', 'محيي', 'تقي', 'زين'
    }
    cond_prefixes = {
        'نور', 'شمس', 'بهاء', 'علاء', 'سيف', 'جمال', 'جلال', 'صلاح', 'عماد', 'فخر', 
        'شهاب', 'تاج', 'نجم', 'شرف', 'صدر', 'سعد', 'ضياء', 'غياث', 'ولي', 'شجاع', 
        'غوث', 'قطب'
    }
    suffixes = {'الدين', 'الله', 'الهدى', 'الاسلام', 'الإسلام', 'الرحمن', 'العابدين'}
    
    i = 0
    merged_words = []
    while i < len(words):
        current = words[i]
        
        # Check if we can merge with the next word
        if i + 1 < len(words):
            next_word = words[i+1]
            
            # 1. Check for always merge prefixes
            if current in always_merge:
                merged_words.append(f"{current} {next_word}")
                i += 2
                continue
                
            # 2. Check for conditional prefixes with suffixes
            if current in cond_prefixes and next_word in suffixes:
                merged_words.append(f"{current} {next_word}")
                i += 2
                continue
                
            # 3. Check if next word is a suffix that merges back
            if next_word in suffixes:
                merged_words.append(f"{current} {next_word}")
                i += 2
                continue
                
            # 4. Check for common compound names in Iraq
            is_compound_first_word = (
                (current == 'محمد' and next_word in {'باقر', 'جواد', 'صادق', 'مهدي', 'هادي', 'تقي', 'رضا', 'امين', 'أمين', 'سعيد', 'شريف', 'حسن', 'حسين', 'المهدي'}) or
                (current == 'علي' and next_word in {'رضا', 'هادي', 'سجاد', 'اكبر', 'أكبر', 'اصغر', 'أصغر', 'الرضا'}) or
                (current in {'فاطمة', 'فاطمه'} and next_word == 'الزهراء')
            )
            if is_compound_first_word:
                merged_words.append(f"{current} {next_word}")
                i += 2
                continue
                
        merged_words.append(current)
        i += 1
        
    return merged_words


def clean_and_validate_row(row_dict, idx):
    import re
    errors = []
    cleaned = {}
    
    # 1. Clean National ID (required)
    nat_id = str(row_dict.get('national_id') or '').strip()
    if not nat_id or nat_id.lower() == 'none' or nat_id == '':
        errors.append("رقم الهوية/الجواز حقل مطلوب للتعرف على الطالب.")
    else:
        if nat_id.endswith('.0'):
            nat_id = nat_id[:-2]
        cleaned['national_id'] = nat_id
        
    # 2. Clean Name fields
    first_name = str(row_dict.get('first_name') or '').strip()
    second_name = str(row_dict.get('second_name') or '').strip()
    third_name = str(row_dict.get('third_name') or '').strip()
    
    # Check if first_name looks like a full name and other name parts are missing
    if first_name and first_name.lower() != 'none' and (not second_name or second_name.lower() == 'none' or second_name == ''):
        name_parts = split_arabic_name(first_name)
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            second_name = name_parts[1]
            if len(name_parts) >= 3:
                third_name = name_parts[2]
                if len(name_parts) > 3:
                    # Append remaining parts to last name
                    row_last = str(row_dict.get('last_name') or '').strip()
                    if row_last and row_last.lower() != 'none':
                        last_name = " ".join(name_parts[3:]) + " " + row_last
                    else:
                        last_name = " ".join(name_parts[3:])
                else:
                    last_name = str(row_dict.get('last_name') or '').strip()
            else:
                last_name = str(row_dict.get('last_name') or '').strip()
        else:
            last_name = str(row_dict.get('last_name') or '').strip()
    else:
        last_name = str(row_dict.get('last_name') or '').strip()

    if not first_name or first_name.lower() == 'none' or first_name == '':
        errors.append("الاسم الأول حقل مطلوب.")
    else:
        cleaned['first_name'] = first_name
        
    if not second_name or second_name.lower() == 'none' or second_name == '':
        errors.append("اسم الأب حقل مطلوب.")
    else:
        cleaned['second_name'] = second_name
        
    if not third_name or third_name.lower() == 'none' or third_name == '':
        errors.append("اسم الجد حقل مطلوب.")
    else:
        cleaned['third_name'] = third_name
        
    cleaned['last_name'] = last_name
    cleaned['surname'] = str(row_dict.get('surname') or '').strip()
    cleaned['mother_name'] = str(row_dict.get('mother_name') or '').strip()
    
    # 3. Clean Gender
    gender_val = str(row_dict.get('gender') or '').strip().lower()
    if gender_val and gender_val != 'none':
        if any(x in gender_val for x in ['ذكر', 'ولد', 'طالب', 'male']):
            cleaned['gender'] = 'male'
        elif any(x in gender_val for x in ['أنث', 'انث', 'بنت', 'طالبة', 'female']):
            cleaned['gender'] = 'female'
        else:
            errors.append(f"الجنس غير صالح: '{gender_val}' (يجب أن يكون ذكر أو أنثى).")
    else:
        cleaned['gender'] = 'male'
        
    # 4. Clean Date of Birth
    dob = row_dict.get('date_of_birth')
    if dob and str(dob).strip().lower() != 'none':
        try:
            if hasattr(dob, 'strftime'):
                cleaned['date_of_birth'] = dob.strftime('%Y-%m-%d')
            else:
                d_str = str(dob).strip()
                if d_str.endswith('.0'):
                    d_str = d_str[:-2]
                if d_str.isdigit() and len(d_str) == 4:
                    cleaned['date_of_birth'] = f"{d_str}-01-01"
                else:
                    import dateutil.parser
                    parsed_date = dateutil.parser.parse(d_str)
                    cleaned['date_of_birth'] = parsed_date.strftime('%Y-%m-%d')
        except Exception:
            errors.append(f"تاريخ الميلاد غير صالح أو صيغته غير معروفة: '{dob}'")
    else:
        cleaned['date_of_birth'] = '2000-01-01'
        
    # 5. GPA/Average
    gpa = row_dict.get('gpa') or row_dict.get('admission_avg') or row_dict.get('avg_no_additions')
    if gpa and str(gpa).strip().lower() != 'none':
        try:
            cleaned['gpa'] = float(str(gpa).replace(',', '.'))
        except ValueError:
            errors.append(f"المعدل أو المعدل التراكمي غير صالح: '{gpa}'")
            
    # 6. Phone number
    phone = str(row_dict.get('phone') or '').strip()
    if phone and phone.lower() != 'none':
        if phone.endswith('.0'):
            phone = phone[:-2]
        cleaned_phone = re.sub(r'\D', '', phone)
        if len(cleaned_phone) == 11:
            cleaned['phone'] = cleaned_phone
        else:
            cleaned['phone'] = phone
            
    # Clean Citizenship
    citizenship_val = str(row_dict.get('citizenship') or '').strip()
    if citizenship_val and citizenship_val.lower() != 'none':
        if 'عراق' in citizenship_val:
            cleaned['citizenship'] = 'عراقي'
        elif any(x in citizenship_val for x in ['اجنب', 'أجنب', 'foreign', 'أخرى', 'اخري']):
            cleaned['citizenship'] = 'أجنبي'
        else:
            cleaned['citizenship'] = citizenship_val
    else:
        cleaned['citizenship'] = ''
            
    # Other standard fields
    fields_list = ['governorate', 'address', 'religion', 'ethnicity', 'birth_place', 
                   'marital_status', 'health_status', 'origin_status', 
                   'school_name', 'branch', 'specialization', 'admission_channel', 
                   'institute', 'registration_code', 'receipt_number', 'archive_locker',
                   'notes']
    for field in fields_list:
        val = row_dict.get(field)
        if val is not None and str(val).strip().lower() != 'none':
            val_str = str(val).strip()
            if val_str.endswith('.0') and val_str[:-2].isdigit():
                val_str = val_str[:-2]
            cleaned[field] = val_str
        else:
            cleaned[field] = ''
            
    cleaned['department'] = str(row_dict.get('department') or '').strip()
    cleaned['entry_year'] = str(row_dict.get('entry_year') or '').strip()
    
    if cleaned['department']:
        dept = normalize_department(cleaned['department'], auto_create=True)
        if not dept:
            errors.append(f"القسم العلمي غير مسجل بالنظام: '{cleaned['department']}'")
            
    if cleaned['entry_year']:
        year = normalize_academic_year(cleaned['entry_year'], auto_create=True)
        if not year:
            errors.append(f"سنة القبول غير مسجلة بالنظام: '{cleaned['entry_year']}'")
            
    return cleaned, errors


def cleanup_import_temp_files(request, temp_dir):
    import os
    # Clean up specific session files
    for key in ['import_temp_file', 'import_mapped_file']:
        filename = request.session.get(key)
        if filename:
            filepath = os.path.join(temp_dir, filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass


def clear_import_session_vars(request):
    for var in ['import_temp_file', 'import_file_ext', 'import_mapping', 'import_mapped_file', 'import_stats', 'import_column_matches']:
        if var in request.session:
            del request.session[var]


@login_required
@permission_required('students.change_student', raise_exception=True)
def bulk_update_documents(request):
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        doc_field = request.POST.get('bulk_doc_field')
        doc_status = request.POST.get('bulk_doc_status')
        
        valid_fields = [
            'doc_national_id_student', 'doc_national_id_father', 'doc_national_id_mother',
            'doc_death_certificate', 'doc_residence_card', 'doc_personal_photos',
            'doc_sponsor', 'doc_medical_exam', 'doc_grade_confirmation'
        ]
        
        if not student_ids:
            messages.error(request, 'لم يتم تحديد أي طلاب لتحديث بياناتهم.')
            return redirect(reverse('student_list') + '?' + request.GET.urlencode())
            
        if doc_field not in valid_fields or doc_status not in ['true', 'false']:
            messages.error(request, 'الإجراء أو الحقل المحدد غير صالح.')
            return redirect(reverse('student_list') + '?' + request.GET.urlencode())
            
        status_bool = (doc_status == 'true')
        
        # Bulk update in DB
        updated_count = Student.objects.filter(id__in=student_ids).update(**{doc_field: status_bool})
        
        # System Log
        full_user_name = request.user.get_full_name() or request.user.username
        doc_verbose = Student._meta.get_field(doc_field).verbose_name
        status_verbose = "موجودة" if status_bool else "غير موجودة"
        SystemLog.objects.create(
            user=request.user,
            action='update',
            details=f"قام [{full_user_name}] بتحديث جماعي لحقل ({doc_verbose}) ليصبح ({status_verbose}) لـ {updated_count} طلاب."
        )
        
        messages.success(request, f'تم تحديث حقل "{doc_verbose}" بنجاح ليصبح ({status_verbose}) لـ {updated_count} طلاب.')
        
    return redirect(reverse('student_list') + '?' + request.GET.urlencode())


@login_required
@permission_required('students.delete_student', raise_exception=True)
def bulk_delete_students(request):
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        
        if not student_ids:
            messages.error(request, 'لم يتم تحديد أي طلاب لحذفهم.')
            return redirect(reverse('student_list') + '?' + request.GET.urlencode())
            
        # Select and delete
        students_to_delete = Student.objects.filter(id__in=student_ids)
        count = students_to_delete.count()
        
        student_names = ", ".join([s.short_name for s in students_to_delete[:10]])
        if count > 10:
            student_names += f" ... وآخرين (إجمالي: {count})"
            
        students_to_delete.delete()
        
        full_user_name = request.user.get_full_name() or request.user.username
        SystemLog.objects.create(
            user=request.user,
            action='delete',
            details=f"قام [{full_user_name}] بحذف جماعي لـ {count} طلاب: {student_names}"
        )
        
        messages.success(request, f'تم حذف {count} طلاب بنجاح من النظام بشكل نهائي.')
        
    return redirect(reverse('student_list') + '?' + request.GET.urlencode())

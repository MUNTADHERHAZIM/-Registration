from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Student, Department, AcademicYear, Semester, StudentDocument, StudentPromotion, StudentNote
from core.models import SystemLog
from .forms import StudentForm, DepartmentForm, AcademicYearForm, SemesterForm, StudentDocumentForm


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
        'sort': sort,
        'total_count': total_count,
        'sort_filter': sort,
        'title': 'قائمة الطلاب',
    }
    return render(request, 'students/student_list.html', context)


@permission_required('students.view_student', raise_exception=True)
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    documents = student.documents.all().order_by('-uploaded_at')
    doc_form = StudentDocumentForm()
    
    context = {
        'student': student,
        'documents': documents,
        'doc_form': doc_form,
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

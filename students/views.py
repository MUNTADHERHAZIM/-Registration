from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Student, Department, AcademicYear, Semester, StudentDocument, StudentPromotion, StudentNote
from core.models import SystemLog
from .forms import StudentForm, DepartmentForm, AcademicYearForm, SemesterForm, StudentDocumentForm


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


@login_required
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
    else:
        message = f"عزيزي الطالب {student.first_name} {student.last_name}،\n"
        
    link = generate_whatsapp_link(phone, message)
    if not link:
        messages.error(request, 'رقم الهاتف المدخل غير صالح.')
        return redirect('student_detail', pk=pk)
        
    return redirect(link)

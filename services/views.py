from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from django.http import JsonResponse
import base64
import uuid

from .models import StudentRequest, FAQ
from .forms import StudentRequestForm, TrackRequestForm, UpdateRequestStatusForm
from core.models import AdmissionGuide


# ============================================================
# PUBLIC VIEWS (no login required)
# ============================================================

def services_home(request):
    """Public landing page for student services"""
    request_types = StudentRequest.REQUEST_TYPE_CHOICES
    faqs = FAQ.objects.filter(is_active=True)
    guides = AdmissionGuide.objects.all().order_by('-updated_at')[:3]
    context = {
        'title': 'بوابة خدمات الطلاب',
        'request_types': request_types,
        'faqs': faqs,
        'guides': guides,
    }
    return render(request, 'services/services_home.html', context)


def admission_guide_public(request):
    """Public view for admission requirements and guidelines"""
    guides = AdmissionGuide.objects.all().order_by('-updated_at')
    return render(request, 'services/admission_guide.html', {
        'guides': guides,
        'title': 'ضوابط وتعليمات القبول',
    })


def submit_request(request):
    """Public form to submit a new student request"""
    if request.method == 'POST':
        form = StudentRequestForm(request.POST, request.FILES)
        if form.is_valid():
            student_request = form.save(commit=False)

            # Handle webcam photo (base64 data)
            webcam_data = form.cleaned_data.get('webcam_data', '')
            if webcam_data and webcam_data.startswith('data:image'):
                try:
                    fmt, imgstr = webcam_data.split(';base64,')
                    ext = fmt.split('/')[-1]
                    if ext == 'jpeg':
                        ext = 'jpg'
                    filename = f"webcam_{uuid.uuid4().hex[:8]}.{ext}"
                    data = ContentFile(base64.b64decode(imgstr), name=filename)
                    student_request.webcam_photo = data
                except Exception:
                    pass

            student_request.save()
            return redirect('request_success', tracking=student_request.tracking_number)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = StudentRequestForm()

    context = {
        'form': form,
        'title': 'تقديم طلب جديد',
    }
    return render(request, 'services/submit_request.html', context)


def request_success(request, tracking):
    """Success page after submitting a request"""
    student_request = get_object_or_404(StudentRequest, tracking_number=tracking)
    context = {
        'student_request': student_request,
        'title': 'تم تقديم الطلب بنجاح',
    }
    return render(request, 'services/request_success.html', context)


def track_request(request):
    """Public page to track request status"""
    form = TrackRequestForm(request.GET or None)
    results = None
    query = ''

    if form.is_valid():
        query = form.cleaned_data['query'].strip()
        results = StudentRequest.objects.filter(
            Q(tracking_number__iexact=query) |
            Q(student_id_number__iexact=query) |
            Q(national_id__iexact=query)
        ).order_by('-created_at')

    context = {
        'form': form,
        'results': results,
        'query': query,
        'title': 'تتبع الطلب',
    }
    return render(request, 'services/track_request.html', context)


def request_detail_public(request, tracking):
    """Public detail view for a specific request"""
    student_request = get_object_or_404(StudentRequest, tracking_number=tracking)
    context = {
        'req': student_request,
        'title': f'طلب رقم {tracking}',
    }
    return render(request, 'services/request_detail.html', context)


# ============================================================
# ADMIN / STAFF VIEWS (login required)
# ============================================================

@login_required
def manage_requests(request):
    """Staff view to manage all incoming requests"""
    requests_qs = StudentRequest.objects.all()

    # Filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    type_filter = request.GET.get('type', '')
    if type_filter:
        requests_qs = requests_qs.filter(request_type=type_filter)

    search = request.GET.get('q', '')
    if search:
        requests_qs = requests_qs.filter(
            Q(tracking_number__icontains=search) |
            Q(student_name__icontains=search) |
            Q(student_id_number__icontains=search) |
            Q(phone__icontains=search)
        )

    # Stats
    stats = {
        'total': StudentRequest.objects.count(),
        'new': StudentRequest.objects.filter(status='new').count(),
        'reviewing': StudentRequest.objects.filter(status='reviewing').count(),
        'approved': StudentRequest.objects.filter(status='approved').count(),
        'rejected': StudentRequest.objects.filter(status='rejected').count(),
        'completed': StudentRequest.objects.filter(status='completed').count(),
    }

    paginator = Paginator(requests_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search': search,
        'request_types': StudentRequest.REQUEST_TYPE_CHOICES,
        'status_choices': StudentRequest.STATUS_CHOICES,
        'title': 'إدارة طلبات الطلاب',
    }
    return render(request, 'services/manage_requests.html', context)


@login_required
def update_request_status(request, pk):
    """Staff view to update a request's status"""
    student_request = get_object_or_404(StudentRequest, pk=pk)

    if request.method == 'POST':
        form = UpdateRequestStatusForm(request.POST, instance=student_request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.reviewed_by = request.user.get_full_name() or request.user.username
            obj.save()
            messages.success(
                request,
                f'تم تحديث حالة الطلب {student_request.tracking_number} إلى "{obj.get_status_display()}"'
            )
            return redirect('manage_requests')
    else:
        form = UpdateRequestStatusForm(instance=student_request)

    context = {
        'form': form,
        'req': student_request,
        'title': f'تحديث الطلب {student_request.tracking_number}',
    }
    return render(request, 'services/update_request.html', context)
# ============================================================
# ERROR HANDLERS
# ============================================================

def handler404(request, exception):
    """Custom 404 error page"""
    return render(request, '404.html', status=404)


def handler500(request):
    """Custom 500 error page"""
    return render(request, '500.html', status=500)

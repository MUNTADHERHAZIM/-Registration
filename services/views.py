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


# ============================================================
# QR CODE SECURE DOCUMENT VERIFICATION SYSTEM
# ============================================================

import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

font_registered = False

def get_arabic_font_name():
    global font_registered
    if font_registered:
        return 'ArabicFont'
        
    # List of possible paths to an Arabic-supporting TTF font on Windows/Linux
    possible_paths = [
        r'C:\Windows\Fonts\arial.ttf',
        r'C:\Windows\Fonts\tahoma.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('ArabicFont', path))
                font_registered = True
                return 'ArabicFont'
            except Exception:
                continue
                
    # Fallback if no TTF found
    return 'Helvetica'


def fix_arabic(text):
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    if not text:
        return ""
    return get_display(reshape(str(text)))


def verify_request_document(request, tracking):
    """
    Publicly accessible unauthenticated document verification page.
    Checks the validity of the document via tracking number.
    """
    from services.models import StudentRequest
    
    student_request = StudentRequest.objects.filter(tracking_number=tracking).first()
    
    # Document is valid if found and status is 'approved' or 'completed'
    is_valid = student_request is not None and student_request.status in ['approved', 'completed']
    
    context = {
        'req': student_request,
        'is_valid': is_valid,
        'tracking_number': tracking,
        'title': f'التحقق من صحة المستند: {tracking}',
    }
    return render(request, 'services/verify_document.html', context)


def generate_request_pdf(request, tracking):
    """
    Publicly accessible but secure dynamic PDF generator.
    Only request statuses of 'approved' or 'completed' are allowed to download official documents.
    """
    from django.http import HttpResponseForbidden, HttpResponse
    from services.models import StudentRequest
    from core.models import SystemSettings
    import io
    
    student_request = get_object_or_404(StudentRequest, tracking_number=tracking)
    
    # Security Check: Only allow generating PDF if status is approved or completed
    if student_request.status not in ['approved', 'completed']:
        return HttpResponseForbidden("<h3>عذراً، هذه الوثيقة غير معتمدة أو لم تتم الموافقة عليها بعد من قبل إدارة التسجيل.</h3>")
    
    # Setup document settings
    settings_obj = SystemSettings.objects.first()
    univ_name = settings_obj.university_name if settings_obj else "الجامعة التقنية"
    coll_name = settings_obj.college_name if settings_obj else "إدارة التسجيل الجامعي"
    theme_color = settings_obj.header_color if settings_obj else "#1a237e"
    
    # Generate in-memory PDF
    buffer = io.BytesIO()
    
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib import colors
    import qrcode
    
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Get registered Arabic font
    font_name = get_arabic_font_name()
    
    # Define styled styles with Arabic font
    title_style = ParagraphStyle(
        'ArabicTitle', parent=styles['Normal'],
        fontName=font_name, fontSize=18, leading=22,
        textColor=colors.HexColor(theme_color),
        alignment=TA_CENTER, spaceAfter=20
    )
    body_style = ParagraphStyle(
        'ArabicBody', parent=styles['Normal'],
        fontName=font_name, fontSize=12, leading=20,
        alignment=TA_RIGHT, spaceAfter=12
    )
    meta_style = ParagraphStyle(
        'ArabicMeta', parent=styles['Normal'],
        fontName=font_name, fontSize=10, leading=14,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_RIGHT
    )
    center_style = ParagraphStyle(
        'ArabicCenter', parent=styles['Normal'],
        fontName=font_name, fontSize=11, leading=15,
        alignment=TA_CENTER
    )
    header_title_style = ParagraphStyle(
        'HeaderTitle', parent=styles['Normal'],
        fontName=font_name, fontSize=14, leading=18,
        textColor=colors.white, alignment=TA_CENTER
    )
    
    elements = []
    
    # --- Header Banner Table (Dark Theme Color) ---
    univ_reshaped = fix_arabic(univ_name)
    coll_reshaped = fix_arabic(coll_name)
    dept_label = fix_arabic("قسم التسجيل وشؤون الطلاب")
    
    header_data = [
        [
            Paragraph(f"<b>{univ_reshaped}</b><br/>{coll_reshaped}<br/>{dept_label}", header_title_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(theme_color)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 1*cm))
    
    # Document Metadata Block (Tracking, Issue Date)
    issue_date = student_request.updated_at.strftime('%Y/%m/%d')
    meta_text = f"الرقم التتبعي: {student_request.tracking_number} | تاريخ الإصدار: {issue_date} | رمز التحقق الإلكتروني"
    elements.append(Paragraph(fix_arabic(meta_text), meta_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Document Content Title and Body
    doc_title = ""
    doc_body = ""
    
    req_type = student_request.request_type
    student_name = student_request.student_name
    dept_name = student_request.department.name if student_request.department else ""
    level_display = student_request.get_level_display()
    
    if req_type == 'confirmation':
        doc_title = "تأييد استمرار بالدراسة"
        doc_body = (
            f"إلى من يهمه الأمر،\n\n"
            f"نؤيد أن الطالب {student_name} "
            f"هو أحد طلابنا المستمرين بالدراسة في {univ_name} - {coll_name}، "
            f"قسم {dept_name}، وهو مسجل في {level_display} للعام الدراسي الحالي. "
            f"وقد أُعطي هذا التأييد بناءً على طلبه لتقديمه للجهات الرسمية المعنية."
        )
    elif req_type == 'graduation_doc':
        doc_title = "وثيقة تخرج مؤقتة"
        doc_body = (
            f"إلى من يهمه الأمر،\n\n"
            f"نؤيد أن الطالب {student_name} "
            f"قد تخرج بنجاح من {univ_name} - {coll_name}، "
            f"قسم {dept_name}، وحصل على شهادة البكالوريوس بتقدير مستحق بعد إتمام كافة المتطلبات الأكاديمية. "
            f"وقد أُعطيت هذه الوثيقة بناءً على طلبه لتقديمها إلى من يهمه الأمر."
        )
    elif req_type == 'transcript':
        doc_title = "بيان الدرجات الأكاديمية"
        doc_body = (
            f"إلى من يهمه الأمر،\n\n"
            f"نؤيد صحة درجات الطالب {student_name} "
            f"المقيد في قسم {dept_name}، مرحلة {level_display}. "
            f"بيان تفصيلي بتقديراته ومعدله التراكمي مسجل رسمياً في إدارة شؤون الطلاب."
        )
    else:
        doc_title = student_request.get_request_type_display()
        doc_body = (
            f"إلى من يهمه الأمر،\n\n"
            f"بناءً على الطلب المقدم من الطالب {student_name} "
            f"المسجل في قسم {dept_name}، {level_display}، "
            f"نؤيد أن حالته الدراسية والأكاديمية معتمدة رسمياً وموثقة لدى عمادة الكلية."
        )
    
    elements.append(Paragraph(fix_arabic(doc_title), title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    for line in doc_body.split('\n'):
        if line.strip():
            elements.append(Paragraph(fix_arabic(line.strip()), body_style))
    
    elements.append(Spacer(1, 2*cm))
    
    # --- Bottom Block: Signature on Left, QR Code on Right ---
    verify_url = f"http://{request.get_host()}/services/verify/{student_request.tracking_number}/"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_io = io.BytesIO()
    qr_img.save(qr_io, format='PNG')
    qr_io.seek(0)
    
    from reportlab.platypus import Image as RLImage
    rl_qr_img = RLImage(qr_io, width=3*cm, height=3*cm)
    
    signature_text = fix_arabic("عمادة الكلية وشؤون الطلاب")
    director_title = fix_arabic("مدير قسم التسجيل العام")
    seal_text = fix_arabic("وثيقة إلكترونية مؤمنة لا تحتاج إلى ختم يدوي")
    
    bottom_left_data = [
        [Paragraph(f"<b>{signature_text}</b>", center_style)],
        [Spacer(1, 0.2*cm)],
        [Paragraph(director_title, center_style)],
        [Spacer(1, 1.2*cm)],
        [Paragraph(f"<font size=8 color='#94a3b8'>{seal_text}</font>", center_style)]
    ]
    bottom_left_table = Table(bottom_left_data, colWidths=[9*cm])
    bottom_left_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 0),
    ]))
    
    bottom_layout_data = [
        [rl_qr_img, bottom_left_table]
    ]
    bottom_table = Table(bottom_layout_data, colWidths=[4*cm, 13*cm])
    bottom_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 0),
    ]))
    
    elements.append(bottom_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Document_{student_request.tracking_number}.pdf"'
    return response


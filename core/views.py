from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AdmissionGuide, SystemLog

def admission_guide_view(request):
    guides = AdmissionGuide.objects.all().order_by('-updated_at')
    return render(request, 'core/admission_guide.html', {'guides': guides, 'title': 'ضوابط وتعليمات القبول'})

@login_required
def system_log_view(request):
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية لعرض سجل النظام')
        return redirect('dashboard')
    
    logs = SystemLog.objects.all().order_by('-timestamp')[:500] # Show last 500
    return render(request, 'core/system_log.html', {'logs': logs, 'title': 'سجل عمليات النظام'})

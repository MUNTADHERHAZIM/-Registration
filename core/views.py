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

@login_required
def clear_system_log(request):
    if not request.user.is_superuser:
        messages.error(request, 'عذراً، هذه الصفحة مخصصة لمدير النظام فقط!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        SystemLog.objects.all().delete()
        messages.success(request, 'تم مسح جميع سجلات النظام بنجاح.')
        
    return redirect('system_log')


@login_required
def system_settings_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'عذراً، هذه الصفحة مخصصة لمدير النظام فقط!')
        return redirect('dashboard')
        
    from .models import SystemSettings, SystemLog
    from .forms import SystemSettingsForm
    
    settings_obj = SystemSettings.objects.first()
    if not settings_obj:
        settings_obj = SystemSettings.objects.create(
            university_name="الجامعة التقنية",
            college_name="إدارة التسجيل الجامعي",
            header_color="#1a237e"
        )
        
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ إعدادات النظام وتحديث الهوية البصرية بنجاح!')
            
            full_user_name = request.user.get_full_name() or request.user.username
            SystemLog.objects.create(
                user=request.user,
                action='update',
                details=f"قام [{full_user_name}] بتحديث إعدادات النظام والألوان الأساسية للهوية البصرية."
            )
            return redirect('system_settings')
        else:
            messages.error(request, 'يرجى التحقق من الأخطاء وتصحيحها.')
    else:
        form = SystemSettingsForm(instance=settings_obj)
        
    context = {
        'form': form,
        'settings': settings_obj,
        'title': 'إعدادات النظام وتخصيص الهوية',
    }
    return render(request, 'core/system_settings.html', context)


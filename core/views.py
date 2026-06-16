from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AdmissionGuide, SystemLog, DynamicChoice
from .forms import DynamicChoiceForm

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


@login_required
def dynamic_choices_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'عذراً، هذه الصفحة مخصصة لمدير النظام فقط!')
        return redirect('dashboard')
    
    category_filter = request.GET.get('category', '')
    categories = DynamicChoice.CATEGORY_CHOICES
    
    from students.models import Student
    default_choices_map = {
        'governorate': Student.GOVERNORATE_CHOICES,
        'religion': Student.RELIGION_CHOICES,
        'health_status': Student.HEALTH_STATUS_CHOICES,
        'branch': Student.BRANCH_CHOICES,
        'origin_status': Student.ORIGIN_CHOICES,
        'admission_channel': Student.ADMISSION_CHANNEL_CHOICES,
        'marital_status': Student.MARITAL_STATUS_CHOICES,
        'gender': Student.GENDER_CHOICES,
        'level': Student.LEVEL_CHOICES,
        'study_type': Student.STUDY_TYPE_CHOICES,
        'status': Student.STATUS_CHOICES,
        'citizenship': Student.CITIZENSHIP_CHOICES,
        'birth_place': Student.BIRTH_PLACE_CHOICES,
    }
    
    db_choices = DynamicChoice.objects.all()
    if category_filter:
        db_choices = db_choices.filter(category=category_filter)
        
    from collections import defaultdict
    db_by_cat = defaultdict(list)
    for choice in db_choices:
        db_by_cat[choice.category].append(choice)
        
    display_choices = []
    cats_to_check = [category_filter] if category_filter else [cat[0] for cat in categories]
    
    counter = 1
    for cat in cats_to_check:
        cat_db = db_by_cat[cat]
        db_map = {choice.value: choice for choice in cat_db}
        defaults = default_choices_map.get(cat, [])
        cat_label = dict(categories).get(cat, cat)
        
        displayed_db_vals = set()
        
        # 1. Process defaults (including overrides)
        for val, display in defaults:
            if not val:
                continue
                
            if val in db_map:
                choice = db_map[val]
                displayed_db_vals.add(val)
                display_choices.append({
                    'index': counter,
                    'category': cat,
                    'category_display': cat_label,
                    'value': val,
                    'display_name': choice.display_name,
                    'is_active': choice.is_active,
                    'is_custom': True,
                    'pk': choice.pk
                })
            else:
                display_choices.append({
                    'index': counter,
                    'category': cat,
                    'category_display': cat_label,
                    'value': val,
                    'display_name': display,
                    'is_active': True,
                    'is_custom': False,
                    'pk': None
                })
            counter += 1
            
        # 2. Process newly added custom choices
        for choice in cat_db:
            if choice.value not in displayed_db_vals:
                display_choices.append({
                    'index': counter,
                    'category': cat,
                    'category_display': cat_label,
                    'value': choice.value,
                    'display_name': choice.display_name,
                    'is_active': choice.is_active,
                    'is_custom': True,
                    'pk': choice.pk
                })
                counter += 1
                    
    context = {
        'choices': display_choices,
        'category_filter': category_filter,
        'category_choices': categories,
        'title': 'تخصيص القوائم والخيارات الديناميكية',
    }
    return render(request, 'core/dynamic_choices.html', context)


@login_required
def dynamic_choice_add(request):
    if not request.user.is_superuser:
        messages.error(request, 'عذراً، هذه الصفحة مخصصة لمدير النظام فقط!')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = DynamicChoiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الخيار الجديد بنجاح.')
            return redirect('dynamic_choices')
    else:
        form = DynamicChoiceForm()
        
    context = {
        'form': form,
        'title': 'إضافة خيار ديناميكي جديد',
    }
    return render(request, 'core/dynamic_choice_form.html', context)


@login_required
def dynamic_choice_edit(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'عذراً، هذه الصفحة مخصصة لمدير النظام فقط!')
        return redirect('dashboard')
        
    choice = get_object_or_404(DynamicChoice, pk=pk)
    if request.method == 'POST':
        form = DynamicChoiceForm(request.POST, instance=choice)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل الخيار بنجاح.')
            return redirect('dynamic_choices')
    else:
        form = DynamicChoiceForm(instance=choice)
        
    context = {
        'form': form,
        'title': 'تعديل خيار ديناميكي',
        'choice': choice,
    }
    return render(request, 'core/dynamic_choice_form.html', context)


@login_required
def dynamic_choice_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'عذراً، هذه الصفحة مخصصة لمدير النظام فقط!')
        return redirect('dashboard')
        
    choice = get_object_or_404(DynamicChoice, pk=pk)
    if request.method == 'POST':
        choice.delete()
        messages.success(request, 'تم حذف الخيار الديناميكي بنجاح.')
    return redirect('dynamic_choices')



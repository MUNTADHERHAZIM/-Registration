from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import LoginForm, UserCreateForm, ChangePasswordForm, ProfileForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard')
                messages.success(request, f'مرحباً {user.get_full_name() or user.username}!')
                return redirect(next_url)
            else:
                messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'تم تسجيل الخروج بنجاح')
    return redirect('login')


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form, 'title': 'الملف الشخصي'})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'تم تغيير كلمة المرور بنجاح')
            return redirect('profile')
    else:
        form = ChangePasswordForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form, 'title': 'تغيير كلمة المرور'})


from .forms import LoginForm, UserCreateForm, ChangePasswordForm, ProfileForm, UserUpdateForm


@login_required
def user_list(request):
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية لعرض هذه الصفحة')
        return redirect('dashboard')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users, 'title': 'إدارة المستخدمين'})


@login_required
def user_add(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'تم إنشاء المستخدم {user.username} بنجاح')
            return redirect('user_list')
    else:
        form = UserCreateForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'إضافة مستخدم جديد'})


@login_required
def user_edit(request, pk):
    if not request.user.is_superuser:
        return redirect('dashboard')
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث بيانات {user.username} بنجاح')
            return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'accounts/user_form.html', {
        'form': form, 
        'title': f'تعديل المستخدم: {user.username}',
        'edit_mode': True
    })


@login_required
def user_delete(request, pk):
    if not request.user.is_superuser:
        return redirect('dashboard')
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'لا يمكنك حذف حسابك الحالي')
        return redirect('user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'تم حذف المستخدم {username} بنجاح')
        return redirect('user_list')
    
    return render(request, 'accounts/user_confirm_delete.html', {'target_user': user})

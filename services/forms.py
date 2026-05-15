from django import forms
from .models import StudentRequest


class StudentRequestForm(forms.ModelForm):
    """Form for public student request submission"""

    webcam_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        label='بيانات صورة الكاميرا'
    )

    class Meta:
        model = StudentRequest
        fields = [
            'request_type', 'student_name', 'student_id_number',
            'national_id', 'phone', 'email', 'department',
            'level', 'description', 'attachment',
        ]
        widgets = {
            'request_type': forms.Select(attrs={
                'class': 'form-select select2-field',
                'data-placeholder': 'اختر نوع الطلب...'
            }),
            'student_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل الاسم الرباعي'
            }),
            'student_id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: 20260001'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهوية الوطنية'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '07xxxxxxxxx',
                'dir': 'ltr'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@email.com',
                'dir': 'ltr'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select select2-field',
                'data-placeholder': 'اختر القسم...'
            }),
            'level': forms.Select(attrs={
                'class': 'form-select select2-field',
                'data-placeholder': 'اختر المرحلة...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'اكتب تفاصيل طلبك هنا...'
            }),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf,.doc,.docx'
            }),
        }


class TrackRequestForm(forms.Form):
    """Form for tracking a request by tracking number or student ID"""

    query = forms.CharField(
        max_length=50,
        label='البحث',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'أدخل رقم التتبع (مثل REQ-2026-0001) أو الرقم الجامعي...',
            'dir': 'ltr',
            'autofocus': True,
        })
    )


class UpdateRequestStatusForm(forms.ModelForm):
    """Form for admin to update request status"""

    class Meta:
        model = StudentRequest
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'أضف ملاحظة للطالب...'
            }),
        }

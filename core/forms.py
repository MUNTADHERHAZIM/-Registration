from django import forms
from .models import SystemSettings

class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ['university_name', 'college_name', 'logo', 'header_color', 'contact_email', 'contact_phone', 'address']
        widgets = {
            'university_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم الجامعة/الكلية'}),
            'college_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم الكلية/المعهد'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'header_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height:45px;width:100%;padding:4px;border-radius:10px;'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@univ.edu.iq'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '077XXXXXXXX'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'العنوان الكامل للجامعة'}),
        }

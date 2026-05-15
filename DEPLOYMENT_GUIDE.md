# 🚀 دليل نشر النظام على PythonAnywhere
# University System - PythonAnywhere Deployment Guide

## الخطوة 1: إنشاء حساب
1. اذهب إلى https://www.pythonanywhere.com
2. أنشئ حساب مجاني (Beginner)
3. سجل الدخول

## الخطوة 2: رفع ملفات المشروع

### الطريقة الأولى: عبر Git (الأفضل)
```bash
# في Bash console على PythonAnywhere:
cd ~
git clone https://github.com/yourusername/university_system.git
```

### الطريقة الثانية: رفع ملف مضغوط
1. اضغط المشروع كملف ZIP على جهازك
2. اذهب إلى Files tab على PythonAnywhere
3. ارفع ملف ZIP
4. افتح Bash console واكتب:
```bash
cd ~
unzip university_system.zip
```

## الخطوة 3: إنشاء بيئة افتراضية
```bash
cd ~/university_system
mkvirtualenv --python=/usr/bin/python3.10 myenv
pip install -r requirements.txt
```

## الخطوة 4: إعداد قاعدة البيانات
```bash
cd ~/university_system
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## الخطوة 5: إعداد Web App
1. اذهب إلى **Web** tab
2. اضغط **Add a new web app**
3. اختر **Manual configuration**
4. اختر **Python 3.10**

### إعداد المسارات:
| الإعداد | القيمة |
|---------|--------|
| Source code | `/home/yourusername/university_system` |
| Working directory | `/home/yourusername/university_system` |
| Virtualenv | `/home/yourusername/.virtualenvs/myenv` |

### إعداد WSGI:
1. اضغط على رابط **WSGI configuration file**
2. احذف كل المحتوى
3. انسخ والصق المحتوى التالي:

```python
import os
import sys

project_home = '/home/yourusername/university_system'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['DJANGO_SETTINGS_MODULE'] = 'university.settings'
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'yourusername.pythonanywhere.com'
os.environ['DJANGO_SECRET_KEY'] = 'ضع-هنا-مفتاح-سري-طويل-وعشوائي'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

⚠️ **مهم**: استبدل `yourusername` باسم المستخدم الحقيقي في PythonAnywhere

### إعداد Static files:
في Web tab، أضف:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/university_system/staticfiles` |
| `/media/` | `/home/yourusername/university_system/media` |

## الخطوة 6: إعادة التشغيل
1. اضغط **Reload** في أعلى Web tab
2. افتح `yourusername.pythonanywhere.com`

## استكشاف الأخطاء:
- **خطأ 500**: افحص Error log في Web tab
- **ملفات ثابتة لا تعمل**: تأكد من مسارات Static files
- **خطأ قاعدة البيانات**: شغل `python manage.py migrate`

## تحديث النظام لاحقاً:
```bash
cd ~/university_system
git pull  # أو ارفع الملفات الجديدة
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```
ثم اضغط **Reload** في Web tab

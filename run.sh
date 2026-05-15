#!/bin/bash
# =============================================
# نظام إدارة شؤون الطلاب الجامعي
# University Student Affairs Management System
# =============================================

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   نظام إدارة شؤون الطلاب الجامعي        ║"
echo "║   University Student Affairs System      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Install dependencies
echo "📦 تثبيت المكتبات..."
pip install -r requirements.txt -q

# Run migrations
echo "🗄️ إنشاء قاعدة البيانات..."
python manage.py makemigrations students courses registration grades reports accounts
python manage.py migrate

# Seed data
echo "🌱 توليد البيانات التجريبية..."
python seed_data.py

# Collect static
echo "📁 تجميع الملفات الثابتة..."
python manage.py collectstatic --noinput -v 0

echo ""
echo "✅ الإعداد اكتمل!"
echo ""
echo "🚀 تشغيل الخادم على: http://127.0.0.1:8000"
echo ""
python manage.py runserver

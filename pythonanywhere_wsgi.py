# ============================================================
# PythonAnywhere WSGI Configuration File
# ============================================================
# Copy this content to your PythonAnywhere WSGI config file:
# Go to Web tab → WSGI configuration file link
# Replace 'yourusername' with your actual PythonAnywhere username
# ============================================================

import os
import sys

# Add your project directory to the sys.path
project_home = '/home/yourusername/university_system'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'university.settings'
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'yourusername.pythonanywhere.com'
os.environ['DJANGO_SECRET_KEY'] = 'your-production-secret-key-change-this-to-random-string'

# Activate your virtualenv
# Uncomment and update the path if using a virtualenv
# activate_this = '/home/yourusername/.virtualenvs/myenv/bin/activate_this.py'
# exec(open(activate_this).read(), {'__file__': activate_this})

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

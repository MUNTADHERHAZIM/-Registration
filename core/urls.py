from django.urls import path
from . import views

urlpatterns = [
    path('admission-guide/', views.admission_guide_view, name='admission_guide'),
    path('system-log/', views.system_log_view, name='system_log'),
    path('system-log/clear/', views.clear_system_log, name='clear_system_log'),
    path('settings/', views.system_settings_view, name='system_settings'),
]

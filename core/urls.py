from django.urls import path
from . import views

urlpatterns = [
    path('admission-guide/', views.admission_guide_view, name='admission_guide'),
    path('system-log/', views.system_log_view, name='system_log'),
    path('system-log/clear/', views.clear_system_log, name='clear_system_log'),
    path('settings/', views.system_settings_view, name='system_settings'),
    path('settings/choices/', views.dynamic_choices_view, name='dynamic_choices'),
    path('settings/choices/add/', views.dynamic_choice_add, name='dynamic_choice_add'),
    path('settings/choices/<int:pk>/edit/', views.dynamic_choice_edit, name='dynamic_choice_edit'),
    path('settings/choices/<int:pk>/delete/', views.dynamic_choice_delete, name='dynamic_choice_delete'),
]

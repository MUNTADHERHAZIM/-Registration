from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    path('students/', views.students_report, name='students_report'),
    path('statistics/', views.statistics_report, name='statistics_report'),
    path('performance/', views.admin_performance_dashboard, name='admin_performance'),
]

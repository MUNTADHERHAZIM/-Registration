from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('students/<int:pk>/print/', views.student_print, name='student_print'),
    path('students/<int:pk>/add-document/', views.add_student_document, name='add_student_document'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    path('academic-years/', views.academic_year_list, name='academic_year_list'),
    path('academic-years/add/', views.academic_year_add, name='academic_year_add'),
    path('semesters/', views.semester_list, name='semester_list'),
    path('semesters/add/', views.semester_add, name='semester_add'),
    path('preliminary/', views.preliminary_registration_list, name='preliminary_list'),
    path('preliminary/activate/', views.activate_students, name='activate_students'),
    path('promote/', views.student_promote, name='student_promote'),
    path('api/students/search/', views.api_students_search, name='api_students_search'),
    
    # Notes & Documents Management
    path('students/<int:pk>/add-note/', views.add_student_note, name='add_student_note'),
    path('notes/<int:pk>/delete/', views.delete_student_note, name='delete_student_note'),
    path('documents/<int:pk>/delete/', views.delete_student_document, name='delete_student_document'),
]

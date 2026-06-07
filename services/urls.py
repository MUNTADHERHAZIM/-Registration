from django.urls import path
from . import views

urlpatterns = [
    # Public URLs (no login required)
    path('', views.services_home, name='services_home_public'),
    path('submit/', views.submit_request, name='submit_request'),
    path('success/<str:tracking>/', views.request_success, name='request_success'),
    path('track/', views.track_request, name='track_request'),
    path('request/<str:tracking>/', views.request_detail_public, name='request_detail_public'),
    path('admission-guide/', views.admission_guide_public, name='admission_guide_public'),

    # Staff URLs (login required)
    path('manage/', views.manage_requests, name='manage_requests'),
    path('manage/<int:pk>/update/', views.update_request_status, name='update_request_status'),

    # Document Verification & Generation URLs (public / secure)
    path('verify/<str:tracking>/', views.verify_request_document, name='verify_request_document'),
    path('request/<str:tracking>/pdf/', views.generate_request_pdf, name='generate_request_pdf'),
]

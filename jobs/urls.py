from django.urls import path
from . import views

urlpatterns = [
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/apply/', views.apply_job, name='apply_job'),
    path('jobs/<int:pk>/applicants/', views.job_applicants, name='job_applicants'),
    path('applications/<int:pk>/status/', views.update_application_status, name='update_application_status'),
    path('applications/<int:pk>/conversation/', views.application_conversation, name='application_conversation'),
    path('post-job/', views.post_job, name='post_job'),
]

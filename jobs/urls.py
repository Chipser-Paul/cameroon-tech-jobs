from django.urls import path
from . import views

urlpatterns = [
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', views.edit_job, name='edit_job'),
    path('jobs/<int:pk>/close/', views.close_job, name='close_job'),
    path('jobs/<int:pk>/delete/', views.delete_job, name='delete_job'),
    path('jobs/<int:pk>/apply/', views.apply_job, name='apply_job'),
    path('jobs/<int:pk>/applicants/', views.job_applicants, name='job_applicants'),
    path('applications/<int:pk>/status/', views.update_application_status, name='update_application_status'),
    path('applications/<int:pk>/conversation/', views.application_conversation, name='application_conversation'),
    path('applications/<int:pk>/schedule-interview/', views.schedule_interview, name='schedule_interview'),
    path('interviews/<int:pk>/respond/', views.respond_to_interview, name='respond_to_interview'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('post-job/', views.post_job, name='post_job'),
]

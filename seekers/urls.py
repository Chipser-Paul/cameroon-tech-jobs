from django.urls import path
from . import views

urlpatterns = [
    path('seeker/register/', views.seeker_register, name='seeker_register'),
    path('seeker/login/', views.seeker_login, name='seeker_login'),
    path('seeker/logout/', views.seeker_logout, name='seeker_logout'),
    path('seeker/dashboard/', views.seeker_dashboard, name='seeker_dashboard'),
    path('seeker/profile/', views.seeker_profile, name='seeker_profile'),
    path('seeker/profile/edit/', views.edit_profile, name='edit_profile'),
    path('seeker/saved-jobs/', views.saved_jobs, name='saved_jobs'),
    path('seeker/save-job/<int:pk>/', views.save_job, name='save_job'),
    path('seekers/', views.seeker_list, name='seeker_list'),
    path('seekers/<int:pk>/', views.seeker_detail, name='seeker_detail'),
]
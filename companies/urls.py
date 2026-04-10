from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.company_login, name='login'),
    path('logout/', views.company_logout, name='logout'),
    path('verify/<uuid:token>/', views.verify_company, name='company_verify'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('edit-profile/', views.edit_profile, name='company_edit_profile'),
    path('company/<int:pk>/', views.company_profile, name='company_profile'),
    path('payment-info/', views.payment_info, name='payment_info'),
]
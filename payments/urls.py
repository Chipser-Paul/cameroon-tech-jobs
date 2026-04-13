from django.urls import path
from . import views

urlpatterns = [
    path('pricing/', views.pricing, name='pricing'),
    path('initiate/<int:job_id>/', views.initiate_payment, name='initiate_payment'),
    path('webhook/', views.webhook, name='payment_webhook'),
    path('success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('success/', views.payment_success, name='payment_success_legacy'),
    path('failure/', views.payment_failure, name='payment_failure'),
    path('check/<int:payment_id>/', views.check_payment_status, name='check_payment_status'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('pricing/', views.pricing, name='pricing'),
    path('initiate/<int:job_id>/', views.initiate_payment, name='initiate_payment'),
    path('webhook/', views.webhook, name='payment_webhook'),
    path('success/', views.payment_success, name='payment_success'),
    path('failure/', views.payment_failure, name='payment_failure'),
]

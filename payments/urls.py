from django.urls import path
from . import views

urlpatterns = [
    path('pricing/', views.pricing, name='pricing'),
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    path('webhook/', views.webhook, name='payment_webhook'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('check/<str:request_id>/', views.check_payment_status, name='check_payment_status'),
]

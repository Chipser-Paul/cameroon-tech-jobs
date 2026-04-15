import json
from unittest.mock import patch

from django.apps import apps
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    SITE_URL='https://cameroon-tech-jobs.onrender.com',
)
class PaymentFlowTests(TestCase):
    def setUp(self):
        Company = apps.get_model('companies', 'Company')
        Category = apps.get_model('jobs', 'Category')
        Job = apps.get_model('jobs', 'Job')
        Payment = apps.get_model('payments', 'Payment')

        self.Payment = Payment
        self.company = Company.objects.create_user(
            email='hr@example.com',
            company_name='Example Co',
            password='secure-pass-123',
            is_verified=True,
        )
        self.category = Category.objects.create(name='Web Development', slug='web-development')
        self.job = Job.objects.create(
            company=self.company,
            category=self.category,
            title='Backend Engineer',
            description='Build APIs',
            requirements='Python and Django',
            location='douala',
            job_type='full_time',
            plan='basic',
            status='pending',
        )

    def test_pricing_page_is_public(self):
        response = self.client.get(reverse('pricing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choose Your Hiring Plan')
        self.assertContains(response, 'Create Company Account')

    def test_company_can_initiate_payment_for_pending_job(self):
        self.client.force_login(self.company, backend='django.contrib.auth.backends.ModelBackend')

        with patch('payments.views.create_payment_request') as create_request:
            create_request.return_value = {
                'success': True,
                'data': {
                    'requestId': 'REQ12345',
                    'links': {
                        'paymentAuthUrl': 'https://sandbox.example/checkout/REQ12345',
                    },
                },
            }

            response = self.client.post(
                reverse('initiate_payment'),
                {'tier': self.Payment.BASIC_TIER, 'job_id': self.job.id},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://sandbox.example/checkout/REQ12345')
        payment = self.Payment.objects.get(job=self.job)
        self.assertEqual(payment.company, self.company)
        self.assertEqual(payment.status, self.Payment.STATUS_PENDING)
        self.assertEqual(payment.tranzak_request_id, 'REQ12345')
        self.assertTrue(payment.mch_transaction_ref)

    @override_settings(TRANZAK_WEBHOOK_KEY='secret-key')
    def test_webhook_marks_payment_successful_and_activates_job(self):
        payment = self.Payment.objects.create(
            company=self.company,
            job=self.job,
            tier=self.Payment.PREMIUM_TIER,
            amount=self.Payment.PREMIUM_TIER,
            currency='XAF',
            status=self.Payment.STATUS_PENDING,
            tranzak_request_id='REQ-SUCCESS',
            mch_transaction_ref='ref-success',
        )

        response = self.client.post(
            reverse('payment_webhook'),
            data=json.dumps({
                'authKey': 'secret-key',
                'eventType': 'REQUEST.COMPLETED',
                'resource': {
                    'requestId': 'REQ-SUCCESS',
                    'status': 'SUCCESSFUL',
                },
            }),
            content_type='application/json',
        )

        payment.refresh_from_db()
        self.job.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, self.Payment.STATUS_SUCCESSFUL)
        self.assertEqual(self.job.status, 'active')
        self.assertTrue(self.job.is_featured)

    def test_check_payment_status_updates_payment_and_redirects(self):
        payment = self.Payment.objects.create(
            company=self.company,
            job=self.job,
            tier=self.Payment.BASIC_TIER,
            amount=self.Payment.BASIC_TIER,
            currency='XAF',
            status=self.Payment.STATUS_PENDING,
            tranzak_request_id='REQ-CHECK',
            mch_transaction_ref='ref-check',
        )
        self.client.force_login(self.company, backend='django.contrib.auth.backends.ModelBackend')

        with patch('payments.views.fetch_request_details') as fetch_details:
            fetch_details.return_value = {
                'success': True,
                'data': {
                    'requestId': 'REQ-CHECK',
                    'status': 'SUCCESSFUL',
                },
            }
            response = self.client.get(reverse('check_payment_status', args=['REQ-CHECK']))

        payment.refresh_from_db()
        self.job.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('dashboard'))
        self.assertEqual(payment.status, self.Payment.STATUS_SUCCESSFUL)
        self.assertEqual(self.job.status, 'active')

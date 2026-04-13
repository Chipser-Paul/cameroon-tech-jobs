import uuid

import django.db.models.deletion
from django.db import migrations, models


def migrate_payment_data(apps, schema_editor):
    Payment = apps.get_model('payments', 'Payment')

    tier_mapping = {
        'basic': 5000,
        'featured': 15000,
    }
    status_mapping = {
        'pending': 'PENDING',
        'successful': 'SUCCESSFUL',
        'failed': 'FAILED',
        'cancelled': 'CANCELLED',
    }

    for payment in Payment.objects.select_related('job', 'job__company').all():
        payment.company = getattr(payment.job, 'company', None)
        payment.tier_amount = tier_mapping.get(payment.tier, 5000)
        payment.amount = int(payment.amount or 0)
        payment.status = status_mapping.get(payment.status, 'PENDING')
        payment.mch_transaction_ref = payment.campay_reference or uuid.uuid4().hex
        payment.save(
            update_fields=[
                'company',
                'tier_amount',
                'amount',
                'status',
                'mch_transaction_ref',
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0004_alter_company_logo_and_more'),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='company',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payments',
                to='companies.company',
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='job',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payments',
                to='jobs.job',
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='currency',
            field=models.CharField(default='XAF', max_length=3),
        ),
        migrations.AddField(
            model_name='payment',
            name='tranzak_request_id',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddField(
            model_name='payment',
            name='mch_transaction_ref',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='tier_amount',
            field=models.PositiveIntegerField(
                blank=True,
                choices=[(5000, 'Basic - 5,000 FCFA'), (15000, 'Premium - 15,000 FCFA')],
                null=True,
            ),
        ),
        migrations.RunPython(migrate_payment_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='payment',
            name='tier',
        ),
        migrations.RenameField(
            model_name='payment',
            old_name='tier_amount',
            new_name='tier',
        ),
        migrations.AlterField(
            model_name='payment',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payments',
                to='companies.company',
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='payment',
            name='tier',
            field=models.PositiveIntegerField(
                choices=[(5000, 'Basic - 5,000 FCFA'), (15000, 'Premium - 15,000 FCFA')]
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('SUCCESSFUL', 'Successful'),
                    ('FAILED', 'Failed'),
                    ('CANCELLED', 'Cancelled'),
                ],
                default='PENDING',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='mch_transaction_ref',
            field=models.CharField(max_length=64, unique=True),
        ),
        migrations.RemoveField(
            model_name='payment',
            name='campay_reference',
        ),
    ]

# Generated migration for CompanyVerificationToken

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_company_is_verified'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyVerificationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_used', models.BooleanField(default=False)),
                ('company', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='verification_token', to='companies.company')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

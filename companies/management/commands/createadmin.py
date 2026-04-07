import os

from django.core.management.base import BaseCommand

from companies.models import Company


class Command(BaseCommand):
    help = "Create a company superuser from environment variables if it does not already exist."

    def handle(self, *args, **options):
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
        company_name = os.getenv("DJANGO_SUPERUSER_COMPANY_NAME", "Admin")

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Skipping admin creation because DJANGO_SUPERUSER_EMAIL or "
                    "DJANGO_SUPERUSER_PASSWORD is not set."
                )
            )
            return

        user, created = Company.objects.get_or_create(
            email=email,
            defaults={
                "company_name": company_name,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created admin user: {email}"))
            return

        changed = False
        if user.company_name != company_name:
            user.company_name = company_name
            changed = True
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True

        if changed:
            user.save(update_fields=["company_name", "is_staff", "is_superuser", "is_active"])

        self.stdout.write(self.style.SUCCESS(f"Admin user already exists: {email}"))

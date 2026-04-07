from django.core.management.base import BaseCommand
from companies.models import Company


class Command(BaseCommand):
    help = 'Create admin superuser'

    def handle(self, *args, **kwargs):
        if not Company.objects.filter(email='chipseremmanuel@gmail.com').exists():
            Company.objects.create_superuser(
                email='chipseremmanuel@gmail.com',
                company_name='Admin',
                password='Jump Force 1'
            )
            self.stdout.write(self.style.SUCCESS('Admin created successfully!'))
        else:
            self.stdout.write('Admin already exists.')
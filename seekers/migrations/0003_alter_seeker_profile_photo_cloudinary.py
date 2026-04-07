from cloudinary.models import CloudinaryField
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('seekers', '0002_alter_seeker_experience_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seeker',
            name='profile_photo',
            field=CloudinaryField(
                blank=True,
                folder='cameroon_tech_jobs/seekers',
                max_length=255,
                null=True,
                verbose_name='image',
            ),
        ),
    ]

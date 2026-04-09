from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    def ready(self):
        import os
        # Only import signals in main process to avoid duplicate registration
        if os.environ.get('RUN_MAIN') == 'true' or 'celery' not in os.environ.get('DJANGO_SETTINGS_MODULE', ''):
            try:
                from . import signals  # noqa: F401
            except Exception:
                pass

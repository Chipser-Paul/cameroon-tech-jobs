import os
from django.asgi import get_asgi_application # pyright: ignore[reportMissingImports]

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
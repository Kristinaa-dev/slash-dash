# app/celery.py
from celery import Celery
import os

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# Create the Celery app
celery_app = Celery('app')

# Load task modules from all registered Django app configs
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()

import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_advocacia.settings')

app = Celery('crm_advocacia')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

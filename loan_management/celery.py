from __future__ import absolute_import, unicode_literals
import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE','loan_management.settings')

app = Celery('loan_management')

app.config_from_object(settings,namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    return f"Request : {self.request!r}" 
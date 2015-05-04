import sys
from datetime import datetime

from django.core.mail import mail_admins

from celery import VERSION

from fjord.celery import app

@app.task()
def celery_health_task(creation_dt):
    """Emails celery health"""
    now = datetime.now()

    data = [
        ('creation_dt', creation_dt),
        ('execute_dt', now),
        ('delta', now - creation_dt),
        ('python_ver', sys.version),
        ('celery_ver', VERSION),
    ]

    message = '\n'.join(['{key}: {val}'.format(key=key, val=str(val))
                         for key, val in data])

    message += '\n\nThank you for playing!\n'

    mail_admins(
        subject=' celery health: {0}'.format(now),
        message=message
    )

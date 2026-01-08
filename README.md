# alx-backend-graphql_crm
#crm/celery.py

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

app = Celery('crm')
## Using Redis as the broker
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

#crm/__init__.py

from .celery import app as celery_app
__all__ = ('celery_app',)

#crm/settings.py
INSTALLED_APPS = [
    ...,
    'django_celery_beat',
]

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0), # Monday 6 AM
    },
}

#crm/tasks.py
import datetime
import requests
from celery import shared_task

@shared_task
def generate_crm_report():
    query = """
    query {
      totalCustomers
      totalOrders
      totalRevenue
    }
    """
    try:
        response = requests.post("http://localhost:8000/graphql", json={'query': query})
        data = response.json().get('data', {})
        
        customers = data.get('totalCustomers', 0)
        orders = data.get('totalOrders', 0)
        revenue = data.get('totalRevenue', 0)
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"{timestamp} - Report: {customers} customers, {orders} orders, {revenue} revenue\n"
        
        with open('/tmp/crm_report_log.txt', 'a') as f:
            f.write(log_msg)
            
    except Exception as e:
        print(f"Error generating report: {e}")

#crm/README.md
### CRM Task Automation Setup

### 1. Prerequisites
- Install Redis: `sudo apt install redis-server` (Linux) or `brew install redis` (Mac)
- Start Redis: `redis-server`

### 2. Dependencies & Database
- Install requirements: `pip install -r requirements.txt`
- Run migrations for Celery Beat: `python manage.py migrate`

### 3. Running the System
You need three separate terminal windows:
1. **Django:** `python manage.py runserver`
2. **Worker:** `celery -A crm worker -l info` (Executes the tasks)
3. **Beat:** `celery -A crm beat -l info` (Schedules the tasks)

### 4. Verification
Check the logs at `/tmp/crm_report_log.txt` to see the generated weekly reports.


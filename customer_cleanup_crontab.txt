crm/cron_jobs/clean_inactive_customers.sh

#!/bin/bash

# Absolute path to project root
PROJECT_DIR="/path/to/your/project"

# Absolute path to Python inside virtual environment
PYTHON_BIN="/path/to/your/venv/bin/python"

# Log file
LOG_FILE="/tmp/customer_cleanup_log.txt"

# Run Django shell command
DELETED_COUNT=$(
$PYTHON_BIN $PROJECT_DIR/manage.py shell << EOF
from datetime import timedelta
from django.utils import timezone
from customers.models import Customer

one_year_ago = timezone.now() - timedelta(days=365)

inactive_customers = Customer.objects.filter(
    orders__isnull=True,
    created_at__lt=one_year_ago
)

count = inactive_customers.count()
inactive_customers.delete()

print(count)
EOF
)

# Write log with timestamp
echo "$(date '+%Y-%m-%d %H:%M:%S') - Deleted customers: $DELETED_COUNT" >> $LOG_FILE

PROJECT_DIR="/path/to/your/project"
PYTHON_BIN="/path/to/your/venv/bin/python"

/home/patrick/crm_project
/home/patrick/venv/bin/python

manage.py shell << EOF

one_year_ago = timezone.now() - timedelta(days=365)

inactive_customers = Customer.objects.filter(
    orders__isnull=True,
    created_at__lt=one_year_ago
)

count = inactive_customers.count()
inactive_customers.delete()

echo "$(date ...) - Deleted customers: $DELETED_COUNT" >> /tmp/customer_cleanup_log.txt

chmod +x crm/cron_jobs/clean_inactive_customers.sh

crm/cron_jobs/customer_cleanup_crontab.txt

0 2 * * 0 /path/to/your/project/crm/cron_jobs/clean_inactive_customers.sh

0 2 * * 0

crontab customer_cleanup_crontab.txt


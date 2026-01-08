crm/cron_jobs/send_order_reminders.py

#!/usr/bin/env python3

from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

LOG_FILE = "/tmp/order_reminders_log.txt"
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"

def main():
    # Calculate date range
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

    # GraphQL query
    query = gql(
        """
        query GetRecentOrders($since: DateTime!) {
            orders(orderDate_Gte: $since, status: "PENDING") {
                id
                customer {
                    email
                }
            }
        }
        """
    )

    # GraphQL client
    transport = RequestsHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        verify=True,
        retries=3,
    )

    client = Client(
        transport=transport,
        fetch_schema_from_transport=False,
    )

    # Execute query
    result = client.execute(query, variable_values={"since": seven_days_ago})

    orders = result.get("orders", [])

    # Log reminders
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a") as log:
        for order in orders:
            order_id = order["id"]
            email = order["customer"]["email"]
            log.write(
                f"{timestamp} - Reminder logged for Order ID: {order_id}, Email: {email}\n"
            )

    print("Order reminders processed!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

pip install gql requests

seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

query GetRecentOrders($since: DateTime!) {
    orders(orderDate_Gte: $since, status: "PENDING") {
        id
        customer {
            email
        }
    }
}

/tmp/order_reminders_log.txt

2026-01-08 08:00:00 - Reminder logged for Order ID: 123, Email: user@example.com

print("Order reminders processed!")

chmod +x crm/cron_jobs/send_order_reminders.py

crm/cron_jobs/order_reminders_crontab.txt

0 8 * * * /usr/bin/python3 /path/to/your/project/crm/cron_jobs/send_order_reminders.py >> /tmp/order_reminders_cron.log 2>&1

0 8 * * *


>> /tmp/order_reminders_cron.log 2>&1

                                     

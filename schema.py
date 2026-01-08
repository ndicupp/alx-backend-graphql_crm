# crm/schema.py
import graphene
from django.utils import timezone
from products.models import Product


class UpdatedProductType(graphene.ObjectType):
    name = graphene.String()
    stock = graphene.Int()


class UpdateLowStockProducts(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    updated_products = graphene.List(UpdatedProductType)

    class Arguments:
        pass  # No external arguments needed

    def mutate(self, info):
        low_stock_products = Product.objects.filter(stock__lt=10)

        updated = []

        for product in low_stock_products:
            product.stock += 10
            product.save()

            updated.append(
                UpdatedProductType(
                    name=product.name,
                    stock=product.stock,
                )
            )

        return UpdateLowStockProducts(
            success=True,
            message="Low stock products updated successfully",
            updated_products=updated,
        )

# crm/cron.py
import datetime
import requests

def update_low_stock():
    log_file_path = '/tmp/low_stock_updates_log.txt'
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    mutation = """
    mutation {
        updateLowStockProducts {
            success
            updatedProducts
        }
    }
    """
    
    try:
        response = requests.post("http://localhost:8000/graphql", json={'query': mutation})
        data = response.json().get('data', {}).get('updateLowStockProducts', {})
        
        if data.get('success'):
            products = data.get('updatedProducts', [])
            with open(log_file_path, 'a') as f:
                if products:
                    for p in products:
                        f.write(f"[{now}] Updated: {p}\n")
                else:
                    f.write(f"[{now}] No low stock products found.\n")
    except Exception as e:
        with open(log_file_path, 'a') as f:
            f.write(f"[{now}] Error executing mutation: {str(e)}\n")

class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()


# crm/settings.py
CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]

0 */12 * * *


# Apply the new schedule
python manage.py crontab add

python manage.py crontab show

cat /tmp/low_stock_updates_log.txt

08/01/2026-00:00:00 - Product: USB Cable, New Stock: 15
08/01/2026-00:00:00 - Product: Keyboard, New Stock: 12






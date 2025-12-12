# alx_backend_graphql_crm/settings.py

INSTALLED_APPS = [
    # ... other apps
    'crm',
    'graphene_django',
    'django_filters', # <-- Ensure this is present
]

# crm/models.py (Snippet - only showing changes)
class Customer(models.Model):
    # ... existing fields
    # Renamed for consistency with GraphQL checkpoint:
    created_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    # ... existing fields
    order_date = models.DateTimeField(auto_now_add=True) # Already present

# crm/filters.py

import django_filters
from django_filters import CharFilter, DateFilter, NumberFilter, RangeFilter, Filter
from .models import Customer, Product, Order
import re

# Custom filter method for the phone number challenge
def filter_by_phone_pattern(queryset, name, value):
    """Filters customers whose phone number matches a basic pattern (e.g., starts with +1)."""
    # Example: Check if phone starts with the provided pattern (e.g., '+1')
    return queryset.filter(phone__startswith=value)

class CustomerFilter(django_filters.FilterSet):
    name = CharFilter(lookup_expr='icontains')
    email = CharFilter(lookup_expr='icontains')
    # Filter for date ranges
    created_at_gte = DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = DateFilter(field_name='created_at', lookup_expr='lte')
    # Challenge: Custom filter for phone pattern
    phone_pattern = django_filters.MethodFilter(method=filter_by_phone_pattern)

    class Meta:
        model = Customer
        # Define fields and lookups to expose in GraphQL
        fields = ['name', 'email', 'created_at'] 

class ProductFilter(django_filters.FilterSet):
    name = CharFilter(lookup_expr='icontains')
    # Price range filter
    price = RangeFilter()
    # Stock range filter
    stock = RangeFilter()
    
    # Challenge: Low stock filter (stock < 10)
    def filter_low_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

    low_stock = Filter(method='filter_low_stock', label="Filter products with stock less than 10")

    class Meta:
        model = Product
        fields = ['name', 'price', 'stock']

class OrderFilter(django_filters.FilterSet):
    # Total amount range filter
    total_amount = RangeFilter()
    # Order date range filter
    order_date = RangeFilter()
    
    # Filter orders by customer's name (related lookup)
    customer_name = CharFilter(field_name='customer__name', lookup_expr='icontains')
    # Filter orders by product's name (related lookup, use distinct to avoid duplicate orders)
    product_name = CharFilter(field_name='products__name', lookup_expr='icontains', distinct=True)
    
    # Challenge: Filter orders that include a specific product ID
    product_id = Filter(field_name='products__id', lookup_expr='exact', distinct=True)

    class Meta:
        model = Order
        fields = ['total_amount', 'order_date']


# crm/schema.py (Updated)

import graphene
from graphene import relay
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
# Import models and filters
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
# ... (Imported other items like re, Decimal, etc. from Task 2)

# --- 1. Define GraphQL Types with Relay Node (Output) ---

# All Types must inherit from relay.Node to use ConnectionFields
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone', 'created_at')
        interfaces = (relay.Node,) # Required for connections/pagination

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock')
        interfaces = (relay.Node,)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'order_date', 'total_amount')
        interfaces = (relay.Node,)

# --- 2. Define Mutations (Omitted for brevity, assumed from Task 2) ---
# ... (CreateCustomer, BulkCreateCustomers, CreateProduct, CreateOrder logic goes here)

class Mutation(graphene.ObjectType):
    # ... (Mutation fields from Task 2 go here)
    pass 

# --- 3. Define the Query Class with Filtering and Ordering ---

class Query(graphene.ObjectType):
    # Relay field to fetch any object by its global ID
    node = relay.Node.Field()
    
    hello = graphene.String(default_value="Hello, CRM GraphQL with Filtering!")

    # A. Customer Queries
    customer = relay.Node.Field(CustomerType)
    # Uses DjangoFilterConnectionField for filtering, sorting, and pagination
    all_customers = DjangoFilterConnectionField(
        CustomerType, 
        filterset_class=CustomerFilter,
        # Challenge: order_by argument is automatically supported by DjangoFilterConnectionField
    )

    # B. Product Queries
    product = relay.Node.Field(ProductType)
    all_products = DjangoFilterConnectionField(
        ProductType, 
        filterset_class=ProductFilter,
    )

    # C. Order Queries
    order = relay.Node.Field(OrderType)
    all_orders = DjangoFilterConnectionField(
        OrderType, 
        filterset_class=OrderFilter,
    )

# Note: The top-level schema (alx_backend_graphql_crm/schema.py) should already be correctly
# importing and combining this Query class from crm.schema, as per Task 2.
# alx_backend_graphql_crm/schema.py:
# class Query(CRMQuery, graphene.ObjectType):
#     pass


# Filter customers by name (e.g., 'Ali') and creation date (after 2025-01-01)
query FilterCustomers {
  allCustomers(nameIcontains: "Ali", createdAtGte: "2025-01-01") {
    edges {
      node {
        id
        name
        email
        createdAt: created_at
      }
    }
  }
}

# Filter products with price between 100 and 1000, sorted descending by stock
query FilterProducts {
  allProducts(priceLte: 1000, priceGte: 100, orderBy: ["-stock"]) {
    edges {
      node {
        id
        name
        price
        stock
      }
    }
  }
}

# Filter orders where the customer name contains 'Alice', product name contains 'Laptop', and total amount is >= 500
query FilterOrders {
  allOrders(customerName: "Alice", productName: "Laptop", totalAmountGte: 500) {
    edges {
      node {
        id
        customer {
          name
        }
        # Note: The name 'products' is plural (M2M field)
        products { 
          edges {
            node {
              name
            }
          }
        }
        totalAmount
        orderDate
      }
    }
  }
}





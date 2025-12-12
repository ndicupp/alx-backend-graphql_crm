django-admin startproject alx_backend_graphql_crm
cd alx_backend_graphql_crm
python manage.py startapp crm

pip install graphene-django django-filter

INSTALLED_APPS = [
    ...
    "crm",
    "graphene_django",
    "django_filters",
]

GRAPHENE = {
    "SCHEMA": "alx_backend_graphql_crm.schema.schema"
}

import graphene

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

schema = graphene.Schema(query=Query)

from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
]

python manage.py runserver

{
  hello
}

{
  "data": {
    "hello": "Hello, GraphQL!"
  }
}


from django.db import models
from django.utils import timezone

class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_date = models.DateTimeField(default=timezone.now)


python manage.py makemigrations
python manage.py migrate


import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from django.db import transaction
from django.utils import timezone
from .models import Customer, Product, Order

# ----------------------------
# GraphQL Types
# ----------------------------

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")

# ----------------------------
# Validation helpers
# ----------------------------

import re

def validate_phone(phone):
    if phone is None:
        return True
    pattern = r"^\+?\d[\d\-]{5,}$"
    return re.match(pattern, phone) is not None

# ----------------------------
# CreateCustomer Mutation
# ----------------------------

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # Email uniqueness check
        if Customer.objects.filter(email=email).exists():
            raise GraphQLError("Email already exists.")

        if not validate_phone(phone):
            raise GraphQLError("Invalid phone format.")

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(
            customer=customer,
            message="Customer created successfully."
        )

# ----------------------------
# BulkCreateCustomers Mutation
# ----------------------------

class BulkCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(BulkCustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, customers):
        created = []
        errors = []

        for c in customers:
            try:
                if Customer.objects.filter(email=c.email).exists():
                    errors.append(f"Duplicate email: {c.email}")
                    continue

                if not validate_phone(c.phone):
                    errors.append(f"Invalid phone: {c.phone}")
                    continue

                customer = Customer.objects.create(
                    name=c.name,
                    email=c.email,
                    phone=c.phone
                )
                created.append(customer)

            except Exception as e:
                errors.append(str(e))

        return BulkCreateCustomers(customers=created, errors=errors)

# ----------------------------
# CreateProduct Mutation
# ----------------------------

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock):
        if price <= 0:
            raise GraphQLError("Price must be positive.")
        if stock < 0:
            raise GraphQLError("Stock cannot be negative.")

        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product)

# ----------------------------
# CreateOrder Mutation
# ----------------------------

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            raise GraphQLError("Invalid customer ID.")

        if not product_ids:
            raise GraphQLError("At least one product must be selected.")

        products = Product.objects.filter(id__in=product_ids)
        if products.count() != len(product_ids):
            raise GraphQLError("One or more product IDs are invalid.")

        total_amount = sum([p.price for p in products])

        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            order_date=order_date or timezone.now(),
        )

        order.products.set(products)
        return CreateOrder(order=order)

# ----------------------------
# Mutation Root
# ----------------------------

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

# ----------------------------
# Query Root
# ----------------------------

class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_orders(self, info):
        return Order.objects.all()

import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class Query(CRMQuery, graphene.ObjectType):
    pass

class Mutation(CRMMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)

mutation {
  createCustomer(name:"Alice", email:"alice@example.com", phone:"+1234567890") {
    customer {
      id
      name
      email
      phone
    }
    message
  }
}

mutation {
  bulkCreateCustomers(customers: [
    {name:"Bob", email:"bob@example.com", phone:"123-456-7890"},
    {name:"Carol", email:"carol@example.com"}
  ]) {
    customers { id name email }
    errors
  }
}

mutation {
  createProduct(name:"Laptop", price:999.99, stock:10) {
    product {
      id
      name
      price
      stock
    }
  }
}

mutation {
  createOrder(customerId:"1", productIds:["1","2"]) {
    order {
      id
      customer { name }
      products { name price }
      totalAmount
      orderDate
    }
  }
}




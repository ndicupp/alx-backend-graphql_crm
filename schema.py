# crm/models.py
from django.db import models
from django.core.validators import RegexValidator
from decimal import Decimal

class Customer(models.Model):
    name = models.CharField(max_length=255)
    # Ensure email is unique at the database level
    email = models.EmailField(unique=True) 
    # Use RegexValidator for basic phone format validation
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    # Ensure price is positive
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    # Stock cannot be negative
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    products = models.ManyToManyField(Product, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    # Stores the calculated total amount at the time of order creation
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00')) 

    def __str__(self):
        return f"Order {self.id} by {self.customer.name}"


python manage.py makemigrations crm
python manage.py migrate

# crm/schema.py

import graphene
from graphene_django.types import DjangoObjectType
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum
import re
from decimal import Decimal

# --- 1. Define GraphQL Types for Models (Output) ---

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        # Explicitly define fields for clarity and security
        fields = ('id', 'name', 'email', 'phone', 'date_joined')

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock')

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'order_date', 'total_amount')

# --- Helper Function for Phone Validation ---

def validate_phone(phone):
    """Basic validation for phone number format."""
    # Simplified regex for validation (e.g., handles digits, dashes, spaces, and optional +)
    if not phone:
        return True # phone is optional
    
    # Example regex: ^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$
    if not re.fullmatch(r'^\+?\d[\d\s-]{7,15}\d$', phone):
        raise ValidationError(f"Invalid phone format: '{phone}'. Use a format like +1234567890.")


# --- 2. Define Mutations (Input & Logic) ---

class CreateCustomer(graphene.Mutation):
    # Inputs (Defined as a nested class)
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    # Outputs
    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @classmethod
    @transaction.atomic
    def mutate(cls, root, info, name, email, phone=None):
        try:
            # Validation 1: Phone format
            if phone:
                validate_phone(phone)

            # Create the customer
            customer = Customer.objects.create(
                name=name,
                email=email,
                phone=phone
            )
            return CreateCustomer(
                customer=customer, 
                message=f"Customer '{name}' created successfully."
            )
        except IntegrityError:
            # Validation 2: Unique Email violation
            return CreateCustomer(
                customer=None, 
                message=f"Error: A customer with the email '{email}' already exists."
            )
        except ValidationError as e:
            # Validation 3: Other model/validator errors (e.g., phone format)
            return CreateCustomer(
                customer=None, 
                message=f"Validation Error: {', '.join(e.messages)}"
            )

# --- BulkCreateCustomers Implementation ---

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    # Outputs
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input):
        valid_customers = []
        errors = []
        
        # Challenge: Support partial success - process valid entries even if some fail
        for data in input:
            name = data.name
            email = data.email
            phone = data.phone
            
            error_msg = None
            
            # 1. Validate Phone Format
            try:
                validate_phone(phone)
            except ValidationError as e:
                error_msg = f"Record for '{email}': Phone validation error: {', '.join(e.messages)}"
            
            if error_msg:
                errors.append(error_msg)
                continue

            # 2. Add to list for bulk creation (Integrity check is handled by transaction)
            valid_customers.append(Customer(name=name, email=email, phone=phone))

        # Perform creation in a single atomic transaction
        with transaction.atomic():
            created_customers = []
            for cust in valid_customers:
                try:
                    cust.save()
                    created_customers.append(cust)
                except IntegrityError:
                    errors.append(f"Record for '{cust.email}': Email already exists.")
                except Exception as e:
                    errors.append(f"Record for '{cust.email}': An unexpected error occurred: {str(e)}")

        return BulkCreateCustomers(customers=created_customers, errors=errors)

# --- CreateProduct Implementation ---

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int(required=False, default_value=0)
    
    product = graphene.Field(ProductType)

    @classmethod
    @transaction.atomic
    def mutate(cls, root, info, name, price, stock=0):
        if price <= 0:
            raise Exception("Price must be a positive number.")
        if stock < 0:
            raise Exception("Stock cannot be negative.")

        product = Product.objects.create(
            name=name,
            price=price,
            stock=stock
        )
        return CreateProduct(product=product)

# --- CreateOrder Implementation ---

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        # order_date is auto_now_add, so no need to take it as input unless requested
    
    order = graphene.Field(OrderType)
    
    @classmethod
    @transaction.atomic
    def mutate(cls, root, info, customer_id, product_ids):
        # Validation 1: Ensure at least one product is selected
        if not product_ids:
            raise Exception("An order must contain at least one product.")
        
        try:
            # Validation 2: Ensure customer exists
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception(f"Invalid customer ID: {customer_id}")

        # Validation 3: Ensure all products exist and fetch them
        # Note: We use in_bulk to check existence and retrieve them efficiently
        product_pks = [pk for pk in product_ids]
        products_map = Product.objects.in_bulk(product_pks)
        
        if len(products_map) != len(product_pks):
            # Find the missing IDs
            found_pks = set(products_map.keys())
            missing_pks = [pk for pk in product_pks if pk not in found_pks]
            raise Exception(f"Invalid product IDs found: {', '.join(map(str, missing_pks))}")

        products = list(products_map.values())
        
        # Calculate total_amount
        total_amount = sum(p.price for p in products)
        
        # Create the order
        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount
        )
        # Associate products (Many-to-Many)
        order.products.set(products)

        return CreateOrder(order=order)


# --- 3. Combine Queries and Mutations (Root Schema) ---

class Query(graphene.ObjectType):
    # Placeholder for future queries (e.g., getting all customers)
    # Re-adding the 'hello' from Task 0 just in case
    hello = graphene.String(default_value="Hello, CRM GraphQL!")
    
    # Placeholder fields for fetching data
    all_customers = graphene.List(CustomerType)
    
    def resolve_all_customers(root, info):
        return Customer.objects.all()

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

# --- 4. Integrate Into Main Schema (alx_backend_graphql_crm/schema.py) ---

# This step is critical to combine the 'hello' query from the root schema
# with the new types/mutations from the 'crm' app.

# Open alx_backend_graphql_crm/schema.py (replace the content):

# alx_backend_graphql_crm/schema.py (Updated content)

# Import the base query and mutation classes from the 'crm' app
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

# Combine the Queries (using the 'hello' from the root if necessary, or just rely on crm)
class Query(CRMQuery, graphene.ObjectType):
    pass # Inherits all fields from CRMQuery

# Combine the Mutations
class Mutation(CRMMutation, graphene.ObjectType):
    pass # Inherits all fields from CRMMutation

schema = graphene.Schema(query=Query, mutation=Mutation)


mutation CreateCustomerMutation {
  createCustomer(input: {
    name: "Alice",
    email: "alice@example.com",
    phone: "+1234567890"
  }) {
    customer {
      id
      name
      email
      phone
    }
    message
  }
}

mutation BulkCreateMutation {
  bulkCreateCustomers(input: [
    { name: "Bob", email: "bob@example.com", phone: "123-456-7890" },
    { name: "Carol", email: "carol@example.com" }
    # Optional: Add a validation failure test case (e.g., duplicate email)
    # { name: "Failure Test", email: "alice@example.com" } 
  ]) {
    customers {
      id
      name
      email
    }
    errors
  }
}

mutation CreateProductMutation {
  laptop: createProduct(input: {
    name: "Laptop Pro",
    price: 1999.99,
    stock: 5
  }) {
    product { id name price stock }
  }
  monitor: createProduct(input: {
    name: "4k Monitor",
    price: 599.00,
    stock: 12
  }) {
    product { id name price stock }
  }
}

mutation CreateOrderMutation {
  createOrder(input: {
    customerId: "1", # Alice's ID (e.g., 1)
    productIds: ["1", "2"] # Laptop Pro (1) and 4k Monitor (2)
  }) {
    order {
      id
      customer {
        name
      }
      products {
        name
        price
      }
      totalAmount # Should be 1999.99 + 599.00 = 2598.99
      orderDate
    }
  }
}

query FilterCustomers {
  allCustomers(name_Icontains: "Ali") {
    edges {
      node {
        id
        name
        email
      }
    }
  }
}

query PaginateProducts {
  allProducts(first: 2) {
    edges {
      node {
        id
        name
        price
      }
    }
  }
}



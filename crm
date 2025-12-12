django-admin startproject alx_backend_graphql_crm
cd alx_backend_graphql_crm

python manage.py startapp crm

pip install graphene-django django-filter

alx_backend_graphql_crm/settings.py

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "graphene_django",

    # Local app
    "crm",
]

GRAPHENE = {
    "SCHEMA": "alx_backend_graphql_crm.schema.schema"
}


alx_backend_graphql_crm/schema.py

import graphene

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

schema = graphene.Schema(query=Query)

alx_backend_graphql_crm/urls.py

from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('admin/', admin.site.urls),
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
]

python manage.py runserver

Open:

http://localhost:8000/graphql

Run this in the GraphiQL editor:

{
  hello
}

Expected output:

{
  "data": {
    "hello": "Hello, GraphQL!"
  }
}



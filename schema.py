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


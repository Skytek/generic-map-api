from django.urls import path

from .views import all_meta

urlpatterns = [
    path("_meta/", all_meta),
]

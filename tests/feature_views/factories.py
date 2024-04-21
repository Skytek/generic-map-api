import urllib
import urllib.parse

from django.http.request import HttpRequest, QueryDict
from rest_framework.request import Request


def request_factory(query_params=None):
    query_params = query_params or {}

    query_string = urllib.parse.urlencode(query_params)

    django_request = HttpRequest()
    django_request.GET = QueryDict(query_string)

    return Request(django_request)

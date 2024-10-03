from django.urls import get_resolver
from rest_framework.decorators import api_view
from rest_framework.response import Response

from generic_map_api.views import MapApiBaseView


def _get_all_meta(request):
    meta_suffix = "_meta/"
    all_views = get_resolver().reverse_dict.items()
    for view, urls in all_views:
        if not callable(view) or not hasattr(view, "cls"):
            continue
        if not issubclass(view.cls, MapApiBaseView):
            continue
        try:
            url = urls[0][0][0]
        except IndexError:
            continue

        if url.endswith("/" + meta_suffix):
            meta_response = view(request)
            if meta_response.status_code == 200:
                yield url[: -len(meta_suffix)], meta_response.data


@api_view()
def all_meta(request):
    django_request = request._request  # pylint: disable=protected-access
    response = {
        "multi-meta": {
            request.build_absolute_uri("/" + url): meta
            for url, meta in _get_all_meta(django_request)
        }
    }
    return Response(response)

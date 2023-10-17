from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from os import path

from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .clustering import Clustering
from .serializers import BaseFeatureSerializer, ClusterSerializer
from .values import BaseViewPort, Tile, ViewPort


class MapApiBaseMeta(ABCMeta):
    def __new__(cls, name, bases, namespace, /, **kwargs):
        if "query_params" in namespace:
            for param_name, param in namespace["query_params"].items():
                param.name = param_name
        return super().__new__(cls, name, bases, namespace, **kwargs)


class MapApiBaseView(ABC, ViewSet, metaclass=MapApiBaseMeta):
    display_name: str = None
    query_params = {}
    has_parametrized_meta = False

    trailing_slash = None

    @action(detail=False, url_path="_meta")
    def meta(self, request):
        meta = self.get_meta(request)
        if self.has_parametrized_meta and "urls" in meta:
            meta["urls"]["parametrized_meta"] = self.reverse_action("parametrized-meta")
        return Response(meta)

    @action(detail=False, url_path="_meta/parametrized")
    def parametrized_meta(self, request):
        params = self._parse_params(request)
        return Response(self.get_parametrized_meta(request, params))

    @abstractmethod
    def get_meta(self, request):
        pass

    def get_parametrized_meta(self, request, params):  # pylint: disable=unused-argument
        return {}

    @action(detail=False, url_path="_meta/query_param/(?P<query_param>[^/.]+)/options")
    def query_param_options(self, request, query_param):
        try:
            parameter = self.get_query_params()[query_param]
        except KeyError:
            return Response(status=404)

        try:
            return Response(parameter.render_options(request))
        except NotImplementedError:
            return Response(status=504)

    def get_query_params(self):
        return self.query_params

    def _render_query_params_meta(self, request):
        return {
            param.name: param.render_meta(self, request)
            for param in self.get_query_params().values()
        }

    def _parse_params(self, request):
        return {
            param: value
            for param, value in {
                param.name: param.parse_request(request)
                for param in self.query_params.values()
            }.items()
            if value is not None
        }


class MapFeaturesBaseView(MapApiBaseView):
    serializer: BaseFeatureSerializer = None
    clustering: bool = False
    clustering_serializer: BaseFeatureSerializer = ClusterSerializer()

    require_viewport_zoom: bool = False
    require_viewport_size: bool = False

    preferred_viewport_handling: str = "viewport"

    def get_meta(self, request):
        return {
            "type": "Features",
            "name": self.display_name,
            "clustering": self.clustering,
            "preferred_viewport_handling": self.preferred_viewport_handling,
            "query_params": self._render_query_params_meta(request),
            "requirements": self._render_requirements(request),
            "urls": {
                "list": self.reverse_action("list"),
                "detail": self.reverse_action("detail", kwargs={"pk": "ID"}),
            },
        }

    def list(self, request):
        viewport = None

        if "tile" in request.GET:
            viewport = Tile.from_query_param(request.GET.get("tile", None))

        elif "viewport" in request.GET:
            viewport = ViewPort.from_geohashes_query_param(
                request.GET.get("viewport", None)
            )

        params = self._parse_params(request)
        clustering_config = self._parse_clustering_config(request)

        items = self.get_items(viewport, params)

        if clustering_config:
            serialized_items = Clustering(self.clustering_serializer).find_clusters(
                clustering_config, (self._render_item(item) for item in items)
            )
        else:
            serialized_items = (self._render_item(item) for item in items)

        response = {
            "items": list(serialized_items),
            "legend": None,  # @TODO build legend
        }
        return Response(response)

    def _parse_clustering_config(self, request):
        config = {}
        params = ("", "viewport", "eps")

        for param in params:
            key = f"clustering.{param}" if param else "clustering"
            if key in request.GET:
                config[param] = request.GET.get(key)

        return config

    def _render_requirements(self, request):  # pylint: disable=unused-argument
        requirements = []
        if self.require_viewport_size:
            requirements.append("viewport.size")
        if self.require_viewport_zoom:
            requirements.append("viewport.zoom")
        return requirements

    def retrieve(self, request, pk):  # pylint: disable=unused-argument
        response = {"item": self._render_detailed_item(self.get_item(item_id=pk))}
        return Response(response)

    @abstractmethod
    def get_items(self, viewport: BaseViewPort, params: dict):
        pass

    @abstractmethod
    def get_item(self, item_id):
        pass

    def _render_item(self, item):
        return self.serializer.serialize(item)

    def _render_detailed_item(self, item):
        return self.serializer.serialize_details(item)

    def _sanity_check(self):
        # @TODO check configuration here
        ...


class MapTilesBaseView(MapApiBaseView):
    def get_meta(self, request):
        return {
            "type": "Tiles",
            "name": self.display_name,
            "query_params": self._render_query_params_meta(request),
            "urls": {
                "tile": self.make_pattern_url(
                    "tile",
                    kwargs={
                        param: "{" + param + "}" for param in self.get_url_params()
                    },
                ),
            },
        }

    def make_pattern_url(self, action_name, kwargs):
        url = self.reverse_action(action_name, kwargs=kwargs)
        url = url.replace("%7B", "{")
        url = url.replace("%7D", "}")
        return url

    def get_url_params(self):
        return ("x", "y", "z")

    @action(
        detail=False,
        url_path=r"(?P<z>[^/.]+)/(?P<x>[^/.]+)/(?P<y>[^/.]+).png",
        trailing_slash=False,
    )
    def tile(self, request, z, x, y):
        params = self._parse_params(request)
        tile_bytes = self.get_tile(z, x, y, params)
        if not tile_bytes:
            return self.render_empty_response(request, z, x, y)
        return HttpResponse(tile_bytes, content_type="image/png")

    @abstractmethod
    def get_tile(self, z: int, x: int, y: int, params: dict) -> bytes:
        pass

    def render_empty_response(
        self, request, z, x, y
    ):  # pylint: disable=unused-argument
        empty_tile = path.join(path.dirname(__file__), "resources", "empty_tile.png")
        with open(empty_tile, "br") as f:
            tile_bytes = f.read()
        return HttpResponse(tile_bytes, content_type="image/png")

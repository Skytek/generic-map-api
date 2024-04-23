from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from base64 import b64encode
from os import path
from typing import Callable, Optional, Tuple, Type

from django.core.exceptions import BadRequest
from django.db.models import QuerySet
from django.http import Http404, HttpResponse
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .bounding_box import AutomaticBoundingBoxing
from .clustering import BaseClustering, BasicClustering, ClusteringOutput
from .constants import ViewportHandling
from .serializers import BaseFeatureSerializer, BoundingBoxSerializer
from .utils import to_bool
from .values import BaseViewPort, BoundingBox, EmptyViewport, Tile, ViewPort


class MapApiBaseMeta(ABCMeta):
    def __new__(cls, name, bases, namespace, /, **kwargs):
        if "query_params" in namespace:
            for param_name, param in namespace["query_params"].items():
                param.name = param_name
        return super().__new__(cls, name, bases, namespace, **kwargs)


class MapApiBaseView(ABC, ViewSet, metaclass=MapApiBaseMeta):
    display_name: str = None
    api_id: Optional[str] = None
    category: Tuple[str] = []
    icon = path.join(path.dirname(__file__), "resources", "icons", "default.png")

    query_params = {}
    has_parametrized_meta = False

    trailing_slash = None

    get_bounds: Callable[[dict, Request], BoundingBox] | None = None

    @action(detail=False, url_path="_meta")
    def meta(self, request):
        meta = self.get_meta(request)
        if not "urls" in meta:
            meta["urls"] = {}
        meta["urls"] = {
            **meta["urls"],
            **self.get_urls(),
        }
        return Response(meta)

    @action(detail=False, url_path="_meta/parametrized")
    def parametrized_meta(self, request):
        params = self._parse_params(request)
        return Response(self.get_parametrized_meta(request, params))

    @action(detail=False, url_path="bounds")
    def bounds(self, request):
        if not callable(self.get_bounds):
            raise BadRequest()

        params = self._parse_params(request)
        bounds = self.get_bounds(params, request)  # pylint: disable=not-callable
        return Response(BoundingBoxSerializer(bounds).data)

    @abstractmethod
    def get_meta(self, request):
        pass

    def get_parametrized_meta(self, request, params):  # pylint: disable=unused-argument
        return {}

    def get_urls(self):
        urls = {
            "meta": self.reverse_action("meta"),
        }
        get_bounds_implemented = self.get_bounds is not None
        if get_bounds_implemented:
            urls["bounds"] = self.reverse_action("bounds")
        if self.has_parametrized_meta:
            urls["parametrized_meta"] = self.reverse_action("parametrized-meta")
        return urls

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

    def render_query_params_meta(self, request):
        return {
            param.name: param.render_meta(self, request)
            for param in self.get_query_params().values()
        }

    def get_icon(self) -> str:
        file_path = self.icon
        extension = file_path.split(".")[-1]
        with open(file_path, "rb") as f:
            data = b64encode(f.read()).decode("utf-8")

        return f"data:image/{extension};base64,{data}"

    def _parse_params(self, request):
        return {
            param: value
            for param, value in self._parse_params_inner(request)
            if value is not None
        }

    def _parse_params_inner(self, request):
        for param in self.query_params.values():
            yield param.name, param.parse_request(request)


class MapFeaturesBaseView(MapApiBaseView):
    icon = path.join(
        path.dirname(__file__), "resources", "icons", "default-features.png"
    )
    serializer: BaseFeatureSerializer = None
    clustering: bool = False
    clustering_class: Type[BaseClustering] = BasicClustering

    bounding_box_db_geometry_field = None

    require_viewport_zoom: bool = False
    require_viewport_size: bool = False
    require_viewport_meters_per_pixel: bool = False

    preferred_viewport_handling: str = ViewportHandling.SPLIT
    preferred_viewport_chunks: int = 10

    def get_bounds(self, params, request):  # pylint: disable=unused-argument
        viewport = EmptyViewport()
        items = self.get_items(viewport, params)
        return AutomaticBoundingBoxing().find_bounding_box(self, items)

    def get_urls(self):
        urls = super().get_urls()
        urls.update(
            {
                "list": self.reverse_action("list"),
                "detail": self.reverse_action("detail", kwargs={"pk": "ID"}),
            }
        )
        return urls

    def get_meta(self, request):
        return {
            "type": "Features",
            "id": self.api_id,
            "name": self.display_name,
            "category": self.category,
            "icon": self.get_icon(),
            "clustering": self.clustering,
            "preferred_viewport_handling": self.preferred_viewport_handling.value
            if isinstance(self.preferred_viewport_handling, ViewportHandling)
            else self.preferred_viewport_handling,
            "preferred_viewport_chunks": self.preferred_viewport_chunks,
            "query_params": self.render_query_params_meta(request),
            "requirements": self.render_requirements(request),
        }

    def list(self, request):
        viewport = EmptyViewport()

        if "tile" in request.GET:
            viewport = Tile.from_query_param(request.GET.get("tile", None))

        elif "viewport" in request.GET:
            viewport = ViewPort.from_geohashes_query_param(
                request.GET.get("viewport", None)
            )

        if "viewport.zoom" in request.GET:
            viewport.zoom = request.GET["viewport.zoom"]

        if "viewport.mpp" in request.GET:
            viewport.meters_per_pixel = request.GET["viewport.mpp"]

        if "viewport.size" in request.GET:
            viewport.size = tuple(request.GET["viewport.size"].split("x"))

        viewport.clustering = to_bool(request.GET.get("clustering", False))

        params = self._parse_params(request)

        items = self.get_items(viewport, params)

        if self.clustering and viewport.clustering:
            clusters = self.get_clustering_algorithm().find_clusters(
                self, viewport, items
            )
            serialized_items = (self.render_cluster_item(item) for item in clusters)
        else:
            if isinstance(items, QuerySet):
                items = items.iterator()
            serialized_items = (self.render_item(item) for item in items)

        response = {
            "items": list(serialized_items),
        }
        return Response(response)

    def render_requirements(self, request):  # pylint: disable=unused-argument
        requirements = []
        if self.require_viewport_size:
            requirements.append("viewport.size")
        if self.require_viewport_zoom:
            requirements.append("viewport.zoom")
        if self.require_viewport_meters_per_pixel:
            requirements.append("viewport.mpp")
        return requirements

    def retrieve(self, request, pk):  # pylint: disable=unused-argument
        item = self.get_item(item_id=pk)  # pylint: disable=assignment-from-none
        if not item:
            raise Http404()

        response = {"item": self.render_detailed_item(item)}
        return Response(response)

    @abstractmethod
    def get_items(self, viewport: BaseViewPort, params: dict):
        pass

    def get_item(self, item_id):  # pylint: disable=unused-argument
        return None

    def get_serializer(self, item):  # pylint: disable=unused-argument
        return self.serializer

    def render_item(self, item):
        return self.get_serializer(item).serialize(item)

    def render_cluster_item(self, item: ClusteringOutput):
        if item.is_cluster:
            return self.get_serializer(item.item).serialize_cluster(item.item)
        return self.get_serializer(item.item).serialize(item.item)

    def render_detailed_item(self, item):
        return self.get_serializer(item).serialize_details(item)

    def get_clustering_algorithm(self) -> BaseClustering:
        return self.clustering_class()


class MapTilesBaseView(MapApiBaseView):
    icon = path.join(path.dirname(__file__), "resources", "icons", "default-tiles.png")

    def get_urls(self):
        urls = super().get_urls()
        urls.update(
            {
                "tile": self.make_pattern_url(
                    "tile",
                    kwargs={
                        param: "{" + param + "}" for param in self.get_url_params()
                    },
                ),
            }
        )
        return urls

    def get_meta(self, request):
        return {
            "type": "Tiles",
            "id": self.api_id,
            "name": self.display_name,
            "category": self.category,
            "icon": self.get_icon(),
            "query_params": self.render_query_params_meta(request),
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

from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .clustering import Clustering
from .serializers import BaseFeatureSerializer, ClusterSerializer
from .values import ViewPort


class MapApiBaseMeta(ABCMeta):
    def __new__(cls, name, bases, namespace, /, **kwargs):
        for param_name, param in namespace["query_params"].items():
            param.name = param_name
        return super().__new__(cls, name, bases, namespace, **kwargs)


class MapApiBaseView(ABC, ViewSet, metaclass=MapApiBaseMeta):
    serializer: BaseFeatureSerializer = None
    clustering: bool = False
    display_name: str = None
    query_params = {}
    clustering_serializer: BaseFeatureSerializer = ClusterSerializer()

    @action(detail=False, url_path="_meta")
    def meta(self, request):  # pylint: disable=unused-argument
        meta = {
            "type": "Features",
            "name": self.display_name,
            "clustering": self.clustering,
            "query_params": self._render_query_params_meta(request),
            "urls": {
                "list": self.reverse_action("list"),
                "detail": self.reverse_action("detail", kwargs={"pk": "ID"}),
            },
        }
        return Response(meta)

    def list(self, request):
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

    def retrieve(self, request, pk):  # pylint: disable=unused-argument
        response = {
            "item": None,  # @TODO
        }
        return Response(response)

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

    @abstractmethod
    def get_items(self, viewport: ViewPort, filters: dict):
        pass

    @abstractmethod
    def get_item(self, id):  # pylint: disable=redefined-builtin
        pass

    def get_query_params(self):
        return self.query_params

    def _render_query_params_meta(self, request):
        return {
            param.name: param.render_meta(self, request)
            for param in self.get_query_params().values()
        }

    def _render_item(self, item):
        return self.serializer.serialize(item)

    def _sanity_check(self):
        # @TODO check configuration here
        ...

    def _parse_params(self, request):
        return {
            param: value
            for param, value in {
                param.name: param.parse_request(request)
                for param in self.query_params.values()
            }.items()
            if value is not None
        }

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
from django.db.models import QuerySet
from shapely.geometry import MultiPoint, MultiPolygon, Point
from sklearn.cluster import DBSCAN

if TYPE_CHECKING:
    from .values import BaseViewPort
    from .views import MapFeaturesBaseView


@dataclass
class ClusteringOutput:
    is_cluster: bool
    item: Any


class BaseClustering:
    def __init__(self) -> None:
        self.view = None

    def find_clusters(self, view: MapFeaturesBaseView, viewport: BaseViewPort, items):
        raise NotImplementedError()


class DatabaseClustering(BaseClustering):
    def find_clusters(self, view: MapFeaturesBaseView, viewport: BaseViewPort, items):
        if not isinstance(items, QuerySet):
            raise ValueError("Database clustering requires QuerySet on input")

        raise NotImplementedError()


class BasicClustering:
    @dataclass
    class Cluster:
        centroid: Point
        shape: MultiPolygon
        items: list

    def find_clusters(  # pylint: disable=too-many-locals
        self,
        view: MapFeaturesBaseView,
        viewport: BaseViewPort,
        items,
    ):
        config = view.get_clustering_config()

        include_orphans = config.get("include_orphans", False)

        def default_item_to_point(item):
            try:
                geom = view.serializer.get_geometry(item)
                return geom.centroid
            except (ValueError, AttributeError):
                return None

        item_to_point = config.get("item_to_point", default_item_to_point)

        items_to_cluster = []
        points_to_cluster = []
        for item in items:
            point = item_to_point(item)

            if point:
                items_to_cluster.append(item)
                points_to_cluster.append(point)
            else:
                if include_orphans:
                    yield ClusteringOutput(
                        is_cluster=False,
                        item=item,
                    )

        if not points_to_cluster:
            return

        dataset = np.array(points_to_cluster)

        clustering = DBSCAN(**self.get_clustering_params(config, viewport)).fit(dataset)

        labels = clustering.labels_

        clusters = {}
        for label, item, point in zip(labels, items_to_cluster, points_to_cluster):
            if label < 0:
                if include_orphans:
                    yield ClusteringOutput(
                        is_cluster=False,
                        item=item,
                    )
            else:
                if label not in clusters:
                    clusters[label] = {"points": [], "items": []}
                clusters[label]["points"].append(point)
                clusters[label]["items"].append(item)

        for cluster in clusters.values():
            multipoint = MultiPoint(cluster["points"])
            multipolygon = MultiPolygon([multipoint.convex_hull])
            cluster_obj = self.Cluster(
                centroid=multipolygon.centroid,
                shape=multipolygon,
                items=cluster["items"],
            )
            yield ClusteringOutput(
                is_cluster=True,
                item=cluster_obj,
            )

    def get_clustering_params(self, in_config, viewport):
        config = {
            "eps": 0.01,
            "eps_factor": 0.01,
            "max_eps": 1.3,
            "p": 2,
            "min_samples": 5,
        }

        algorithm_params = ("eps", "p", "min_samples")

        if "eps_factor" in in_config:
            config["eps_factor"] = float(in_config["eps_factor"])

        if viewport:
            eps = config["eps_factor"] * sum(viewport.get_dimensions()) / 2
            config["eps"] = eps
        elif "eps" in in_config:
            config["eps"] = float(in_config["eps"])

        if config["eps"] > config["max_eps"]:
            config["eps"] = config["max_eps"]

        return {k: v for k, v in config.items() if k in algorithm_params}

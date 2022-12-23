from dataclasses import dataclass

import numpy as np
from shapely.geometry import MultiPoint, Point
from sklearn.cluster import DBSCAN

from .geometry_serializers import flip_coords
from .serializers import BaseFeatureSerializer
from .values import ViewPort


@dataclass
class Cluster:
    centroid: Point
    points: MultiPoint
    items: list


class Clustering:
    def __init__(self, serializer: BaseFeatureSerializer) -> None:
        self.serializer = serializer

    def item_to_point(self, item: dict):
        if "point" in item["type"]:
            return flip_coords(item["geom"])
        return None

    def find_clusters(self, config, serialized_items):
        items_to_cluster = []
        points_to_cluster = []

        for item in serialized_items:
            point = self.item_to_point(item)

            if point:
                items_to_cluster.append(item)
                points_to_cluster.append(point)
            else:
                yield item

        if not points_to_cluster:
            return

        dataset = np.array(points_to_cluster)

        clustering = DBSCAN(**self.get_clustering_params(config)).fit(dataset)

        labels = clustering.labels_

        clusters = {}
        for label, item, point in zip(labels, items_to_cluster, points_to_cluster):
            if label < 0:
                yield item
            else:
                if label not in clusters:
                    clusters[label] = {"points": [], "items": []}
                clusters[label]["points"].append(point)
                clusters[label]["items"].append(item)

        for cluster in clusters.values():
            multipoint = MultiPoint(cluster["points"])
            cluster = Cluster(
                centroid=multipoint.centroid, points=multipoint, items=cluster["items"]
            )
            yield self.serializer.serialize(cluster)

    def get_clustering_params(self, in_config):
        config = {
            "eps": 0.01,
            "eps_factor": 0.01,
            "max_eps": 1.3,
        }

        algorithm_params = ("eps",)

        if "eps_factor" in in_config:
            config["eps_factor"] = float(in_config["eps_factor"])

        if "viewport" in in_config:
            viewport = ViewPort.from_geohashes_query_param(in_config["viewport"])
            eps = config["eps_factor"] * sum(viewport.get_dimensions()) / 2
            config["eps"] = eps
        elif "eps" in in_config:
            config["eps"] = float(in_config["eps"])

        if config["eps"] > config["max_eps"]:
            config["eps"] = config["max_eps"]

        return {k: v for k, v in config.items() if k in algorithm_params}

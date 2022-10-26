from abc import ABC, ABCMeta, abstractmethod
from typing import Tuple

from django.contrib.gis.geos import LineString as GeosLineString
from django.contrib.gis.geos import MultiPolygon as GeosMultiPolygon
from django.contrib.gis.geos import Point as GeosPoint
from django.contrib.gis.geos import Polygon as GeosPolygon
from shapely.geometry import LineString as ShapelyLineString
from shapely.geometry import MultiPolygon as ShapelyMultiPolygon
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon as ShapelyPolygon


def flip_coords(lon_lat: Tuple[float, float]):
    return lon_lat[1], lon_lat[0]


class FeatureSerializerMeta(ABCMeta):
    def __new__(cls, name, bases, namespace, /, **kwargs):
        created_class = super().__new__(cls, name, bases, namespace, **kwargs)
        created_class.feature_types = cls._build_feature_type_list(created_class)
        return created_class

    @classmethod
    def _build_feature_type_list(cls, created_class):
        return tuple(
            c.feature_type
            for c in created_class.__mro__
            if getattr(c, "feature_type", None)
        )


class BaseFeatureSerializer(ABC, metaclass=FeatureSerializerMeta):
    feature_type = None
    feature_types = ()

    def serialize(self, obj):
        return {
            "type": self.get_type(obj),
            "id": self.get_id(obj),
            "geom": self.get_frontend_style_geometry(obj),
        }

    def get_type(self, obj):  # pylint: disable=unused-argument
        return self.feature_types

    def get_id(self, obj):  # pylint: disable=unused-argument
        return None

    def get_geometry(self, obj):  # pylint: disable=unused-argument
        return None

    @abstractmethod
    def make_frontend_style_geometry(self, geometry):
        pass

    def get_frontend_style_geometry(self, obj):
        geometry = self.get_geometry(obj)  # pylint: disable=assignment-from-none
        return self.make_frontend_style_geometry(geometry)


class PointSerializer(BaseFeatureSerializer):
    feature_type = "point"

    def make_frontend_style_geometry(self, geometry):
        if isinstance(geometry, GeosPoint):
            return flip_coords(geometry.coords)
        if isinstance(geometry, ShapelyPoint):
            return flip_coords(geometry.coords[0])
        raise ValueError()


class LineSerializer(BaseFeatureSerializer):
    feature_type = "line"

    def make_frontend_style_geometry(self, geometry):
        if isinstance(geometry, (GeosLineString, ShapelyLineString)):
            return tuple(flip_coords(point) for point in geometry.coords)
        raise ValueError()


class PolygonSerializer(BaseFeatureSerializer):
    feature_type = "polygon"

    def make_frontend_style_geometry(self, geometry):
        if isinstance(geometry, GeosPolygon):
            return tuple(flip_coords(point) for point in geometry.shell.coords)
        if isinstance(geometry, ShapelyPolygon):
            ...  # @TODO
        raise ValueError()


class MultiPolygonSerializer(BaseFeatureSerializer):
    feature_type = "multipolygon"

    def make_frontend_style_geometry(self, geometry):
        if isinstance(geometry, GeosMultiPolygon):
            ...  # @TODO
        if isinstance(geometry, ShapelyMultiPolygon):
            ...  # @TODO
        raise ValueError()


class ClusterSerializer(PointSerializer):
    feature_type = "cluster"

    def serialize(self, obj):
        return {
            "type": self.get_type(obj),
            "geom": self.get_frontend_style_geometry(obj),
            "count": len(obj.items),
        }

    def get_geometry(self, obj):
        return obj.centroid

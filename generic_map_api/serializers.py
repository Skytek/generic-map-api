from abc import ABC, ABCMeta, abstractmethod
from typing import Tuple, Union

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


def make_boundary_box_from_geos_geometry(
    geometry,
) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
    if isinstance(geometry, GeosPoint):
        return flip_coords(geometry.coords)

    envelope = geometry.envelope
    if isinstance(envelope, GeosPoint):
        return flip_coords(envelope.coords)

    coords = envelope.shell.coords
    return flip_coords(coords[0]), flip_coords(coords[2])


def make_boundary_box_from_shapely_geometry(
    geometry,
) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
    if isinstance(geometry, ShapelyPoint):
        return flip_coords(geometry.coords[0])

    bounds = geometry.bounds
    return flip_coords(bounds[0:2]), flip_coords(bounds[2:4])


class FeatureSerializerMeta(ABCMeta):
    def __new__(cls, name, bases, namespace, /, **kwargs):
        created_class = super().__new__(cls, name, bases, namespace, **kwargs)
        created_class.feature_types = cls._build_feature_type_list(created_class)
        return created_class

    @classmethod
    def _build_feature_type_list(cls, created_class):
        return tuple(
            {
                c.feature_type: None
                for c in created_class.__mro__
                if getattr(c, "feature_type", None)
            }.keys()
        )


class BaseFeatureSerializer(ABC, metaclass=FeatureSerializerMeta):
    feature_type = None
    feature_types = ()

    def serialize(self, obj):
        return {
            "type": self.get_type(obj),
            "id": self.get_id(obj),
            "geom": self.get_frontend_style_geometry(obj),
            "bbox": self.get_boundary_box(obj),
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

    @abstractmethod
    def make_boundary_box(
        self, geometry
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        pass

    def get_frontend_style_geometry(self, obj):
        geometry = self.get_geometry(obj)  # pylint: disable=assignment-from-none
        return self.make_frontend_style_geometry(geometry)

    def get_boundary_box(
        self, obj
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        geometry = self.get_geometry(obj)  # pylint: disable=assignment-from-none
        return self.make_boundary_box(geometry)


class PointSerializer(BaseFeatureSerializer):
    feature_type = "point"

    def make_frontend_style_geometry(self, geometry):
        if isinstance(geometry, GeosPoint):
            return flip_coords(geometry.coords)
        if isinstance(geometry, ShapelyPoint):
            return flip_coords(geometry.coords[0])
        raise ValueError(
            f"Cannot make frontend geometry from {geometry.__class__} in {self.__class__}"
        )

    def make_boundary_box(
        self, geometry
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        if isinstance(geometry, ShapelyPoint):
            return make_boundary_box_from_shapely_geometry(geometry)
        if isinstance(geometry, GeosPoint):
            return make_boundary_box_from_geos_geometry(geometry)
        raise ValueError(
            f"Cannot get boundary box of {geometry.__class__} in {self.__class__}"
        )


class LineSerializer(BaseFeatureSerializer):
    feature_type = "line"

    def make_frontend_style_geometry(self, geometry):
        if isinstance(geometry, (GeosLineString, ShapelyLineString)):
            return tuple(flip_coords(point) for point in geometry.coords)
        raise ValueError(
            f"Cannot make frontend geometry from {geometry.__class__} in {self.__class__}"
        )

    def make_boundary_box(
        self, geometry
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        if isinstance(geometry, ShapelyLineString):
            return make_boundary_box_from_shapely_geometry(geometry)
        if isinstance(geometry, GeosLineString):
            return make_boundary_box_from_geos_geometry(geometry)
        raise ValueError(
            f"Cannot get boundary box of {geometry.__class__} in {self.__class__}"
        )


class PolygonSerializer(BaseFeatureSerializer):
    feature_type = "polygon"

    def make_frontend_style_geometry(self, geometry):
        if isinstance(geometry, GeosPolygon):
            if len(geometry) == 1:
                return tuple(flip_coords(point) for point in geometry.shell.coords)

            return tuple(
                tuple(flip_coords(point) for point in ring.coords) for ring in geometry
            )
        if isinstance(geometry, ShapelyPolygon):
            if not geometry.interiors:
                return tuple(flip_coords(point) for point in geometry.exterior.coords)

            return tuple(
                tuple(flip_coords(point) for point in ring.coords)
                for ring in (geometry.exterior,) + tuple(geometry.interiors)
            )
        raise ValueError(
            f"Cannot make frontend geometry from {geometry.__class__} in {self.__class__}"
        )

    def make_boundary_box(
        self, geometry
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        if isinstance(geometry, ShapelyPolygon):
            return make_boundary_box_from_shapely_geometry(geometry)
        if isinstance(geometry, GeosPolygon):
            return make_boundary_box_from_geos_geometry(geometry)
        raise ValueError(
            f"Cannot get boundary box of {geometry.__class__} in {self.__class__}"
        )


class MultiPolygonSerializer(BaseFeatureSerializer):
    feature_type = "multipolygon"

    def make_frontend_style_geometry(self, geometry):
        if isinstance(geometry, GeosMultiPolygon):
            return tuple(
                tuple(
                    tuple(flip_coords(point) for point in ring.coords)
                    for ring in polygon
                )
                for polygon in geometry
            )
        if isinstance(geometry, ShapelyMultiPolygon):
            return tuple(
                tuple(
                    tuple(flip_coords(point) for point in ring.coords)
                    for ring in (polygon.exterior,) + tuple(polygon.interiors)
                )
                for polygon in geometry.geoms
            )
        raise ValueError(
            f"Cannot make frontend geometry from {geometry.__class__} in {self.__class__}"
        )

    def make_boundary_box(
        self, geometry
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        if isinstance(geometry, ShapelyMultiPolygon):
            return make_boundary_box_from_shapely_geometry(geometry)
        if isinstance(geometry, GeosMultiPolygon):
            return make_boundary_box_from_geos_geometry(geometry)
        raise ValueError(
            f"Cannot get boundary box of {geometry.__class__} in {self.__class__}"
        )


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

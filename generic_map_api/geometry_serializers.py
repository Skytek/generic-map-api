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


class ShapelySerializer:
    supported_shapes = (
        ShapelyPoint,
        ShapelyLineString,
        ShapelyPolygon,
        ShapelyMultiPolygon,
    )

    @classmethod
    def can_serialize(cls, geometry):
        return isinstance(geometry, cls.supported_shapes)

    @classmethod
    def get_feature_type(cls, geometry):
        if isinstance(geometry, ShapelyPoint):
            return "point"
        if isinstance(geometry, ShapelyLineString):
            return "line"
        if isinstance(geometry, ShapelyPolygon):
            return "polygon"
        if isinstance(geometry, ShapelyMultiPolygon):
            return "multipolygon"
        return None

    @classmethod
    def serialize(cls, geometry):
        if isinstance(geometry, ShapelyPoint):
            return flip_coords(geometry.coords[0])

        if isinstance(geometry, ShapelyLineString):
            return tuple(flip_coords(point) for point in geometry.coords)

        if isinstance(geometry, ShapelyPolygon):
            if not geometry.interiors:
                return tuple(flip_coords(point) for point in geometry.exterior.coords)

            return tuple(
                tuple(flip_coords(point) for point in ring.coords)
                for ring in (geometry.exterior,) + tuple(geometry.interiors)
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
            f"Cannot serialize geometry object of type {geometry.__class__}"
        )

    @classmethod
    def make_boundary_box(
        cls,
        geometry,
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        if isinstance(geometry, ShapelyPoint):
            return flip_coords(geometry.coords[0])

        bounds = geometry.bounds
        return flip_coords(bounds[0:2]), flip_coords(bounds[2:4])


class GeosSerializer:
    supported_shapes = (GeosPoint, GeosLineString, GeosPolygon, GeosMultiPolygon)

    @classmethod
    def can_serialize(cls, geometry):
        return isinstance(geometry, cls.supported_shapes)

    @classmethod
    def get_feature_type(cls, geometry):
        if isinstance(geometry, GeosPoint):
            return "point"
        if isinstance(geometry, GeosLineString):
            return "line"
        if isinstance(geometry, GeosPolygon):
            return "polygon"
        if isinstance(geometry, GeosMultiPolygon):
            return "multipolygon"
        return None

    @classmethod
    def serialize(cls, geometry):
        if isinstance(geometry, GeosPoint):
            return flip_coords(geometry.coords)

        if isinstance(geometry, GeosLineString):
            return tuple(flip_coords(point) for point in geometry.coords)

        if isinstance(geometry, GeosPolygon):
            if len(geometry) == 1:
                return tuple(flip_coords(point) for point in geometry.shell.coords)

            return tuple(
                tuple(flip_coords(point) for point in ring.coords) for ring in geometry
            )

        if isinstance(geometry, GeosMultiPolygon):
            return tuple(
                tuple(
                    tuple(flip_coords(point) for point in ring.coords)
                    for ring in polygon
                )
                for polygon in geometry
            )
        raise ValueError(
            f"Cannot serialize geometry object of type {geometry.__class__}"
        )

    @classmethod
    def make_boundary_box(
        cls,
        geometry,
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        if isinstance(geometry, GeosPoint):
            return flip_coords(geometry.coords)

        envelope = geometry.envelope
        if isinstance(envelope, GeosPoint):
            return flip_coords(envelope.coords)

        coords = envelope.shell.coords
        return flip_coords(coords[0]), flip_coords(coords[2])


class GeoJsonSerializer:
    supported_shapes = ("Point", "LineString", "Polygon", "MultiPolygon")

    @classmethod
    def can_serialize(cls, geometry):
        return (
            isinstance(geometry, dict)
            and geometry.get("type") in cls.supported_shapes
            and geometry.get("coordinates")
        )

    @classmethod
    def get_feature_type(cls, geometry):
        if geometry["type"] == "LineString":
            return "line"
        return geometry["type"].lower()

    @classmethod
    def serialize(cls, geometry):
        if geometry["type"] == "Point":
            return flip_coords(geometry["coordinates"])

        if geometry["type"] == "LineString":
            return tuple(flip_coords(point) for point in geometry["coordinates"])

        if geometry["type"] == "Polygon":
            rings = geometry["coordinates"]
            if len(rings) == 1:
                ring = rings[0]
                return tuple(flip_coords(point) for point in ring)

            return tuple(tuple(flip_coords(point) for point in ring) for ring in rings)

        if geometry["type"] == "MultiPolygon":
            return tuple(
                tuple(tuple(flip_coords(point) for point in ring) for ring in polygon)
                for polygon in geometry["coordinates"]
            )
        raise ValueError(
            f"Cannot serialize geometry object of type {geometry.__class__}"
        )

    @classmethod
    def make_boundary_box(
        cls,
        geometry,
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        coordinates = geometry["coordinates"]

        if geometry["type"] == "Point":
            return flip_coords(coordinates)

        if geometry["type"] in ("LineString", "Polygon", "MultiPolygon"):
            min_x = float("inf")
            min_y = float("inf")
            max_x = -float("inf")
            max_y = -float("inf")

            if geometry["type"] == "LineString":
                # convert polygon to multipolygon-like shape
                coordinates = [[coordinates]]

            if geometry["type"] == "Polygon":
                # convert polygon to multipolygon
                coordinates = [coordinates]

            for polygon in coordinates:
                for ring in polygon:
                    for x, y in ring:
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)

            return ((min_y, min_x), (max_y, max_x))

        return None

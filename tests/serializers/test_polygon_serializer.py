import pytest
from django.contrib.gis.geos import Polygon as GeosPolygon
from shapely.geometry import Polygon as ShapelyPolygon

from generic_map_api.serializers import BaseFeatureSerializer


def geo_json_factory(shell, holes=None):
    holes = holes or []
    return {
        "type": "Polygon",
        "coordinates": [shell] + holes,
    }


class TestPolygonSerializer(BaseFeatureSerializer):
    feature_type = "test"

    def get_geometry(self, obj):
        return obj["geometry"]


@pytest.mark.parametrize(
    "geometry_class", (GeosPolygon, ShapelyPolygon, geo_json_factory)
)
def test_simple_polygon_serializer(geometry_class):
    obj = {
        "geometry": geometry_class(
            [(0.0, 0.0), (0.0, 1.0), (2.0, 3.0), (1.0, 0.0), (0.0, 0.0)]
        )
    }

    expected_output = {
        "type": (
            "test",
            "polygon",
        ),
        "geom": ((0.0, 0.0), (1.0, 0.0), (3.0, 2.0), (0.0, 1.0), (0.0, 0.0)),
        "id": None,
        "bbox": ((0.0, 0.0), (3.0, 2.0)),
    }

    serializer = TestPolygonSerializer()
    serialized = serializer.serialize(obj)

    assert expected_output == serialized


def geos_polygon_factory(shell, holes):
    return GeosPolygon(shell, *holes)


@pytest.mark.parametrize(
    "geometry_factory",
    (
        geos_polygon_factory,
        ShapelyPolygon,
        geo_json_factory,
    ),
)
def test_holed_polygon_serializer(geometry_factory):
    shell = [(0, 0), (0, 10), (14, 15), (10, 0), (0, 0)]
    holes = [
        [(1, 1), (1, 2), (3, 4), (2, 1), (1, 1)],
    ]
    obj = {"geometry": geometry_factory(shell, holes)}

    expected_output = {
        "type": (
            "test",
            "polygon",
        ),
        "geom": (
            ((0.0, 0.0), (10.0, 0.0), (15.0, 14.0), (0.0, 10.0), (0.0, 0.0)),
            ((1.0, 1.0), (2.0, 1.0), (4.0, 3.0), (1.0, 2.0), (1.0, 1.0)),
        ),
        "id": None,
        "bbox": ((0.0, 0.0), (15.0, 14.0)),
    }

    serializer = TestPolygonSerializer()
    serialized = serializer.serialize(obj)

    assert expected_output == serialized

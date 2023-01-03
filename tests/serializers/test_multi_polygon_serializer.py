import pytest
from django.contrib.gis.geos import MultiPolygon as GeosMultiPolygon
from django.contrib.gis.geos import Polygon as GeosPolygon
from shapely.geometry import MultiPolygon as ShapelyMultiPolygon
from shapely.geometry import Polygon as ShapelyPolygon

from generic_map_api.serializers import BaseFeatureSerializer


class TestMultiPolygonSerializer(BaseFeatureSerializer):
    feature_type = "test"

    def get_geometry(self, obj):
        return obj["geometry"]


def polygon_for_geo_json_factory(polygon):
    return [polygon]


def geo_json_factory(multipolygon):
    return {
        "type": "MultiPolygon",
        "coordinates": multipolygon,
    }


@pytest.mark.parametrize(
    "mpoly_class, poly_class",
    (
        (GeosMultiPolygon, GeosPolygon),
        (ShapelyMultiPolygon, ShapelyPolygon),
        (geo_json_factory, polygon_for_geo_json_factory),
    ),
)
def test_multi_polygon_serializer(mpoly_class, poly_class):
    obj = {
        "geometry": mpoly_class(
            [
                poly_class(
                    [(0.0, 0.0), (0.0, 1.0), (2.0, 3.0), (1.0, 0.0), (0.0, 0.0)]
                ),
                poly_class(
                    [(10.0, 0.0), (10.0, 1.0), (12.0, 3.0), (11.0, 0.0), (10.0, 0.0)]
                ),
            ]
        )
    }

    expected_output = {
        "type": (
            "test",
            "multipolygon",
        ),
        "geom": (
            (((0.0, 0.0), (1.0, 0.0), (3.0, 2.0), (0.0, 1.0), (0.0, 0.0)),),
            (((0.0, 10.0), (1.0, 10.0), (3.0, 12.0), (0.0, 11.0), (0.0, 10.0)),),
        ),
        "id": None,
        "bbox": ((0.0, 0.0), (3.0, 12.0)),
    }

    serializer = TestMultiPolygonSerializer()
    serialized = serializer.serialize(obj)

    assert expected_output == serialized

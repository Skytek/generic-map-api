import pytest
from django.contrib.gis.geos import LineString as GeosLineString
from shapely.geometry import LineString as ShapelyLineString

from generic_map_api.serializers import BaseFeatureSerializer


class TestLineSerializer(BaseFeatureSerializer):
    feature_type = "test"

    def get_geometry(self, obj):
        return obj["geometry"]


def geo_json_factory(line):
    return {
        "type": "LineString",
        "coordinates": line,
    }


@pytest.mark.parametrize(
    "geometry_class", (GeosLineString, ShapelyLineString, geo_json_factory)
)
def test_simple_line_serializer(geometry_class):
    obj = {"geometry": geometry_class([(0.0, 0.0), (0.0, 1.0), (2.0, 3.0), (1.0, 0.0)])}

    expected_output = {
        "type": (
            "test",
            "line",
        ),
        "geom": ((0.0, 0.0), (1.0, 0.0), (3.0, 2.0), (0.0, 1.0)),
        "id": None,
        "bbox": ((0.0, 0.0), (3.0, 2.0)),
    }

    serializer = TestLineSerializer()
    serialized = serializer.serialize(obj)

    assert expected_output == serialized

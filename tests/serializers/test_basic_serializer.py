import pytest
from django.contrib.gis.geos import Point as GeosPoint
from shapely.geometry import Point as ShapelyPoint

from generic_map_api.serializers import BaseFeatureSerializer


class TestSerializer(BaseFeatureSerializer):
    def get_geometry(self, obj):
        return obj["geometry"]


def geo_json_factory(x, y):
    return {
        "type": "Point",
        "coordinates": [x, y],
    }


@pytest.mark.parametrize("point_class", (GeosPoint, ShapelyPoint, geo_json_factory))
def test_serializer(point_class):
    obj = {"geometry": point_class(1.0, 2.0)}

    expected_output = {
        "type": ("point",),
        "geom": (2.0, 1.0),
        "id": None,
        "bbox": (2.0, 1.0),
    }

    serializer = TestSerializer()
    serialized = serializer.serialize(obj)

    assert expected_output == serialized

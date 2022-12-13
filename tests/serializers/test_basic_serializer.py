import pytest
from django.contrib.gis.geos import Point as GeosPoint
from shapely.geometry import Point as ShapelyPoint

from generic_map_api.serializers import PointSerializer


class TestSerializer(PointSerializer):
    def get_geometry(self, obj):
        return obj["geometry"]


@pytest.mark.parametrize("point_class", (GeosPoint, ShapelyPoint))
def test_serializer(point_class):
    obj = {"geometry": point_class(1, 2)}

    expected_output = {
        "type": ("point",),
        "geom": (2.0, 1.0),
        "id": None,
        "bbox": (2.0, 1.0),
    }

    serializer = TestSerializer()
    serialized = serializer.serialize(obj)

    assert expected_output == serialized

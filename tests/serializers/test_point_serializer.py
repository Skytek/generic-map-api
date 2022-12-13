import pytest
from django.contrib.gis.geos import Point as GeosPoint
from shapely.geometry import Point as ShapelyPoint

from generic_map_api.serializers import PointSerializer


class TestPointSerializer(PointSerializer):
    feature_type = "test"

    def get_geometry(self, obj):
        return obj["geometry"]


@pytest.mark.parametrize("geometry_class", (GeosPoint, ShapelyPoint))
def test_point_serializer(geometry_class):
    obj = {"geometry": geometry_class(1, 2)}

    expected_output = {
        "type": ("test", "point"),
        "geom": (2.0, 1.0),
        "id": None,
        "bbox": (2.0, 1.0),
    }

    serializer = TestPointSerializer()
    serialized = serializer.serialize(obj)

    assert expected_output == serialized

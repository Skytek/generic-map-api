from generic_map_api.values import ViewPort
from shapely.geometry import Point


def test_viewport_from_geohashes():
    geohashes = "g823h7/sw096f"
    viewport = ViewPort.from_geohashes_query_param(geohashes)
    assert viewport.upper_left == Point(-21.961669921875, 46.5985107421875)
    assert viewport.lower_right == Point(23.3349609375, 33.9862060546875)

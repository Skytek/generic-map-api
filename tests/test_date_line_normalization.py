import pytest
from shapely.geometry import MultiPolygon, box

from generic_map_api.date_line_normalization import normalized_viewport


@pytest.mark.parametrize(
    "input_args,expected_geometry",
    [
        ((10, 70, 50, 20), box(10, 70, 50, 20)),
        ((-100, 70, 50, 20), box(-100, 70, 50, 20)),
        ((-100, 70, 50, -80), box(-100, 70, 50, -80)),
        (
            (170, 70, -170, -80),
            MultiPolygon([box(-170, -80, -180, 70), box(180, -80, 170, 70)]),
        ),
        ((-190, 70, 190, -80), box(-180, 70, 180, -80)),
        ((-170 + 360, 70, 170 + 360, -80), box(-170, 70, 170, -80)),
        ((-170 - 360, 70, 170 - 360, -80), box(-170, 70, 170, -80)),
    ],
)
def test_normalize_viewport(input_args, expected_geometry):
    result = normalized_viewport(*input_args)
    assert expected_geometry.wkt == result.wkt

from itertools import pairwise
from typing import Generator, Iterable, Tuple

from shapely.geometry import Polygon, box


def normalize_line(
    line: Iterable[Tuple[float, float]]
) -> Generator[Tuple[float, float], None, None]:
    """Fixes date line crossing problem for a line

    It works by detecting date-line crossings and moving points to adjacent worlds.
    """
    first_point_yielded = False
    world_number = 0

    for prev_point, point in pairwise(line):
        if not first_point_yielded:
            yield prev_point[0], prev_point[1]
            first_point_yielded = True

        if prev_point[1] > 0 > point[1]:
            # crossing E -> W
            world_number += 1

        if prev_point[1] < 0 < point[1]:
            # crossing W -> E
            world_number -= 1

        yield point[0], point[1] + (world_number * 360)


def normalize_geometry(geometry):
    if not geometry:
        # emoty
        return geometry

    if len(geometry) == 2 and isinstance(geometry[0], (int, float)):
        # point
        return geometry

    if (
        isinstance(geometry[0], (list, tuple))
        and geometry[0]
        and isinstance(geometry[0][0], (int, float))
    ):
        # line
        return tuple(normalize_line(geometry))

    # higher dimension object (polygon, multipolygon, etc.)
    return tuple(normalize_geometry(subgeom) for subgeom in geometry)


def normalized_viewport(
    upper_left_x: float,
    upper_left_y: float,
    lower_right_x: float,
    lower_right_y: float,
) -> Polygon:
    return box(upper_left_x, upper_left_y, lower_right_x, lower_right_y)

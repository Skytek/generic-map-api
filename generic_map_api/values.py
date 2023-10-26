from __future__ import annotations

import geohash2
from shapely.geometry import Point, Polygon
from skytek_utils.spatial import tiles

from .date_line_normalization import normalized_viewport


class BaseViewPort:
    def to_polygon(self) -> Polygon:
        raise NotImplementedError()

    def get_dimensions(self):
        raise NotImplementedError()


class ViewPort(BaseViewPort):
    def __init__(self, upper_left, lower_right) -> None:
        self.upper_left = upper_left
        self.lower_right = lower_right

    def to_polygon(self) -> Polygon:
        return normalized_viewport(
            self.upper_left.x,
            self.upper_left.y,
            self.lower_right.x,
            self.lower_right.y,
        )

    def get_dimensions(self):
        return abs(self.lower_right.x - self.upper_left.x), abs(
            self.lower_right.y - self.upper_left.y
        )

    @classmethod
    def from_geohashes_query_param(cls, geohashes):
        if geohashes is None:
            return None
        geohashes_arr = geohashes.split("/")
        if len(geohashes_arr) >= 2:
            lat1, lon1, lat1_err, lon1_err = geohash2.decode_exactly(geohashes_arr[0])
            lat2, lon2, lat2_err, lon2_err = geohash2.decode_exactly(geohashes_arr[1])
        else:
            lat1, lon1, lat1_err, lon1_err = (
                lat2,
                lon2,
                lat2_err,
                lon2_err,
            ) = geohash2.decode_exactly(geohashes_arr[0])

        upper_left, lower_right = Point(lon1 - lon1_err, lat1 + lat1_err), Point(
            lon2 + lon2_err, lat2 - lat2_err
        )

        return cls(upper_left, lower_right)


class Tile(BaseViewPort):
    def __init__(self, x: int, y: int, z: int) -> None:
        self.x = x
        self.y = y
        self.z = z

    def to_polygon(self) -> Polygon:
        upper_left_x, upper_left_y = tiles.tile2deg(
            self.x,
            self.y,
            self.z,
        )
        lower_right_x, lower_right_y = tiles.tile2deg(
            self.x + 1,
            self.y + 1,
            self.z,
        )
        return normalized_viewport(
            upper_left_x,
            upper_left_y,
            lower_right_x,
            lower_right_y,
        )

    def get_dimensions(self):
        upper_left_x, upper_left_y = tiles.tile2deg(
            self.x,
            self.y,
            self.z,
        )
        lower_right_x, lower_right_y = tiles.tile2deg(
            self.x + 1,
            self.y + 1,
            self.z,
        )

        return abs(lower_right_x - upper_left_x), abs(lower_right_y - upper_left_y)

    @classmethod
    def from_query_param(cls, param):
        if param is None:
            return None

        param_arr = param.split("/")
        if len(param_arr) != 3:
            raise ValueError("Tile has to be defined by exactly 3 integers")

        return cls(*[int(v) for v in param_arr])

from __future__ import annotations

import geohash2
from shapely.geometry import Point, box


class ViewPort:
    def __init__(self, upper_left, lower_right) -> None:
        self.upper_left = upper_left
        self.lower_right = lower_right

    def to_polygon(self):
        return box(
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

        upper_left, lower_right = Point(lon1 - lon1_err, lat1 - lat1_err), Point(
            lon2 + lon2_err, lat2 + lat2_err
        )

        return cls(upper_left, lower_right)

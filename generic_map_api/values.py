from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Union

import geohash2
from shapely import set_srid
from shapely.geometry import MultiPolygon, Point, Polygon
from skytek_utils.spatial import tiles

from .constants import WGS84
from .date_line_normalization import normalized_viewport


class BaseViewPort:
    def __init__(self) -> None:
        self.size = None
        self.meters_per_pixel = None
        self.zoom = None
        self.clustering = False

    def to_polygon(self) -> Polygon:
        raise NotImplementedError()

    def get_dimensions(self):
        raise NotImplementedError()

    def to_dict(self) -> dict:
        return {
            "size": self.size,
            "mpp": self.meters_per_pixel,
            "zoom": self.zoom,
            "clustering": self.clustering,
        }


class EmptyViewport(BaseViewPort):
    def __bool__(self) -> bool:
        return False

    def to_polygon(self) -> Polygon:
        return None

    def get_dimensions(self):
        return None

    def to_dict(self) -> dict:
        return {"type": "empty"}


class ViewPort(BaseViewPort):
    def __init__(self, upper_left, lower_right) -> None:
        super().__init__()
        self.upper_left = upper_left
        self.lower_right = lower_right

    def to_polygon(self) -> Union[Polygon | MultiPolygon]:
        return set_srid(
            normalized_viewport(
                self.upper_left.x,
                self.upper_left.y,
                self.lower_right.x,
                self.lower_right.y,
            ),
            WGS84,
        )

    def get_dimensions(self):
        return abs(self.lower_right.x - self.upper_left.x), abs(
            self.lower_right.y - self.upper_left.y
        )

    @classmethod
    def from_geohashes_query_param(cls, geohashes):
        if geohashes is None:
            return None
        split_by = r"[\/,\- ]"
        geohashes_arr = re.split(split_by, geohashes)
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

    def to_dict(self) -> dict:
        output = super().to_dict()
        output.update(
            {
                "type": "geohash",
                "corners": (
                    (self.upper_left.x, self.upper_left.y),
                    (self.lower_right.x, self.lower_right.y),
                ),
            }
        )
        return output


class Tile(BaseViewPort):
    def __init__(self, x: int, y: int, z: int) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.z = z

    def to_polygon(self) -> Union[Polygon, MultiPolygon]:
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
        return set_srid(
            normalized_viewport(
                upper_left_x,
                upper_left_y,
                lower_right_x,
                lower_right_y,
            ),
            WGS84,
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

        split_by = r"[\/,\- ]"
        param_arr = re.split(split_by, param)

        if len(param_arr) != 3:
            raise ValueError("Tile has to be defined by exactly 3 integers")

        return cls(*[int(v) for v in param_arr])

    def to_dict(self) -> dict:
        output = super().to_dict()
        output.update(
            {
                "type": "xyz",
                "coords": (self.x, self.y, self.z),
            }
        )
        return output


@dataclass
class ClusteringOutput:
    is_cluster: bool
    item: Any


@dataclass
class BoundingBox:
    @dataclass
    class Point:
        latitude: float
        longitude: float

    northwest: Point
    southeast: Point

    count: int

    @classmethod
    def full(cls, count=0):
        return cls(
            northwest=cls.Point(
                latitude=90,
                longitude=-180,
            ),
            southeast=cls.Point(
                latitude=-90,
                longitude=180,
            ),
            count=count,
        )


@dataclass
class TileRedirect:
    url: str

    def to_cache(self):
        return {"url": self.url}

    @classmethod
    def from_cache(cls, data):
        return cls(url=data["url"])

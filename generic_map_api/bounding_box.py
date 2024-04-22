from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Union

from django.contrib.gis.db.models.functions import GeoFunc
from django.db.models import Count, F, FloatField, Max, Min, QuerySet

from .values import BoundingBox

if TYPE_CHECKING:
    from .views import MapFeaturesBaseView


def queryset_to_bounding_box(queryset, geometry_field) -> None | BoundingBox:
    class XMin(GeoFunc):
        output_field = FloatField()

    class XMax(GeoFunc):
        output_field = FloatField()

    class YMin(GeoFunc):
        output_field = FloatField()

    class YMax(GeoFunc):
        output_field = FloatField()

    aggregate = queryset.aggregate(
        min_x=Min(XMin(F(geometry_field))),
        max_x=Max(XMax(F(geometry_field))),
        min_y=Min(YMin(F(geometry_field))),
        max_y=Max(YMax(F(geometry_field))),
        count=Count(geometry_field),
    )

    if not aggregate["count"]:
        return BoundingBox.full()

    return BoundingBox(
        northwest=BoundingBox.Point(
            latitude=aggregate["max_y"],
            longitude=aggregate["min_x"],
        ),
        southeast=BoundingBox.Point(
            latitude=aggregate["min_y"],
            longitude=aggregate["max_x"],
        ),
        count=aggregate["count"],
    )


class BaseBoundingBoxing:
    def find_bounding_box(self, view: MapFeaturesBaseView, items) -> None | BoundingBox:
        raise NotImplementedError()


class DatabaseBoundingBoxing(BaseBoundingBoxing):
    def find_bounding_box(self, view: MapFeaturesBaseView, items) -> None | BoundingBox:
        assert isinstance(items, QuerySet)

        geometry_field = view.bounding_box_db_geometry_field
        queryset = items.all()

        return queryset_to_bounding_box(queryset, geometry_field)


class SerializerBoundingBoxing(BaseBoundingBoxing):
    @staticmethod
    def _ensure_2d(
        bbox: Union[
            Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]
        ]
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        if isinstance(bbox[0], (tuple, list)):
            return bbox

        return bbox, bbox

    @staticmethod
    def _combine_bbox(
        bbox1: None | Tuple[Tuple[float, float], Tuple[float, float]],
        bbox2: Tuple[Tuple[float, float], Tuple[float, float]],
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        if bbox1 is None:
            return bbox2

        return (
            (min(bbox1[0][0], bbox2[0][0]), min(bbox1[0][1], bbox2[0][1])),
            (max(bbox1[1][0], bbox2[1][0]), max(bbox1[1][1], bbox2[1][1])),
        )

    def find_bounding_box(self, view: MapFeaturesBaseView, items) -> None | BoundingBox:
        bbox = None
        count = 0
        for item in items:
            count += 1
            serializer = view.get_serializer(item)
            item_bbox = serializer.get_boundary_box(item)
            bbox = self._combine_bbox(bbox, self._ensure_2d(item_bbox))

        if not bbox:
            return BoundingBox.full()

        return BoundingBox(
            northwest=BoundingBox.Point(
                longitude=bbox[0][1],
                latitude=bbox[1][0],
            ),
            southeast=BoundingBox.Point(
                longitude=bbox[1][1],
                latitude=bbox[0][0],
            ),
            count=count,
        )


class AutomaticBoundingBoxing(BaseBoundingBoxing):
    def find_bounding_box(self, view: MapFeaturesBaseView, items) -> None | BoundingBox:
        if isinstance(items, QuerySet) and view.bounding_box_db_geometry_field:
            bbox = DatabaseBoundingBoxing()
        else:
            bbox = SerializerBoundingBoxing()

        return bbox.find_bounding_box(view, items)

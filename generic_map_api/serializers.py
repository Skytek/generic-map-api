from typing import Tuple, Union

from rest_framework.serializers import Serializer

from . import date_line_normalization, geometry_serializers


class FeatureSerializerMeta(type):
    def __new__(cls, name, bases, namespace, /, **kwargs):
        created_class = super().__new__(cls, name, bases, namespace, **kwargs)
        created_class.feature_types = cls._build_feature_type_list(created_class)
        created_class.cluster_types = cls._build_cluster_type_list(created_class)
        return created_class

    @classmethod
    def _build_feature_type_list(cls, created_class):
        return tuple(
            {
                c.feature_type: None
                for c in created_class.__mro__
                if getattr(c, "feature_type", None)
            }.keys()
        )

    @classmethod
    def _build_cluster_type_list(cls, created_class):
        return tuple(
            {
                c.cluster_type: None
                for c in created_class.__mro__
                if getattr(c, "cluster_type", None)
            }.keys()
        )


class BaseFeatureSerializer(metaclass=FeatureSerializerMeta):
    feature_type = None
    feature_types = ()

    cluster_type = "cluster"
    cluster_types = ()

    def serialize(self, obj):
        return {
            "type": self.get_type(obj),
            "id": self.get_id(obj),
            "geom": self.get_frontend_style_geometry(obj),
            "bbox": self.get_boundary_box(obj),
        }

    def serialize_details(self, obj):
        return {
            "type": self.get_type(obj, with_geometry=False),
            "id": self.get_id(obj),
        }

    def serialize_cluster(self, obj):
        return {
            # @TODO id?
            "type": self.get_cluster_type(obj),
            "geom": self.get_frontend_style_cluster_geometry(obj),
            "bbox": self.get_cluster_boundary_box(obj),
        }

    def get_type(self, obj, with_geometry=True):  # pylint: disable=unused-argument
        if with_geometry:
            geometry_feature_type = self.get_geometry_feature_type(
                self.get_geometry(obj)
            )
            if geometry_feature_type:
                return self.feature_types + (geometry_feature_type,)
        return self.feature_types

    def get_cluster_type(self, obj):  # pylint: disable=unused-argument
        return self.cluster_types + ("multipolygon",)

    def get_id(self, obj):  # pylint: disable=unused-argument
        return None

    def get_geometry(self, obj):  # pylint: disable=unused-argument
        return None

    def get_cluster_geometry(self, obj):  # pylint: disable=unused-argument
        return None

    def get_frontend_style_geometry(self, obj):
        input_geometry = self.get_geometry(obj)  # pylint: disable=assignment-from-none
        geometry = self.make_frontend_style_geometry(input_geometry)
        return date_line_normalization.normalize_geometry(geometry)

    def get_frontend_style_cluster_geometry(self, obj):
        # pylint: disable=assignment-from-none
        input_geometry = self.get_cluster_geometry(obj)
        geometry = self.make_frontend_style_geometry(input_geometry)
        return date_line_normalization.normalize_geometry(geometry)

    def get_boundary_box(
        self, obj
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        geometry = self.get_geometry(obj)  # pylint: disable=assignment-from-none
        return self.make_boundary_box(geometry)

    def get_cluster_boundary_box(
        self, obj
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        # pylint: disable=assignment-from-none
        geometry = self.get_cluster_geometry(obj)
        return self.make_boundary_box(geometry)

    def get_geometry_feature_type(self, geometry):
        if geometry_serializers.GeosSerializer.can_serialize(geometry):
            return geometry_serializers.GeosSerializer.get_feature_type(geometry)
        if geometry_serializers.ShapelySerializer.can_serialize(geometry):
            return geometry_serializers.ShapelySerializer.get_feature_type(geometry)
        if geometry_serializers.GeoJsonSerializer.can_serialize(geometry):
            return geometry_serializers.GeoJsonSerializer.get_feature_type(geometry)
        raise ValueError(
            "Cannot determine generic geometry type type of "
            f"{geometry.__class__} in {self.__class__}"
        )

    def make_frontend_style_geometry(self, geometry):
        if geometry_serializers.GeosSerializer.can_serialize(geometry):
            return geometry_serializers.GeosSerializer.serialize(geometry)
        if geometry_serializers.ShapelySerializer.can_serialize(geometry):
            return geometry_serializers.ShapelySerializer.serialize(geometry)
        if geometry_serializers.GeoJsonSerializer.can_serialize(geometry):
            return geometry_serializers.GeoJsonSerializer.serialize(geometry)
        raise ValueError(
            f"Cannot make frontend geometry from {geometry.__class__} in {self.__class__}"
        )

    def make_boundary_box(
        self, geometry
    ) -> Union[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float]]:
        if geometry_serializers.GeosSerializer.can_serialize(geometry):
            return geometry_serializers.GeosSerializer.make_boundary_box(geometry)
        if geometry_serializers.ShapelySerializer.can_serialize(geometry):
            return geometry_serializers.ShapelySerializer.make_boundary_box(geometry)
        if geometry_serializers.GeoJsonSerializer.can_serialize(geometry):
            return geometry_serializers.GeoJsonSerializer.make_boundary_box(geometry)
        raise ValueError(
            f"Cannot get boundary box of {geometry.__class__} in {self.__class__}"
        )


# Left for compatibility.
# Will be removed in future versions:

PointSerializer = BaseFeatureSerializer
LineSerializer = BaseFeatureSerializer
PolygonSerializer = BaseFeatureSerializer
MultiPolygonSerializer = BaseFeatureSerializer


class BoundingBoxSerializer(Serializer):
    def to_representation(self, instance):
        return {
            "northwest": {
                "latitude": instance.northwest.latitude,
                "longitude": instance.northwest.longitude,
            },
            "southeast": {
                "latitude": instance.southeast.latitude,
                "longitude": instance.southeast.longitude,
            },
            "count": instance.count,
        }

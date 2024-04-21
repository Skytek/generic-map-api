from generic_map_api.params import Text
from generic_map_api.serializers import BaseFeatureSerializer
from generic_map_api.values import BaseViewPort
from generic_map_api.views import MapFeaturesBaseView
from tests.app.models import Feature


class FeatureSerializer(BaseFeatureSerializer):
    def get_geometry(self, obj):
        return obj.position

    def get_id(self, obj):
        return obj.id

    def serialize(self, obj):
        serialized = super().serialize(obj)
        serialized.update(
            {
                "category": obj.category,
            }
        )
        return serialized


class FeatureView(MapFeaturesBaseView):

    serializer = FeatureSerializer()

    query_params = {"category": Text("Category", many=False)}

    def get_items(self, viewport: BaseViewPort, params: dict):
        features = Feature.objects.all()

        if viewport:
            features = features.filter(
                position__intersects=viewport.to_polygon().wkb_hex
            )

        if "category" in params:
            features = features.filter(category=params["category"])

        return features

    def get_item(self, item_id):
        return None

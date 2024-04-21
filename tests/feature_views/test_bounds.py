import pytest

from generic_map_api.values import BaseViewPort
from tests.app.models import Feature

from .factories import request_factory
from .fixtures import create_feature_data
from .views import FeatureView


@pytest.mark.django_db
def test_models(create_feature_data):
    assert Feature.objects.count() == 7


@pytest.mark.django_db
def test_no_params(create_feature_data):
    view = FeatureView()
    request = request_factory(
        {
            "viewport": "get2u6/rfpzxg",
        }
    )
    result = view.bounds(request)

    expected_result = {
        "count": 7,
        "northwest": {"latitude": 50.0, "longitude": -20.0},
        "southeast": {"latitude": -50.0, "longitude": 20.0},
    }

    assert result.data == expected_result


@pytest.mark.django_db
def test_filter_param(create_feature_data):
    view = FeatureView()
    request = request_factory(
        {
            "viewport": "get2u6/rfpzxg",
            "category": "A",
        }
    )
    result = view.bounds(request)

    expected_result = {
        "northwest": {"latitude": 50.0, "longitude": -20.0},
        "southeast": {"latitude": 49.99, "longitude": 20.0},
        "count": 4,
    }

    assert result.data == expected_result


@pytest.mark.django_db
def test_view_returning_list(create_feature_data):
    class FeatureListView(FeatureView):
        def get_items(self, viewport: BaseViewPort, params: dict):
            items = super().get_items(viewport, params)
            return list(items)

    view = FeatureListView()
    request = request_factory(
        {
            "viewport": "get2u6/rfpzxg",
        }
    )
    result = view.bounds(request)

    expected_result = {
        "count": 7,
        "northwest": {"latitude": 50.0, "longitude": -20.0},
        "southeast": {"latitude": -50.0, "longitude": 20.0},
    }

    assert result.data == expected_result

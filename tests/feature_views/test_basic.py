import pytest

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
    request = request_factory()
    result = view.list(request)

    expected_result = {
        "items": [
            {
                "type": ("point",),
                "id": 1,
                "geom": (50.0, 20.0),
                "bbox": (50.0, 20.0),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 2,
                "geom": (49.99, 19.99),
                "bbox": (49.99, 19.99),
                "category": "B",
            },
            {
                "type": ("point",),
                "id": 3,
                "geom": (50.0, 19.99),
                "bbox": (50.0, 19.99),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 4,
                "geom": (49.99, 20.0),
                "bbox": (49.99, 20.0),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 5,
                "geom": (50.0, -20.0),
                "bbox": (50.0, -20.0),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 6,
                "geom": (-50.0, 20.0),
                "bbox": (-50.0, 20.0),
                "category": "B",
            },
            {
                "type": ("point",),
                "id": 7,
                "geom": (-50.0, -20.0),
                "bbox": (-50.0, -20.0),
                "category": "B",
            },
        ]
    }

    assert result.data == expected_result


@pytest.mark.django_db
def test_north_west_viewport(create_feature_data):
    view = FeatureView()
    request = request_factory(
        {
            "viewport": "get2u6/rfpzxg",
        }
    )
    result = view.list(request)

    expected_result = {
        "items": [
            {
                "type": ("point",),
                "id": 1,
                "geom": (50.0, 20.0),
                "bbox": (50.0, 20.0),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 2,
                "geom": (49.99, 19.99),
                "bbox": (49.99, 19.99),
                "category": "B",
            },
            {
                "type": ("point",),
                "id": 3,
                "geom": (50.0, 19.99),
                "bbox": (50.0, 19.99),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 4,
                "geom": (49.99, 20.0),
                "bbox": (49.99, 20.0),
                "category": "A",
            },
        ]
    }

    print(result.data)

    assert result.data == expected_result


@pytest.mark.django_db
def test_param_filter(create_feature_data):
    view = FeatureView()
    request = request_factory({"category": "A"})
    result = view.list(request)

    expected_result = {
        "items": [
            {
                "type": ("point",),
                "id": 1,
                "geom": (50.0, 20.0),
                "bbox": (50.0, 20.0),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 3,
                "geom": (50.0, 19.99),
                "bbox": (50.0, 19.99),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 4,
                "geom": (49.99, 20.0),
                "bbox": (49.99, 20.0),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 5,
                "geom": (50.0, -20.0),
                "bbox": (50.0, -20.0),
                "category": "A",
            },
        ]
    }

    assert result.data == expected_result


@pytest.mark.django_db
def test_param_filter_and_north_west_viewport(create_feature_data):
    view = FeatureView()
    request = request_factory(
        {
            "viewport": "get2u6/rfpzxg",
            "category": "A",
        }
    )
    result = view.list(request)

    expected_result = {
        "items": [
            {
                "type": ("point",),
                "id": 1,
                "geom": (50.0, 20.0),
                "bbox": (50.0, 20.0),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 3,
                "geom": (50.0, 19.99),
                "bbox": (50.0, 19.99),
                "category": "A",
            },
            {
                "type": ("point",),
                "id": 4,
                "geom": (49.99, 20.0),
                "bbox": (49.99, 20.0),
                "category": "A",
            },
        ]
    }

    assert result.data == expected_result

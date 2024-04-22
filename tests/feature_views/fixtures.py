import pytest
from django.contrib.gis.geos import Point

from tests.app.models import Feature


@pytest.fixture
def create_feature_data():
    Feature.objects.create(id=1, position=Point(20, 50))
    Feature.objects.create(id=2, position=Point(19.99, 49.99), category="B")
    Feature.objects.create(id=3, position=Point(19.99, 50))
    Feature.objects.create(id=4, position=Point(20, 49.99))

    Feature.objects.create(id=5, position=Point(-20, 50))
    Feature.objects.create(id=6, position=Point(20, -50), category="B")
    Feature.objects.create(id=7, position=Point(-20, -50), category="B")

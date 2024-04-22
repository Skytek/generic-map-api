import os

SECRET_KEY = "fake-key"
INSTALLED_APPS = [
    "tests.app",
]

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.spatialite",
        "NAME": os.path.join(PROJECT_DIR, "test.db"),
    }
}

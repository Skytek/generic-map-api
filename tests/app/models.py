from django.contrib.gis.db import models


class Feature(models.Model):
    position = models.PointField()
    category = models.CharField(max_length=10, default="A")

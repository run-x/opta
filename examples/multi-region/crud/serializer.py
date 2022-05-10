from rest_framework import serializers

from . import models


class TestModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TestModel
        fields = "__all__"

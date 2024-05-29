from rest_framework import serializers

from apps.contrib.serializers import (
    MetaInformationSerializerMixin,
    UpdateSerializerMixin,
    IntegerIDField,
)
from .models import ExtractionQuery


class ExtractionQuerySerializer(MetaInformationSerializerMixin, serializers.ModelSerializer):
    """Serializer for the ExtractionQuery model.

    This serializer is used to convert ExtractionQuery objects to and from JSON format.
    It inherits from the MetaInformationSerializerMixin and serializers.ModelSerializer classes.

    Attributes:
        model (class): The model class that the serializer is associated with.
        fields (str): The fields that should be serialized and deserialized. In this case, it
            is set to '__all__' to indicate that all fields of the model should be included.

    """
    class Meta:
        model = ExtractionQuery
        fields = '__all__'


class ExtractionQueryUpdateSerializer(UpdateSerializerMixin, ExtractionQuerySerializer):
    """
    Class: ExtractionQueryUpdateSerializer

        This class is responsible for serializing and validating update requests for the ExtractionQuery model.

    Attributes:
        - id (IntegerIDField): The unique identifier for the extraction query (required).

    """
    id = IntegerIDField(required=True)

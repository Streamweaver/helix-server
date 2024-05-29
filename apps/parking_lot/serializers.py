from rest_framework import serializers

from apps.contrib.serializers import (
    MetaInformationSerializerMixin,
    UpdateSerializerMixin,
    IntegerIDField,
)
from apps.parking_lot.models import ParkedItem
from apps.country.models import Country


class ParkedItemSerializer(MetaInformationSerializerMixin,
                           serializers.ModelSerializer):
    """
    ParkedItemSerializer

    Serializes and deserializes ParkedItem objects to and from JSON.

    Inherits from:
    - MetaInformationSerializerMixin
    - serializers.ModelSerializer

    Attributes:
    - country_iso3: A CharField representing the ISO3 code of the country. Optional.
    - status_display: A CharField representing the display value of the status. Read-only.
    - source_display: A CharField representing the display value of the source. Read-only.

    Meta:
    - model: The ParkedItem model.
    - fields: All fields of the ParkedItem model.

    Methods:
    - validate(data): Validates the serialized data.
    - create(validated_data): Creates a ParkedItem object with the given validated data.

    Exceptions:
    - serializers.ValidationError: Raised when the country ISO3 code is not found in the database.

    """
    country_iso3 = serializers.CharField(required=False)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)

    class Meta:
        model = ParkedItem
        fields = '__all__'

    def validate(self, data):
        data = super().validate(data)
        iso3 = data.get('country_iso3')
        if iso3 and not Country.objects.filter(iso3=iso3).exists():
            raise serializers.ValidationError({'iso3': 'No any iso3 found for the country'})
        return data

    def create(self, validated_data):
        iso3 = validated_data.pop('country_iso3', None)
        if iso3:
            validated_data['country'] = Country.objects.filter(iso3=iso3).first()
        return ParkedItem.objects.create(**validated_data)


class ParkedItemUpdateSerializer(UpdateSerializerMixin, ParkedItemSerializer):
    """
    Class: ParkedItemUpdateSerializer

    A serializer class for updating ParkedItem objects.

    It inherits from the UpdateSerializerMixin and ParkedItemSerializer classes.

    Attributes:
        id (int): The identifier of the ParkedItem to be updated.

    """
    id = IntegerIDField(required=True)

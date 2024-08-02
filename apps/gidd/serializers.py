from rest_framework import serializers
from apps.country.models import Country
from .models import (
    Conflict, Disaster, GiddFigure, StatusLog, ReleaseMetadata,
    DisplacementData, PublicFigureAnalysis, IdpsSaddEstimate,
)
from apps.crisis.models import Crisis
from apps.entry.models import Figure


class CountrySerializer(serializers.ModelSerializer):
    """
    Serializer for the Country model.

    Fields:
    - iso2: The two-letter ISO code for the country.
    - iso3: The three-letter ISO code for the country.
    - country_name: The short name of the country.

    Meta options:
    - model: The model that this serializer is used for, which is Country.
    - fields: The fields to include in the serialized representation of the model, which are iso2, iso3, and
    country_name.
    - lookup_field: The field to use for lookups, which is the id field of the model.

    Example usage:

    serializer = CountrySerializer(data=data)
    if serializer.is_valid():
        serializer.save()
    """
    country_name = serializers.CharField(source='idmc_short_name')

    class Meta:
        model = Country
        fields = (
            'iso2',
            'iso3',
            'country_name',
        )
        lookup_field = 'id'


class ConflictSerializer(serializers.ModelSerializer):
    """

    """
    class Meta:
        model = Conflict
        fields = (
            'iso3',
            'country_name',
            'year',
            'new_displacement',
            'new_displacement_rounded',
            'total_displacement_rounded',
            'total_displacement',
        )
        lookup_field = 'id'


class DisasterSerializer(serializers.ModelSerializer):
    """

    Class: DisasterSerializer

    Description:
    This class is a serializer for the Disaster model. It defines the fields that should be serialized and provides
    serialization and deserialization capabilities for instances of the Disaster model.

    Attributes:
    - model: The Disaster model that this serializer is associated with.
    - fields: The fields of the Disaster model that should be serialized.
    - lookup_field: The field used as the lookup parameter when retrieving a single instance of the Disaster model.

    """
    class Meta:
        model = Disaster
        fields = (
            'iso3',
            'country_name',
            'year',
            'start_date',
            'start_date_accuracy',
            'end_date',
            'end_date_accuracy',
            'event_name',
            'new_displacement',
            'new_displacement_rounded',
            'total_displacement',
            'total_displacement_rounded',
            'hazard_category',
            'hazard_category_name',
            'hazard_sub_category',
            'hazard_sub_category_name',
            'hazard_type',
            'hazard_type_name',
            'hazard_sub_type',
            'hazard_sub_type_name',
            'glide_numbers',
            'event_codes',
            'event_codes_type',
        )
        lookup_field = 'id'


class DisplacementDataSerializer(serializers.ModelSerializer):
    """
    Serializer for converting DisplacementData instances into JSON format.

    Attributes:
        Meta: Meta class for defining the model and fields to be serialized.

    Example usage:
        serializer = DisplacementDataSerializer(data=data)
        if serializer.is_valid():
            json_data = serializer.data
        else:
            print(serializer.errors)
    """
    class Meta:
        model = DisplacementData
        fields = (
            'iso3',
            'country_name',
            'year',
            'conflict_new_displacement',
            'conflict_new_displacement_rounded',
            'conflict_total_displacement',
            'conflict_total_displacement_rounded',
            'disaster_new_displacement',
            'disaster_new_displacement_rounded',
            'disaster_total_displacement',
            'disaster_total_displacement_rounded',
        )


class PublicFigureAnalysisSerializer(serializers.ModelSerializer):
    """
    Class: PublicFigureAnalysisSerializer

    Serializes PublicFigureAnalysis objects

    """
    figure_cause_name = serializers.SerializerMethodField('get_figure_cause_name')
    figure_category_name = serializers.SerializerMethodField('get_figure_category_name')

    def get_figure_cause_name(self, obj):
        return Crisis.CRISIS_TYPE.get(obj.figure_cause).label

    def get_figure_category_name(self, obj):
        return Figure.FIGURE_CATEGORY_TYPES.get(obj.figure_category).label

    class Meta:
        model = PublicFigureAnalysis
        fields = (
            'iso3',
            'year',
            'figure_cause',
            'figure_cause_name',
            'figure_category',
            'figure_category',
            'figure_category_name',
            'description',
            'figures',
            'figures_rounded',
            # TODO:
            # Add country_name
        )


class StatusLogSerializer(serializers.ModelSerializer):
    """
    Serializer for the StatusLog model.

    This serializer is used to convert StatusLog objects to JSON and vice versa.

    Attributes:
        model (django.db.models.Model): The StatusLog model that the serializer is based on.
        fields (str): A string representing the fields from the model that should be included in the serialized
        representation. If set to '__all__', all fields will be included.

    """
    class Meta:
        model = StatusLog
        fields = '__all__'


class ReleaseMetadataSerializer(serializers.ModelSerializer):
    """

    Class: ReleaseMetadataSerializer

    Description:
        This class is responsible for serializing and deserializing ReleaseMetadata objects.

    Methods:
        - create(self, validated_data): This method is used to create a new ReleaseMetadata object with the given
        validated data.

    Attributes:
        - Meta (nested class): This is a nested class that defines the metadata for the serializer. It specifies the
        model to be used and the fields to include in the serialization process.

    Authors:
        [Your Name]

    """
    class Meta:
        model = ReleaseMetadata
        fields = ('pre_release_year', 'release_year')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['modified_by'] = user
        return ReleaseMetadata.objects.create(**validated_data)


class DisaggregationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Disaggregation model.

    Responsible for serializing and deserializing Disaggregation instances into JSON format.

    Attributes:
        model (model): The model to be used for serialization and deserialization.
        fields (tuple): A tuple containing the fields to be serialized and deserialized.

    """
    class Meta:
        model = GiddFigure
        fields = (
            'iso3',
            'figure',
            'country_name',
            'geographical_region_name',
            'year',
            'locations_coordinates',
            'unit',
            'category',
            'cause',
            'term',
            'total_figures',
            'household_size',
            'reported',
            'start_date',
            'end_date',
            'start_date_accuracy',
            'end_date_accuracy',
            'stock_date',
            'stock_date_accuracy',
            'stock_reporting_date',
            'sources',
            'publishers',
            'gidd_event',
            'is_housing_destruction',
            'locations_names',
            'locations_accuracy',
            'locations_type',
            'displacement_occurred',
        )


class IdpsSaddEstimateSerializer(serializers.ModelSerializer):
    """
    Class: IdpsSaddEstimateSerializer

    This class is a serializer for the IdpsSaddEstimate model. It is used to serialize and validate data when creating
    or updating instances of the model.

    Attributes:
    - model: The model class associated with this serializer.
    - exclude: A list of field names to be excluded from the serialized representation.

    Methods:
    - validate(validated_data): This method is called to perform validation on the input data. It is called after the
    default validation performed by the superclass. It takes the validated data as input and returns the validated data
    after performing additional validation. In this method, the country name and iso3 fields are calculated based on the
    country field and added to the validated data.

    Example Usage:
    serializer = IdpsSaddEstimateSerializer(data=data)
    if serializer.is_valid():
        validated_data = serializer.validated_data
        # Perform further actions with the validated data
    else:
        errors = serializer.errors
        # Handle validation errors
    """

    class Meta:
        model = IdpsSaddEstimate
        exclude = ['iso3', 'country_name']  # This are calculated by country

    def validate(self, validated_data):
        validated_data = super().validate(validated_data)
        country = validated_data['country']
        validated_data['country_name'] = country.name
        validated_data['iso3'] = country.iso3
        return validated_data

from rest_framework import serializers

from apps.users.models import User
from apps.contrib.serializers import MetaInformationSerializerMixin
from apps.country.models import Summary, ContextualAnalysis, HouseholdSize


class SummarySerializer(MetaInformationSerializerMixin, serializers.ModelSerializer):
    """
    Serializes the Summary model for data retrieval and deserialization.

    Inherited Mixins:
    - MetaInformationSerializerMixin: Adds metadata fields to the serialized data.

    Serializer Meta:
    - model: Summary
    - fields: '__all__' (All fields of the Summary model are included in the serialization)

    Usage:
    summary_serializer = SummarySerializer(data=request.data)
    if summary_serializer.is_valid():
        summary = summary_serializer.save()
        serialized_data = SummarySerializer(summary).data
    """
    class Meta:
        model = Summary
        fields = '__all__'


class ContextualAnalysisSerializer(MetaInformationSerializerMixin, serializers.ModelSerializer):
    """
    Class for serializing ContextualAnalysis model instances.

    Inherits from the MetaInformationSerializerMixin and serializers.ModelSerializer classes.

    Attributes:
        Meta:
            model (Model): The ContextualAnalysis model that will be serialized.
            fields (list): The fields to be included in the serialized output. If set to '__all__', all fields of the model will be included.

    """
    class Meta:
        model = ContextualAnalysis
        fields = '__all__'


class HouseholdSizeCliImportSerializer(serializers.ModelSerializer):
    """Serialize and deserialize HouseholdSize objects for CLI import.

    This class provides the necessary serialization and deserialization logic
    for the HouseholdSize model when importing data through the command line interface (CLI).

    Attributes:
        created_at (DateTimeField): The date and time when the object was created.
        modified_at (DateTimeField): The date and time when the object was last modified.
        created_by (PrimaryKeyRelatedField): The primary key of the User who created the object.
        last_modified_by (PrimaryKeyRelatedField): The primary key of the User who last modified the object.

    Meta:
        model (HouseholdSize): The model class used for serialization and deserialization.
        fields (str): A string representing the fields to be included in the serialization.

    """
    created_at = serializers.DateTimeField()
    modified_at = serializers.DateTimeField()
    created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    last_modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = HouseholdSize
        fields = '__all__'

from rest_framework import serializers

from apps.contrib.serializers import MetaInformationSerializerMixin
from apps.country.models import Summary, ContextualAnalysis, HouseholdSize


class SummarySerializer(MetaInformationSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = '__all__'


class ContextualAnalysisSerializer(MetaInformationSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ContextualAnalysis
        fields = '__all__'


class HouseholdSizeSerializer(MetaInformationSerializerMixin, serializers.ModelSerializer):
    created_at = serializers.DateTimeField()
    modified_at = serializers.DateTimeField()

    class Meta:
        model = HouseholdSize
        fields = '__all__'

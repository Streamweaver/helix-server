from rest_framework import serializers

from apps.users.models import User
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


class HouseholdSizeCliImportSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField()
    modified_at = serializers.DateTimeField()
    created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    last_modified_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = HouseholdSize
        fields = '__all__'

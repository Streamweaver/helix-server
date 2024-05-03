import django_filters
from rest_framework import serializers
from django.db.models import Q

from apps.crisis.models import Crisis

from .filters import ReleaseMetadataFilter, get_name_choices
from .models import (
    Conflict,
    Disaster,
    DisplacementData,
    GiddFigure,
    IdpsSaddEstimate,
    PublicFigureAnalysis,
    ReleaseMetadata,
)


class RestConflictFilterSet(ReleaseMetadataFilter):
    start_year = django_filters.NumberFilter(field_name='start_year', method='filter_start_year')
    end_year = django_filters.NumberFilter(field_name='end_year', method='filter_end_year')

    class Meta:
        model = Conflict
        fields = {
            'id': ['iexact'],
            'iso3': ['iexact'],
        }

    def filter_start_year(self, queryset, name, value):
        return queryset.filter(year__gte=value)

    def filter_end_year(self, queryset, name, value):
        return queryset.filter(year__lte=value)


class RestDisasterFilterSet(ReleaseMetadataFilter):

    class Meta:
        model = Disaster
        fields = {
            'iso3': ['iexact'],
        }

    @property
    def qs(self):
        qs = super().qs
        return qs.filter(new_displacement__gt=0)


class RestDisplacementDataFilterSet(ReleaseMetadataFilter):
    cause = django_filters.ChoiceFilter(
        method='filter_cause',
        choices=get_name_choices(Crisis.CRISIS_TYPE),
    )

    class Meta:
        model = DisplacementData
        fields = {
            'iso3': ['iexact'],
        }

    def filter_cause(self, queryset, name, value):
        if value.lower() == Crisis.CRISIS_TYPE.CONFLICT.name.lower():
            return queryset.filter(
                Q(conflict_new_displacement__gt=0) |
                Q(conflict_total_displacement__gt=0)
            )
        elif value.lower() == Crisis.CRISIS_TYPE.DISASTER.name.lower():
            return queryset.filter(
                Q(disaster_new_displacement__gt=0) |
                Q(disaster_total_displacement__gt=0)
            )

    @property
    def qs(self):
        qs = super().qs
        if 'cause' not in self.data:
            return qs.filter(
                Q(conflict_new_displacement__gt=0) |
                Q(conflict_total_displacement__gt=0) |
                Q(disaster_new_displacement__gt=0) |
                Q(disaster_total_displacement__gt=0)
            )
        return qs


class IdpsSaddEstimateFilter(ReleaseMetadataFilter):
    cause = django_filters.ChoiceFilter(
        method='filter_cause',
        choices=get_name_choices(Crisis.CRISIS_TYPE),
    )

    class Meta:
        model = IdpsSaddEstimate
        fields = {
            'iso3': ['iexact'],
        }

    def filter_cause(self, queryset, name, value):
        # NOTE: this filter is used inside displacement export
        if value.lower() == Crisis.CRISIS_TYPE.CONFLICT.name.lower():
            return queryset.filter(
                cause=Crisis.CRISIS_TYPE.CONFLICT.value,
            )
        elif value.lower() == Crisis.CRISIS_TYPE.DISASTER.name.lower():
            return queryset.filter(
                cause=Crisis.CRISIS_TYPE.DISASTER.value,
            )
        return queryset


class PublicFigureAnalysisFilterSet(ReleaseMetadataFilter):
    cause = django_filters.ChoiceFilter(
        method='filter_cause',
        choices=get_name_choices(Crisis.CRISIS_TYPE),
    )

    class Meta:
        model = PublicFigureAnalysis
        fields = {
            'iso3': ['iexact'],
        }

    def filter_cause(self, queryset, name, value):
        # NOTE: this filter is used inside displacement export
        if value.lower() == Crisis.CRISIS_TYPE.CONFLICT.name.lower():
            return queryset.filter(
                figure_cause=Crisis.CRISIS_TYPE.CONFLICT.value,
            )

        elif value.lower() == Crisis.CRISIS_TYPE.DISASTER.name.lower():
            return queryset.filter(
                figure_cause=Crisis.CRISIS_TYPE.DISASTER.value,
            )
        return queryset


class DisaggregationFilterSet(django_filters.FilterSet):
    cause = django_filters.ChoiceFilter(
        method='filter_cause',
        choices=get_name_choices(Crisis.CRISIS_TYPE),
    )
    release_environment = django_filters.ChoiceFilter(
        method='no_op',
        choices=get_name_choices(ReleaseMetadata.ReleaseEnvironment),
    )

    class Meta:
        model = GiddFigure
        fields = {
            'iso3': ['in'],
            'disaster_type': ['in'],
        }

    def filter_cause(self, queryset, name, value):
        if value.lower() == Crisis.CRISIS_TYPE.CONFLICT.name.lower():
            return queryset.filter(
                cause=Crisis.CRISIS_TYPE.CONFLICT.value,
            )

        elif value.lower() == Crisis.CRISIS_TYPE.DISASTER.name.lower():
            return queryset.filter(
                cause=Crisis.CRISIS_TYPE.DISASTER.value,
            )
        return queryset

    def no_op(self, qs, name, value):
        return qs

    def get_release_metadata(self):
        release_meta_data = ReleaseMetadata.objects.last()
        if not release_meta_data:
            raise serializers.ValidationError('Release metadata is not configured.')
        return release_meta_data

    def filter_release_environment(self, qs, value):
        release_meta_data = self.get_release_metadata()
        if value.lower() == ReleaseMetadata.ReleaseEnvironment.PRE_RELEASE.name.lower():
            return qs.filter(year=release_meta_data.pre_release_year)
        return qs.filter(year=release_meta_data.release_year)

    @property
    def qs(self):
        qs = super().qs
        release_environment_name = self.data.get(
            'release_environment',
            ReleaseMetadata.ReleaseEnvironment.RELEASE.name,
        )
        qs = self.filter_release_environment(qs, release_environment_name)
        return qs

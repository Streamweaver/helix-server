import django_filters
from django.db.models import Q
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
from apps.crisis.models import Crisis


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
    cause = django_filters.CharFilter(method='filter_cause')

    class Meta:
        model = DisplacementData
        fields = {
            'iso3': ['iexact'],
        }

    def filter_cause(self, queryset, name, value):
        if value == 'conflict':
            return queryset.filter(
                Q(conflict_new_displacement__gt=0) |
                Q(conflict_total_displacement__gt=0)
            )
        elif value == 'disaster':
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
    cause = django_filters.CharFilter(method='filter_cause')

    class Meta:
        model = IdpsSaddEstimate
        fields = {
            'iso3': ['iexact'],
        }

    def filter_cause(self, queryset, name, value):
        # NOTE: this filter is used inside displacement export
        if value == 'conflict':
            return queryset.filter(
                cause=Crisis.CRISIS_TYPE.CONFLICT.value,
            )

        elif value == 'disaster':
            return queryset.filter(
                cause=Crisis.CRISIS_TYPE.DISASTER.value,
            )
        return queryset


class PublicFigureAnalysisFilterSet(ReleaseMetadataFilter):
    cause = django_filters.CharFilter(method='filter_cause')

    class Meta:
        model = PublicFigureAnalysis
        fields = {
            'iso3': ['iexact'],
        }

    def filter_cause(self, queryset, name, value):
        # NOTE: this filter is used inside displacement export
        if value == 'conflict':
            return queryset.filter(
                cause=Crisis.CRISIS_TYPE.CONFLICT.value,
            )

        elif value == 'disaster':
            return queryset.filter(
                cause=Crisis.CRISIS_TYPE.DISASTER.value,
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
        if value == Crisis.CRISIS_TYPE.CONFLICT.name:
            return queryset.filter(
                cause=Crisis.CRISIS_TYPE.CONFLICT.value,
            )

        elif value == Crisis.CRISIS_TYPE.DISASTER.name:
            return queryset.filter(
                cause=Crisis.CRISIS_TYPE.DISASTER.value,
            )
        return queryset

    def no_op(self, qs, name, value):
        return qs

    def filter_release_environment(self, qs, value):
        release_meta_data = self.get_release_metadata()
        if value == ReleaseMetadata.ReleaseEnvironment.PRE_RELEASE.name:
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

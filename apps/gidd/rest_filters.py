import django_filters
from rest_framework import serializers
from django.db.models import Q

from apps.crisis.models import Crisis

from .enums import CRISIS_TYPE_PUBLIC
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
    """

    RestConflictFilterSet is a class that extends ReleaseMetadataFilter class for filtering Conflict objects based on start year and end year.

    Attributes:
    - start_year (django_filters.NumberFilter): A filter for the start year field in Conflict model. It is defined as a NumberFilter that uses the method 'filter_start_year' for filtering.
    - end_year (django_filters.NumberFilter): A filter for the end year field in Conflict model. It is defined as a NumberFilter that uses the method 'filter_end_year' for filtering.

    Meta:
    - model: The model that the RestConflictFilterSet is associated with is Conflict model.
    - fields: A dictionary of fields to be filtered. In this case, it contains 'id' and 'iso3' fields with the 'iexact' lookup.


    Methods:
    - filter_start_year(queryset, name, value): This method is called by the start_year filter to apply filtering based on the start year. If the value is not provided, the original queryset is returned. Otherwise, the queryset is filtered to include Conflict objects with a year greater than or equal to the provided start year.
    Parameters:
        - queryset (QuerySet): The original queryset containing Conflict objects.
        - name (str): The name of the field being filtered (start_year).
        - value (int): The value to be used for filtering (start year).

    - filter_end_year(queryset, name, value): This method is called by the end_year filter to apply filtering based on the end year. If the value is not provided, the original queryset is returned. Otherwise, the queryset is filtered to include Conflict objects with a year less than or equal to the provided end year.
    Parameters:
        - queryset (QuerySet): The original queryset containing Conflict objects.
        - name (str): The name of the field being filtered (end_year).
        - value (int): The value to be used for filtering (end year).

    """
    start_year = django_filters.NumberFilter(field_name='start_year', method='filter_start_year')
    end_year = django_filters.NumberFilter(field_name='end_year', method='filter_end_year')

    class Meta:
        model = Conflict
        fields = {
            'id': ['iexact'],
            'iso3': ['iexact'],
        }

    def filter_start_year(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(year__gte=value)

    def filter_end_year(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(year__lte=value)


class RestDisasterFilterSet(ReleaseMetadataFilter):
    """

    RestDisasterFilterSet

    This class is a subclass of ReleaseMetadataFilter and provides custom filters for the Disaster model. It filters the queryset based on the event name, start year, and end year.

    Properties:
    - event_name: A CharFilter that filters the queryset based on the event name.
    - start_year: A NumberFilter that filters the queryset based on the start year.
    - end_year: A NumberFilter that filters the queryset based on the end year.

    Methods:
    - filter_event_name(queryset, name, value): Filters the queryset by event name. If no value is provided, the queryset is returned unchanged. Otherwise, the queryset is filtered to include only records that have an event name containing the provided value (case-insensitive).
    - filter_start_year(queryset, name, value): Filters the queryset by start year. If no value is provided, the queryset is returned unchanged. Otherwise, the queryset is filtered to include only records that have a year greater than or equal to the provided value.
    - filter_end_year(queryset, name, value): Filters the queryset by end year. If no value is provided, the queryset is returned unchanged. Otherwise, the queryset is filtered to include only records that have a year less than or equal to the provided value.
    - qs(): Returns the filtered queryset after applying an additional filter to include only records with a new_displacement greater than 0.

    """
    event_name = django_filters.CharFilter(method='filter_event_name')
    start_year = django_filters.NumberFilter(field_name='start_year', method='filter_start_year')
    end_year = django_filters.NumberFilter(field_name='end_year', method='filter_end_year')

    class Meta:
        model = Disaster
        fields = {
            'event_name': ['icontains'],
            'iso3': ['in'],
            'hazard_type': ['in'],
        }

    def filter_event_name(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(event_name__icontains=value)

    def filter_start_year(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(year__gte=value)

    def filter_end_year(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(year__lte=value)

    @property
    def qs(self):
        qs = super().qs
        return qs.filter(new_displacement__gt=0)


class RestDisplacementDataFilterSet(ReleaseMetadataFilter):
    """
    RestDisplacementDataFilterSet class is a filter set used to filter RestDisplacementData objects based on certain criteria.

    Attributes:
    - cause: A django_filters.ChoiceFilter that filters the objects based on the cause of displacement. The choices are retrieved from the get_name_choices() function using the CRISIS_TYPE_PUBLIC constant.

    - start_year: A django_filters.NumberFilter that filters the objects based on the start year. It only includes objects with a year greater than or equal to the provided value.

    - end_year: A django_filters.NumberFilter that filters the objects based on the end year. It only includes objects with a year less than or equal to the provided value.

    Methods:
    - filter_start_year(queryset, name, value): This method filters the queryset based on the start year. If no value is provided, the queryset is returned unchanged.

    - filter_end_year(queryset, name, value): This method filters the queryset based on the end year. If no value is provided, the queryset is returned unchanged.

    - filter_cause(queryset, name, value): This method filters the queryset based on the cause. If no value is provided, the queryset is returned unchanged.
        - If the value is 'CONFlict', it includes objects with conflict_new_displacement > 0 or conflict_total_displacement > 0.
        - If the value is 'DISASTER', it includes objects with disaster_new_displacement > 0 or disaster_total_displacement > 0.

    Properties:
    - qs: This property returns the filtered queryset based on the provided criteria. If no cause is specified, it includes objects with conflict or disaster displacement.

    This class extends ReleaseMetadataFilter and uses the DisplacementData model as its Meta model. The fields it filters include 'iso3' with 'in' lookup.
    """
    cause = django_filters.ChoiceFilter(
        method='filter_cause',
        choices=get_name_choices(CRISIS_TYPE_PUBLIC),
    )
    start_year = django_filters.NumberFilter(field_name='start_year', method='filter_start_year')
    end_year = django_filters.NumberFilter(field_name='end_year', method='filter_end_year')

    class Meta:
        model = DisplacementData
        fields = {
            'iso3': ['in'],
        }

    def filter_start_year(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(year__gte=value)

    def filter_end_year(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(year__lte=value)

    def filter_cause(self, queryset, name, value):
        if not value:
            return queryset
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
        return queryset

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
    """

    Class for filtering IdpsSaddEstimate objects based on release metadata.

    Attributes:
        cause (django_filters.ChoiceFilter): Filter for cause of displacement.
        start_year (django_filters.NumberFilter): Filter for start year of displacement.
        end_year (django_filters.NumberFilter): Filter for end year of displacement.

    Meta:
        model (IdpsSaddEstimate): The model class used by the filter.
        fields (dict): Dictionary of fields to be used for filtering.

    Methods:
        filter_start_year(queryset, name, value): Filters queryset based on start year.
        filter_end_year(queryset, name, value): Filters queryset based on end year.
        filter_cause(queryset, name, value): Filters queryset based on cause of displacement.

    """
    cause = django_filters.ChoiceFilter(
        method='filter_cause',
        choices=get_name_choices(CRISIS_TYPE_PUBLIC),
    )
    start_year = django_filters.NumberFilter(field_name='start_year', method='filter_start_year')
    end_year = django_filters.NumberFilter(field_name='end_year', method='filter_end_year')

    class Meta:
        model = IdpsSaddEstimate
        fields = {
            'iso3': ['in'],
        }

    def filter_start_year(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(year__gte=value)

    def filter_end_year(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(year__lte=value)

    def filter_cause(self, queryset, name, value):
        if not value:
            return queryset
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
    """
    This class is a filter set used for filtering instances of the PublicFigureAnalysis model. It extends the ReleaseMetadataFilter class.

    Attributes:
        cause (django_filters.ChoiceFilter): A choice filter used for filtering instances based on the cause of the crisis. It is initialized with a method 'filter_cause' and the choices are obtained from the 'get_name_choices' function with the argument 'CRISIS_TYPE_PUBLIC'.

        start_year (django_filters.NumberFilter): A number filter used for filtering instances based on the start year. It is initialized with a field_name 'start_year' and a method 'filter_start_year'.

        end_year (django_filters.NumberFilter): A number filter used for filtering instances based on the end year. It is initialized with a field_name 'end_year' and a method 'filter_end_year'.

    Meta:
        model (PublicFigureAnalysis): The model class associated with this filter set.

        fields (dict): A dictionary specifying the fields to be filtered. The 'iso3' field is filtered using the 'in' lookup.

    Methods:
        filter_start_year(queryset, name, value):
            Filters the queryset based on the start year. If the value is not provided, the queryset is returned as is. Otherwise, the queryset is filtered to include only instances with a year greater than or equal to the specified value.

        filter_end_year(queryset, name, value):
            Filters the queryset based on the end year. If the value is not provided, the queryset is returned as is. Otherwise, the queryset is filtered to include only instances with a year less than or equal to the specified value.

        filter_cause(queryset, name, value):
            Filters the queryset based on the cause of the crisis. If the value is not provided, the queryset is returned as is. If the value is 'CONFLICT', the queryset is filtered to include only instances with a figure_cause equal to the 'CONFLICT' value of the Crisis.CRISIS_TYPE enum. If the value is 'DISASTER', the queryset is filtered to include only instances with a figure_cause equal to the 'DISASTER' value of the Crisis.CRISIS_TYPE enum.

    Note:
        The filter_cause method mentioned in the documentation is used inside the displacement export.
    """
    cause = django_filters.ChoiceFilter(
        method='filter_cause',
        choices=get_name_choices(CRISIS_TYPE_PUBLIC),
    )
    start_year = django_filters.NumberFilter(field_name='start_year', method='filter_start_year')
    end_year = django_filters.NumberFilter(field_name='end_year', method='filter_end_year')

    class Meta:
        model = PublicFigureAnalysis
        fields = {
            'iso3': ['in'],
        }

    def filter_start_year(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(year__gte=value)

    def filter_end_year(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(year__lte=value)

    def filter_cause(self, queryset, name, value):
        if not value:
            return queryset
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
    """
    A class representing a filter set for the Disaggregation model.

    This filter set allows for filtering the Disaggregation objects based on certain conditions.

    Attributes:
        cause: A ChoiceFilter for filtering by cause.
        release_environment: A ChoiceFilter for filtering by release environment.

    Methods:
        filter_cause(queryset, name, value): Filters the queryset based on the cause parameter.
        no_op(qs, name, value): A no-op filter method.
        get_release_metadata(): Retrieves the latest release metadata.
        filter_release_environment(qs, value): Filters the queryset based on the release environment parameter.
        qs: Property returning the filtered queryset.

    """
    cause = django_filters.ChoiceFilter(
        method='filter_cause',
        choices=get_name_choices(CRISIS_TYPE_PUBLIC),
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
        if not value:
            return queryset
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


class DisaggregationPublicFigureAnalysisFilterSet(django_filters.FilterSet):
    """
    Class representing a filter set for the DisaggregationPublicFigureAnalysisFilterSet.

    Attributes:
        cause (django_filters.ChoiceFilter): A filter for the cause of the figure.
        release_environment (django_filters.ChoiceFilter): A filter for the release environment.

    Methods:
        filter_figure_cause: Filters the queryset based on the figure cause.
        no_op: No operation method, does not modify the queryset.
        get_release_metadata: Retrieves the latest release metadata object.
        filter_release_environment: Filters the queryset based on the release environment.
        qs: Overrides the default property to return a filtered queryset.

    """
    cause = django_filters.ChoiceFilter(
        method='filter_figure_cause',
        choices=get_name_choices(CRISIS_TYPE_PUBLIC),
    )
    release_environment = django_filters.ChoiceFilter(
        method='no_op',
        choices=get_name_choices(ReleaseMetadata.ReleaseEnvironment),
    )

    class Meta:
        model = PublicFigureAnalysis
        fields = {
            'iso3': ['in'],
        }

    def filter_figure_cause(self, qs, name, value):
        if not value:
            return qs
        # NOTE: this filter is used inside disaggregation export
        if value.lower() == Crisis.CRISIS_TYPE.CONFLICT.name.lower():
            return qs.filter(
                figure_cause=Crisis.CRISIS_TYPE.CONFLICT.value,
            )
        elif value.lower() == Crisis.CRISIS_TYPE.DISASTER.name.lower():
            return qs.filter(
                figure_cause=Crisis.CRISIS_TYPE.DISASTER.value,
            )
        return qs

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

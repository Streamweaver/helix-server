import typing
import django_filters
from rest_framework import serializers
from django.db.models import Q
from utils.filters import StringListFilter, IDListFilter
from apps.entry.models import ExternalApiDump
from apps.crisis.models import Crisis
from .enums import CRISIS_TYPE_PUBLIC
from .models import (
    Conflict,
    Disaster,
    StatusLog,
    PublicFigureAnalysis,
    DisplacementData,
    ReleaseMetadata,
)


def get_name_choices(enum_class) -> typing.List[typing.Tuple[str, str]]:
    """
    Returns a list of tuples containing name choices from the given enum class.

    Parameters:
    - enum_class (enum): The enum class to get the name choices from.

    Returns:
    - List of tuples: Each tuple contains two string values: the name and the label.

    Example usage:
    ```
    class MyEnum(Enum):
        VALUE_1 = "Value 1"
        VALUE_2 = "Value 2"

    choices = get_name_choices(MyEnum)
    print(choices)
    # Output: [('VALUE_1', 'Value 1'), ('VALUE_2', 'Value 2'), ('value_1', 'Value 1'), ('value_2', 'Value 2')]
    ```

    Notes:
    - The method returns the name choices from the enum class as tuples, where the first element of each tuple is the
    name of the enum item in uppercase, and the second element is the corresponding label.
    - The method also includes lowercase versions of the name choices in the returned list.
    """
    return [
        (i.name, i.label)
        for i in enum_class
    ] + [
        (i.name.lower(), i.label)
        for i in enum_class
    ]


class ReleaseMetadataFilter(django_filters.FilterSet):
    """

    """
    release_environment = django_filters.ChoiceFilter(
        method='no_op',
        choices=get_name_choices(ReleaseMetadata.ReleaseEnvironment),
    )

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
            return qs.filter(year__lte=release_meta_data.pre_release_year)
        return qs.filter(year__lte=release_meta_data.release_year)

    @property
    def qs(self):
        qs = super().qs
        release_environment_name = self.data.get(
            'release_environment',
            ReleaseMetadata.ReleaseEnvironment.RELEASE.name,
        )
        qs = self.filter_release_environment(qs, release_environment_name)
        return qs


class ConflictFilter(ReleaseMetadataFilter):
    """
    A class used to filter Conflict objects based on specific criteria.

    Inherits from the ReleaseMetadataFilter class.

    Attributes
    ----------
    Meta : class
        A nested class that specifies metadata about the ConflictFilter class.

        model : class
            The model class that the ConflictFilter is filtering.

        fields : dict
            A dictionary that specifies the fields and lookup types for filtering.

    Methods
    -------
    No additional methods are defined in this class.
    """
    class Meta:
        model = Conflict
        fields = {
            'id': ['iexact']
        }


class DisasterFilter(ReleaseMetadataFilter):
    """

    This class is a subclass of ReleaseMetadataFilter and is used for filtering disaster data based on various
    parameters.

    Attributes:
        - hazard_types: IDListFilter object that filters disaster data based on hazard types.
        - event_name: CharFilter object that filters disaster data based on event name.
        - start_year: NumberFilter object that filters disaster data based on start year.
        - end_year: NumberFilter object that filters disaster data based on end year.
        - countries_iso3: StringListFilter object that filters disaster data based on countries' ISO3 codes.

    Methods:
        - filter_event_name(queryset, name, value): Filters the queryset based on the event name.
        - filter_hazard_types(queryset, name, value): Filters the queryset based on the hazard types.
        - filter_start_year(queryset, name, value): Filters the queryset based on the start year.
        - filter_end_year(queryset, name, value): Filters the queryset based on the end year.
        - filter_countries_iso3(queryset, name, value): Filters the queryset based on the countries' ISO3 codes.

    Properties:
        - qs: Overrides the parent class's qs property and returns the filtered queryset with new_displacement greater
        than 0.

    """
    hazard_types = IDListFilter(method='filter_hazard_types')
    event_name = django_filters.CharFilter(method='filter_event_name')
    start_year = django_filters.NumberFilter(method='filter_start_year')
    end_year = django_filters.NumberFilter(method='filter_end_year')
    countries_iso3 = StringListFilter(method='filter_countries_iso3')

    class Meta:
        model = Disaster
        fields = {
            'id': ['iexact']
        }

    def filter_event_name(self, queryset, name, value):
        return queryset.filter(event_name__icontains=value)

    def filter_hazard_types(self, queryset, name, value):
        return queryset.filter(hazard_type__in=value)

    def filter_start_year(self, queryset, name, value):
        return queryset.filter(year__gte=value)

    def filter_end_year(self, queryset, name, value):
        return queryset.filter(year__lte=value)

    def filter_countries_iso3(self, queryset, name, value):
        return queryset.filter(iso3__in=value)

    @property
    def qs(self):
        qs = super().qs
        return qs.filter(new_displacement__gt=0)


class ConflictStatisticsFilter(ReleaseMetadataFilter):
    """
    Class: ConflictStatisticsFilter

    Subclass of: ReleaseMetadataFilter

    This class is used to filter conflict statistics based on various criteria such as countries, start year, end year,
    and country ISO3 code.

    Attributes:
        countries (StringListFilter): A filter for selecting conflicts based on countries.
        start_year (NumberFilter): A filter for selecting conflicts that occurred on or after a certain year.
        end_year (NumberFilter): A filter for selecting conflicts that occurred on or before a certain year.
        countries_iso3 (StringListFilter): A filter for selecting conflicts based on country ISO3 codes.

    Methods:
        filter_countries(queryset, name, value): Filters the queryset based on the specified countries.
        filter_start_year(queryset, name, value): Filters the queryset to select conflicts that occurred on or after the
        specified start year.
        filter_end_year(queryset, name, value): Filters the queryset to select conflicts that occurred on or before the
        specified end year.
        filter_countries_iso3(queryset, name, value): Filters the queryset based on the specified country ISO3 codes.

    """
    countries = StringListFilter(method='filter_countries')
    start_year = django_filters.NumberFilter(method='filter_start_year')
    end_year = django_filters.NumberFilter(method='filter_end_year')
    countries_iso3 = StringListFilter(method='filter_countries_iso3')

    class Meta:
        model = Conflict
        fields = ()

    def filter_countries(self, queryset, name, value):
        return queryset.filter(country__in=value)

    def filter_start_year(self, queryset, name, value):
        return queryset.filter(year__gte=value)

    def filter_end_year(self, queryset, name, value):
        return queryset.filter(year__lte=value)

    def filter_countries_iso3(self, queryset, name, value):
        return queryset.filter(iso3__in=value)


class DisasterStatisticsFilter(ReleaseMetadataFilter):
    """
    A class that represents a filter for disaster statistics.

    Attributes:
        hazard_types (IDListFilter): A filter for hazard types.
        countries (StringListFilter): A filter for countries.
        start_year (django_filters.NumberFilter): A filter for the starting year.
        end_year (django_filters.NumberFilter): A filter for the ending year.
        countries_iso3 (StringListFilter): A filter for countries' ISO3 codes.
    """
    hazard_types = IDListFilter(method='filter_hazard_types')
    countries = StringListFilter(method='filter_countries')
    start_year = django_filters.NumberFilter(method='filter_start_year')
    end_year = django_filters.NumberFilter(method='filter_end_year')
    countries_iso3 = StringListFilter(method='filter_countries_iso3')

    class Meta:
        model = Disaster
        fields = ()

    def filter_hazard_types(self, queryset, name, value):
        return queryset.filter(hazard_type__in=value)

    def filter_countries(self, queryset, name, value):
        return queryset.filter(country__in=value)

    def filter_start_year(self, queryset, name, value):
        return queryset.filter(year__gte=value)

    def filter_end_year(self, queryset, name, value):
        return queryset.filter(year__lte=value)

    def filter_countries_iso3(self, queryset, name, value):
        return queryset.filter(iso3__in=value)


class GiddStatusLogFilter(django_filters.FilterSet):
    """

    GiddStatusLogFilter class

    A class that provides filtering capabilities for the StatusLog model based on the status field.

    Attributes:
        status (StringListFilter): A filter for the status field.

    Methods:
        filter_by_status(qs, name, value): Filters the queryset based on the provided status values.

    """
    status = StringListFilter(method='filter_by_status')

    class Meta:
        model = StatusLog
        fields = ()

    def filter_by_status(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # coming from saved query
                return qs.filter(status__in=value)
            return qs.filter(status__in=[
                StatusLog.Status.get(item).value for item in value
            ])
        return qs


class PublicFigureAnalysisFilter(ReleaseMetadataFilter):
    """
    Class: PublicFigureAnalysisFilter

    This class is an implementation of ReleaseMetadataFilter used for filtering PublicFigureAnalysis model instances
    based on certain criteria.

    Attributes:
        - model: The model attribute specifies the model class that the filter is intended for, which is
        PublicFigureAnalysis in this case.
        - fields: The fields attribute is a dictionary that defines the available filter options for the
        PublicFigureAnalysis model. The key represents the field name, and the value is a list of available filter
        options for that field.

    """
    class Meta:
        model = PublicFigureAnalysis
        fields = {
            'iso3': ['exact'],
            'year': ['exact'],
        }


class DisplacementDataFilter(ReleaseMetadataFilter):
    """

    Class: DisplacementDataFilter

    Extends: ReleaseMetadataFilter

    Filters the DisplacementData model based on various parameters such as start year, end year, countries, and cause.

    Attributes:
    - start_year: A django_filters.NumberFilter instance that filters the queryset based on the start year of the
    displacement data.
    - end_year: A django_filters.NumberFilter instance that filters the queryset based on the end year of the
    displacement data.
    - countries_iso3: A StringListFilter instance that filters the queryset based on the ISO3 country codes.
    - cause: A django_filters.ChoiceFilter instance that filters the queryset based on the cause of the displacement.
    Can be 'conflict' or 'disaster'.

    Methods:
    - filter_start_year(queryset, name, value): Filters the queryset based on the start year.
    - filter_end_year(queryset, name, value): Filters the queryset based on the end year.
    - filter_countries_iso3(queryset, name, value): Filters the queryset based on the countries' ISO3 codes.
    - filter_cause(queryset, name, value): Filters the queryset based on the cause of the displacement.
    - qs(): Returns the filtered queryset based on the parameters.

    """
    start_year = django_filters.NumberFilter(method='filter_start_year')
    end_year = django_filters.NumberFilter(method='filter_end_year')
    countries_iso3 = StringListFilter(method='filter_countries_iso3')
    cause = django_filters.ChoiceFilter(
        method='filter_cause',
        choices=get_name_choices(CRISIS_TYPE_PUBLIC),
    )

    class Meta:
        model = DisplacementData
        fields = ()

    def filter_start_year(self, queryset, name, value):
        return queryset.filter(year__gte=value)

    def filter_end_year(self, queryset, name, value):
        return queryset.filter(year__lte=value)

    def filter_countries_iso3(self, queryset, name, value):
        return queryset.filter(iso3__in=value)

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


# Gidd filtets to api type map
GIDD_TRACKING_FILTERS = {
    DisasterFilter: ExternalApiDump.ExternalApiType.GIDD_DISASTER_GRAPHQL,
    ConflictFilter: ExternalApiDump.ExternalApiType.GIDD_CONFLICT_GRAPHQL,
    DisplacementDataFilter: ExternalApiDump.ExternalApiType.GIDD_DISPLACEMENT_DATA_GRAPHQL,
    PublicFigureAnalysisFilter: ExternalApiDump.ExternalApiType.GIDD_PFA_GRAPHQL,
    DisasterStatisticsFilter: ExternalApiDump.ExternalApiType.GIDD_DISASTER_STAT_GRAPHQL,
    ConflictStatisticsFilter: ExternalApiDump.ExternalApiType.GIDD_CONFLICT_STAT_GRAPHQL,
}

GIDD_API_TYPE_MAP = {
    # WHY? https://github.com/eamigo86/graphene-django-extras/blob/master/graphene_django_extras/filters/filter.py#L29
    f'{prefix}{filter_class.__name__}': api_type
    for prefix in ['Graphene', '']
    for filter_class, api_type in GIDD_TRACKING_FILTERS.items()
}

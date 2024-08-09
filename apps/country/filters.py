import graphene
import datetime
import django_filters
from django.db.models import Value
from django.utils import timezone
from django.db.models.functions import Lower, StrIndex
from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from django.http import HttpRequest

from apps.country.models import (
    Country,
    CountryRegion,
    GeographicalGroup,
    MonitoringSubRegion,
    ContextualAnalysis,
    Summary,
)
from apps.extraction.filters import (
    FigureExtractionFilterDataInputType,
    FigureExtractionFilterDataType,
)
from utils.filters import (
    IDListFilter,
    StringListFilter,
    NameFilterMixin,
    SimpleInputFilter,
    generate_type_for_filter_set,
)
from utils.figure_filter import (
    FigureFilterHelper,
    CountryFigureAggregateFilterDataType,
    CountryFigureAggregateFilterDataInputType,
)


class GeographicalGroupFilter(NameFilterMixin,
                              django_filters.FilterSet):
    """
    Filter class for GeographicalGroup model.

    Inherits from NameFilterMixin and django_filters.FilterSet.

    Attributes:
        name (django_filters.CharFilter): Filter for filtering by name.

    Meta:
        model (class): The model this filter is associated with (GeographicalGroup).
        fields (dict): A dictionary specifying the fields to filter on and the lookup types.

    Usage:
        filter = GeographicalGroupFilter(data=request.GET, queryset=queryset)
        filtered_queryset = filter.qs
    """
    name = django_filters.CharFilter(method='_filter_name')

    class Meta:
        model = GeographicalGroup
        fields = {
            'id': ['iexact'],
        }


class CountryRegionFilter(NameFilterMixin,
                          django_filters.FilterSet):
    """
    Filter class for filtering CountryRegion instances.
    Inherits from NameFilterMixin and django_filters.FilterSet.

    Attributes:
    - name: A CharFilter field used for filtering by name.
    - Meta: A class defining the metadata of the filter, including the model and fields to be filtered.

    Example usage:
    filter_set = CountryRegionFilter(data=request.GET, queryset=CountryRegion.objects.all())
    filtered_queryset = filter_set.qs
    """
    name = django_filters.CharFilter(method='_filter_name')

    class Meta:
        model = CountryRegion
        fields = {
            'id': ['iexact'],
        }


class CountryFilter(django_filters.FilterSet):
    """

    Class to filter Country objects based on different criteria.

    Filters:
    - country_name: Filters countries by name. Uses '_filter_name' method.
    - region_name: Filters countries by region name. Uses 'filter_region_name' method.
    - geographical_group_name: Filters countries by geographical group name. Uses 'filter_geo_group_name' method.
    - region_by_ids: Filters countries by a list of region ids. Uses 'filter_regions' method.
    - geo_group_by_ids: Filters countries by a list of geographical group ids. Uses 'filter_geo_groups' method.
    - filter_figures: Filters countries based on figure filters. Uses 'filter_by_figures' method.
    - aggregate_figures: No operation method.
    - events: Filters countries based on a list of event ids. Uses 'filter_by_events' method.
    - crises: Filters countries based on a list of crisis ids. Uses 'filter_by_crisis' method.

    Attributes:
    - request: HttpRequest object.
    - qs: QuerySet of Country objects.

    Methods:
    - noop: No operation method.
    - filter_by_figures: Filters countries based on figure filters.
    - filter_by_events: Filters countries based on a list of event ids.
    - filter_by_crisis: Filters countries based on a list of crisis ids.
    - _filter_name: Filters countries by name.
    - filter_geo_group_name: Filters countries by geographical group name.
    - filter_region_name: Filters countries by region name.
    - filter_regions: Filters countries by a list of region ids.
    - filter_geo_groups: Filters countries by a list of geographical group ids.
    - filter_year: No operation method.

    """
    country_name = django_filters.CharFilter(method='_filter_name')
    region_name = django_filters.CharFilter(method='filter_region_name')
    geographical_group_name = django_filters.CharFilter(method='filter_geo_group_name')
    region_by_ids = StringListFilter(method='filter_regions')
    geo_group_by_ids = StringListFilter(method='filter_geo_groups')

    filter_figures = SimpleInputFilter(FigureExtractionFilterDataInputType, method='filter_by_figures')
    aggregate_figures = SimpleInputFilter(CountryFigureAggregateFilterDataInputType, method='noop')

    # used in report country table
    events = IDListFilter(method='filter_by_events')
    crises = IDListFilter(method='filter_by_crisis')

    request: HttpRequest

    class Meta:
        model = Country
        fields = {
            'iso3': ['unaccent__icontains'],
            'id': ['iexact'],
        }

    def noop(self, qs, name, value):
        return qs

    def filter_by_figures(self, qs, _, value):
        return FigureFilterHelper.filter_using_figure_filters(qs, value, self.request)

    def filter_by_events(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(
            id__in=Country.objects.filter(events__in=value).values('id')
        )

    def filter_by_crisis(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(
            id__in=Country.objects.filter(crises__in=value).values('id')
        )

    def _filter_name(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.annotate(
            lname=Lower('idmc_short_name')
        ).annotate(
            idx=StrIndex('lname', Value(value.lower()))
        ).filter(idx__gt=0).order_by('idx', 'idmc_short_name')

    def filter_geo_group_name(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.select_related(
            'geographical_group'
        ).annotate(
            geo_name=Lower('geographical_group__name')
        ).annotate(
            idx=StrIndex('geo_name', Value(value.lower()))
        ).filter(idx__gt=0).order_by('idx', 'geo_name')

    def filter_region_name(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.select_related(
            'region'
        ).annotate(
            region_name=Lower('region__name')
        ).annotate(
            idx=StrIndex('region_name', Value(value.lower()))
        ).filter(idx__gt=0).order_by('idx', 'region_name')

    def filter_regions(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(region__in=value).distinct()

    def filter_geo_groups(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(geographical_group__in=value).distinct()

    def filter_year(self, qs, name, value):
        ''' Filter logic is applied in qs'''
        return qs

    @property
    def qs(self):
        # Aggregate filter logic
        aggregate_figures = self.data.get('aggregate_figures') or {}
        year = aggregate_figures.get('year')
        report_id = FigureFilterHelper.get_report_id_from_filter_data(aggregate_figures)
        report = report_id and FigureFilterHelper.get_report(report_id)
        # Only 1 is allowed among report and year
        if report and year:
            raise ValidationError(gettext('Cannot pass both report and year in filter'))

        start_date = None
        figure_qs, end_date = FigureFilterHelper.aggregate_data_generate(aggregate_figures, self.request)
        if end_date is None:
            year = year or timezone.now().year
            start_date = datetime.datetime(year=int(year), month=1, day=1)
            end_date = datetime.datetime(year=int(year), month=12, day=31)

        return super().qs.annotate(
            **Country._total_figure_disaggregation_subquery(
                figures=figure_qs,
                start_date=start_date,
                end_date=end_date,
            )
        )


class MonitoringSubRegionFilter(django_filters.FilterSet):
    """
    Class: MonitoringSubRegionFilter

    A class that defines a filter set for the MonitoringSubRegion model in Django.

    Attributes:
    - name (django_filters.CharFilter): A character filter for the name field.

    Methods:
    - _filter_name(queryset, name, value): A private method that filters the queryset based on the name field.

    """
    name = django_filters.CharFilter(method='_filter_name')

    class Meta:
        model = MonitoringSubRegion
        fields = ['id']

    def _filter_name(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.annotate(
            lname=Lower('name')
        ).annotate(
            idx=StrIndex('lname', Value(value.lower()))
        ).filter(idx__gt=0).order_by('idx', 'name')


class CountrySummaryFilter(django_filters.FilterSet):
    """
    FilterSet class for filtering summary objects by country.

    Filters the summary objects based on the selected country using the 'lte' and 'gte' operators on the 'created_at'
    field.

    Attributes:
        model (django.db.models.Model): The model class to which the filterset will be applied
        fields (dict): The fields on which the filters will be applied

    """
    class Meta:
        model = Summary
        fields = {
            'created_at': ['lte', 'gte']
        }


class ContextualAnalysisFilter(django_filters.FilterSet):
    """

    The `ContextualAnalysisFilter` class is a filter set class that is used for filtering data from the
    `ContextualAnalysis` model.

    Attributes:
        model (django.db.models.Model): The `ContextualAnalysis` model that will be filtered.

    Fields:
        The following fields are used for filtering the `ContextualAnalysis` data:
            - 'created_at': ['lte', 'gte'] (Filter by the 'created_at' attribute using the 'less than or equal to' and
            'greater than or equal to' conditions)

    Example usage:

        # Create an instance of the filter set
        filter_set = ContextualAnalysisFilter(data=request.GET, queryset=ContextualAnalysis.objects.all())

        # Apply filters on the queryset
        filtered_queryset = filter_set.qs

        # Iterate over the filtered queryset
        for analysis in filtered_queryset:
            # Do something with the filtered `ContextualAnalysis` objects

    Note: This documentation does not contain the actual example code.

    """
    class Meta:
        model = ContextualAnalysis
        fields = {
            'created_at': ['lte', 'gte']
        }


CountryFilterDataType, CountryFilterDataInputType = generate_type_for_filter_set(
    CountryFilter,
    'country.schema.country_list',
    'CountryFilterDataType',
    'CountryFilterDataInputType',
    custom_new_fields_map={
        'filter_figures': graphene.Field(FigureExtractionFilterDataType),
        'aggregate_figures': graphene.Field(CountryFigureAggregateFilterDataType),
    },
)


MonitoringSubRegionFilterDataType, MonitoringSubRegionFilterDataInputType = generate_type_for_filter_set(
    MonitoringSubRegionFilter,
    'country.schema.monitoring_sub_region_list',
    'MonitoringSubRegionFilterDataType',
    'MonitoringSubRegionFilterDataInputType',
)

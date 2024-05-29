import graphene
import django_filters
from django.http import HttpRequest

from apps.crisis.models import Crisis
from apps.extraction.filters import (
    FigureExtractionFilterDataInputType,
    FigureExtractionFilterDataType,
)
from utils.filters import (
    StringListFilter,
    NameFilterMixin,
    IDListFilter,
    SimpleInputFilter,
    generate_type_for_filter_set,
)
from utils.figure_filter import (
    FigureFilterHelper,
    FigureAggregateFilterDataType,
    FigureAggregateFilterDataInputType,
)
from django.db.models import Q, Count


class CrisisFilter(NameFilterMixin, django_filters.FilterSet):
    """

    Class: CrisisFilter

    This class is a subclass of django_filters.FilterSet and includes additional methods for filtering crises based on various parameters.

    Attributes:
    - name: A CharFilter used to filter crises by name.
    - countries: A IDListFilter used to filter crises by countries.
    - crisis_types: A StringListFilter used to filter crises by crisis types.
    - events: A IDListFilter used to filter crises by events.
    - filter_figures: A SimpleInputFilter used to filter crises based on figure extraction filter data.
    - aggregate_figures: A SimpleInputFilter used for aggregation of figures (no operation).
    - created_by_ids: A IDListFilter used to filter crises by creator IDs.
    - request: An instance of the HttpRequest class.

    Methods:
    - noop(self, qs, name, value): A method that returns the unchanged queryset. It is used as a placeholder method for the aggregate_figures filter.
    - filter_by_figures(self, qs, _, value): A method that filters the queryset based on figure filters using FigureFilterHelper.
    - filter_events(self, qs, name, value): A method that filters the queryset by events.
    - filter_countries(self, qs, name, value): A method that filters the queryset by countries.
    - filter_crisis_types(self, qs, name, value): A method that filters the queryset by crisis types.
    - filter_name(self, qs, name, value): A method that filters the queryset by name, searching for a match in either the crisis name or event name.
    - filter_created_by(self, qs, name, value): A method that filters the queryset by creator IDs.
    - qs(self): A property method that returns the filtered queryset with additional annotations and prefetches.

    Note: This class is used as a filter for the Crisis model, and provides various filtering options for retrieving specific crises based on different criteria.
    """
    name = django_filters.CharFilter(method='filter_name')
    countries = IDListFilter(method='filter_countries')
    crisis_types = StringListFilter(method='filter_crisis_types')
    events = IDListFilter(method='filter_events')

    filter_figures = SimpleInputFilter(FigureExtractionFilterDataInputType, method='filter_by_figures')
    aggregate_figures = SimpleInputFilter(FigureAggregateFilterDataInputType, method='noop')

    # used in report crisis table
    created_by_ids = IDListFilter(method='filter_created_by')

    request: HttpRequest

    class Meta:
        model = Crisis
        fields = {
            'created_at': ['lt', 'lte', 'gt', 'gte'],
            'start_date': ['lt', 'lte', 'gt', 'gte'],
            'end_date': ['lt', 'lte', 'gt', 'gte'],
        }

    def noop(self, qs, name, value):
        return qs

    def filter_by_figures(self, qs, _, value):
        return FigureFilterHelper.filter_using_figure_filters(qs, value, self.request)

    def filter_events(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(events__in=value).distinct()

    def filter_countries(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(countries__in=value).distinct()

    def filter_crisis_types(self, qs, name, value):
        if not value:
            return qs
        if isinstance(value[0], int):
            # internal filtering
            return qs.filter(crisis_type__in=value).distinct()
        # client side filtering
        return qs.filter(crisis_type__in=[
            Crisis.CRISIS_TYPE.get(item).value for item in value
        ]).distinct()

    def filter_name(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(Q(name__unaccent__icontains=value) | Q(events__name__unaccent__icontains=value)).distinct()

    def filter_created_by(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(created_by__in=value)

    @property
    def qs(self):
        figure_qs, reference_date = FigureFilterHelper.aggregate_data_generate(
            self.data.get('aggregate_figures'),
            self.request,
        )
        return super().qs.annotate(
            **Crisis._total_figure_disaggregation_subquery(
                figures=figure_qs,
                reference_date=reference_date,
            ),
            **Crisis.annotate_review_figures_count(),
            event_count=Count('events'),
        ).prefetch_related('events').distinct()


CrisisFilterDataType, CrisisFilterDataInputType = generate_type_for_filter_set(
    CrisisFilter,
    'crisis.schema.crisis_list',
    'CrisisFilterDataType',
    'CrisisFilterDataInputType',
    custom_new_fields_map={
        'filter_figures': graphene.Field(FigureExtractionFilterDataType),
        'aggregate_figures': graphene.Field(FigureAggregateFilterDataType),
    },
)

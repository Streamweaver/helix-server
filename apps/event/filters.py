import graphene
import django_filters
from django.db.models import Q, Count
from django.http import HttpRequest
from django.contrib.postgres.aggregates.general import ArrayAgg

from apps.event.models import (
    Actor,
    Event,
    DisasterSubType,
    DisasterType,
    DisasterCategory,
    DisasterSubCategory,
    ContextOfViolence,
    Violence,
    ViolenceSubType,
    OsvSubType,
    OtherSubType,
)
from apps.entry.models import Figure
from apps.crisis.models import Crisis
from apps.extraction.filters import (
    FigureExtractionFilterDataInputType,
    FigureExtractionFilterDataType,
)
from utils.filters import (
    NameFilterMixin,
    StringListFilter,
    IDListFilter,
    SimpleInputFilter,
    generate_type_for_filter_set,
)
from utils.figure_filter import (
    FigureFilterHelper,
    FigureAggregateFilterDataType,
    FigureAggregateFilterDataInputType,
)
from apps.event.constants import OSV
from django.db import models
from apps.common.enums import QA_RULE_TYPE


class EventFilter(NameFilterMixin,
                  django_filters.FilterSet):
    """
    EventFilter class is used to filter event objects based on various criteria. It is a subclass of NameFilterMixin and django_filters.FilterSet.

    Attributes:
        - name: CharFilter to filter events by name
        - crisis_by_ids: IDListFilter to filter events by crisis IDs
        - event_types: StringListFilter to filter events by event types
        - countries: IDListFilter to filter events by countries
        - osv_sub_type_by_ids: IDListFilter to filter events by OSV sub types
        - disaster_sub_types: IDListFilter to filter events by disaster sub types
        - violence_types: IDListFilter to filter events by violence types
        - violence_sub_types: IDListFilter to filter events by violence sub types
        - created_by_ids: IDListFilter to filter events by created by user IDs
        - qa_rule: CharFilter to filter events by QA rule
        - context_of_violences: IDListFilter to filter events by context of violence IDs
        - review_status: StringListFilter to filter events by review status
        - assignees: IDListFilter to filter events by assignees IDs
        - assigners: IDListFilter to filter events by assigners IDs
        - filter_figures: SimpleInputFilter to filter events by figure extraction filter data input
        - aggregate_figures: SimpleInputFilter to aggregate data using figure aggregate filter data input

    Properties:
        - qs: Queryset property that returns the filtered queryset of events

    Methods:
        - noop: Method used as a filter method for aggregate_figures filter, no operation is performed
        - filter_by_figures: Method used as a filter method for filter_figures filter, filters events based on figure filters
        - filter_countries: Method used as a filter method for countries filter, filters events by countries
        - filter_disaster_sub_types: Method used as a filter method for disaster_sub_types filter, filters events by disaster sub types
        - filter_violence_types: Method used as a filter method for violence_types filter, filters events by violence types
        - filter_violence_sub_types: Method used as a filter method for violence_sub_types filter, filters events by violence sub types
        - filter_crises: Method used as a filter method for crisis_by_ids filter, filters events by crisis IDs
        - filter_event_types: Method used as a filter method for event_types filter, filters events by event types
        - filter_review_status: Method used as a filter method for review_status filter, filters events by review status
        - filter_name: Method used as a filter method for name filter, filters events by name
        - filter_osv_sub_types: Method used as a filter method for osv_sub_type_by_ids filter, filters events by OSV sub types
        - filter_qa_rule: Method used as a filter method for qa_rule filter, filters events by QA rule
        - filter_context_of_violences: Method used as a filter method for context_of_violences filter, filters events by context of violence IDs
        - filter_assigners: Method used as a filter method for assigners filter, filters events by assigners IDs
        - filter_assignees: Method used as a filter method for assignees filter, filters events by assignees IDs
        - filter_created_by: Method used as a filter method for created_by_ids filter, filters events by created by user IDs
    """
    name = django_filters.CharFilter(method='filter_name')
    crisis_by_ids = IDListFilter(method='filter_crises')
    event_types = StringListFilter(method='filter_event_types')
    countries = IDListFilter(method='filter_countries')

    osv_sub_type_by_ids = IDListFilter(method='filter_osv_sub_types')
    # used in report entry table
    disaster_sub_types = IDListFilter(method='filter_disaster_sub_types')
    violence_types = IDListFilter(method='filter_violence_types')
    violence_sub_types = IDListFilter(method='filter_violence_sub_types')
    created_by_ids = IDListFilter(method='filter_created_by')
    qa_rule = django_filters.CharFilter(method='filter_qa_rule')
    context_of_violences = IDListFilter(method='filter_context_of_violences')
    review_status = StringListFilter(method='filter_review_status')
    assignees = IDListFilter(method='filter_assignees')
    assigners = IDListFilter(method='filter_assigners')

    filter_figures = SimpleInputFilter(FigureExtractionFilterDataInputType, method='filter_by_figures')
    aggregate_figures = SimpleInputFilter(FigureAggregateFilterDataInputType, method='noop')

    request: HttpRequest

    class Meta:
        model = Event
        fields = {
            'created_at': ['lte', 'lt', 'gte', 'gt'],
            'start_date': ['lte', 'lt', 'gte', 'gt'],
            'end_date': ['lte', 'lt', 'gte', 'gt'],
            'ignore_qa': ['exact']
        }

    def noop(self, qs, name, value):
        return qs

    def filter_by_figures(self, qs, _, value):
        return FigureFilterHelper.filter_using_figure_filters(qs, value, self.request)

    def filter_countries(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(countries__in=value).distinct()

    def filter_disaster_sub_types(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(~Q(event_type=Crisis.CRISIS_TYPE.DISASTER.value) | Q(disaster_sub_type__in=value)).distinct()

    def filter_violence_types(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(~Q(event_type=Crisis.CRISIS_TYPE.CONFLICT.value) | Q(violence__in=value)).distinct()

    def filter_violence_sub_types(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(~Q(event_type=Crisis.CRISIS_TYPE.CONFLICT.value) | Q(violence_sub_type__in=value)).distinct()

    def filter_crises(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(crisis__in=value).distinct()

    def filter_event_types(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # internal filtering
                return qs.filter(event_type__in=value).distinct()
            return qs.filter(event_type__in=[
                Crisis.CRISIS_TYPE.get(item).value for item in value
            ]).distinct()
        return qs

    def filter_review_status(self, qs, name, value):
        # Filter out *_BUT_CHANGED values from user input
        value = [
            v
            for v in value or []
            if v not in [
                Event.EVENT_REVIEW_STATUS.APPROVED_BUT_CHANGED.value,
                Event.EVENT_REVIEW_STATUS.APPROVED_BUT_CHANGED.name,
                Event.EVENT_REVIEW_STATUS.SIGNED_OFF_BUT_CHANGED.value,
                Event.EVENT_REVIEW_STATUS.SIGNED_OFF_BUT_CHANGED.name,
            ]
        ]
        if value:
            if (
                Event.EVENT_REVIEW_STATUS.REVIEW_IN_PROGRESS.value in value or
                Event.EVENT_REVIEW_STATUS.REVIEW_IN_PROGRESS.name in value
            ):
                # Add *_BUT_CHANGED values if REVIEW_IN_PROGRESS is provided by user
                value = [
                    *value,
                    Event.EVENT_REVIEW_STATUS.APPROVED_BUT_CHANGED.value,
                    Event.EVENT_REVIEW_STATUS.SIGNED_OFF_BUT_CHANGED.value,
                ]
            if isinstance(value[0], int):
                return qs.filter(review_status__in=value).distinct()
            return qs.filter(review_status__in=[
                # NOTE: item is string. eg: 'REVIEW_IN_PROGRESS'
                Event.EVENT_REVIEW_STATUS.get(item).value
                for item in value
            ]).distinct()
        return qs

    def filter_name(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(Q(name__unaccent__icontains=value) | Q(event_code__event_code__iexact=value)).distinct()

    def filter_osv_sub_types(self, qs, name, value):
        if value:
            return qs.filter(~Q(violence__name=OSV) | Q(osv_sub_type__in=value)).distinct()
        return qs

    def filter_qa_rule(self, qs, name, value):
        if QA_RULE_TYPE.HAS_NO_RECOMMENDED_FIGURES.name == value:
            return qs.annotate(
                figure_count=Count(
                    'figures', filter=Q(
                        figures__category__in=[
                            Figure.FIGURE_CATEGORY_TYPES.IDPS,
                            Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                        ],
                        ignore_qa=False,
                        figures__role=Figure.ROLE.RECOMMENDED,
                        figures__geo_locations__isnull=False,
                    )
                )
            ).filter(
                figure_count=0
            )
        elif QA_RULE_TYPE.HAS_MULTIPLE_RECOMMENDED_FIGURES.name == value:
            events_id_qs = Figure.objects.filter(
                category__in=[
                    Figure.FIGURE_CATEGORY_TYPES.IDPS,
                    Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                ],
                event__ignore_qa=False,
                role=Figure.ROLE.RECOMMENDED,
                geo_locations__isnull=False,
            ).annotate(
                locations=models.Subquery(
                    Figure.geo_locations.through.objects.filter(
                        figure=models.OuterRef('pk')
                    ).order_by().values('figure').annotate(
                        locations=ArrayAgg(
                            'osmname__name', distinct=True, ordering='osmname__name'
                        ),
                    ).values('locations')[:1],
                    output_field=models.CharField(),
                ),
            ).order_by().values('event', 'category', 'locations').annotate(
                count=Count('id', distinct=True),
            )
            return qs.filter(
                id__in=events_id_qs.filter(count__gt=1).values('event').distinct()
            )
        return qs

    def filter_context_of_violences(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(context_of_violence__in=value).distinct()

    def filter_assigners(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(assigner__in=value)

    def filter_assignees(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(assignee__in=value)

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
            **Event._total_figure_disaggregation_subquery(
                figures=figure_qs,
                reference_date=reference_date,
            ),
            **Event.annotate_review_figures_count(),
            entry_count=models.Subquery(
                Figure.objects.filter(
                    event=models.OuterRef('pk')
                ).order_by().values('event').annotate(
                    count=models.Count('entry', distinct=True)
                ).values('count')[:1],
                output_field=models.IntegerField()
            )
        ).prefetch_related("figures", 'context_of_violence')


class ActorFilter(django_filters.FilterSet):
    """
    ActorFilter is a class that represents a filter for the Actor model.

    This class inherits from django_filters.FilterSet and is used to filter Actor objects based on certain criteria.

    Attributes:
        model (Model): The model this filter is associated with, in this case, Actor.

    Example usage:
        filter = ActorFilter(query_params, queryset=Actor.objects.all())

    Methods:
        Meta: A nested class that defines metadata for the filter.

        Available Fields:
            - name: Filters Actor objects by name using the 'unaccent__icontains' lookup.

    """
    class Meta:
        model = Actor
        fields = {
            'name': ['unaccent__icontains']
        }


class DisasterSubTypeFilter(django_filters.FilterSet):
    """
    class DisasterSubTypeFilter(django_filters.FilterSet):
        A filter class used to filter DisasterSubType objects based on their name.

        Attributes:
            model (DisasterSubType): The model class to be filtered.
            fields (dict): The fields to be used in the filter.

        Usage:
            filter_class = DisasterSubTypeFilter
            queryset = DisasterSubType.objects.all()
            filter = filter_class(data=request.GET, queryset=queryset)
            filtered_queryset = filter.qs

        Example:
            filter = DisasterSubTypeFilter(data={'name': 'earthquake'}, queryset=queryset)
            filtered_queryset = filter.qs
    """
    class Meta:
        model = DisasterSubType
        fields = {
            'name': ['unaccent__icontains']
        }


class DisasterTypeFilter(django_filters.FilterSet):
    """
    Class: DisasterTypeFilter

    This class inherits from the django_filters.FilterSet class and is used to filter instances of the DisasterType model based on a specific criteria.

    Parameters:
    - model: The model class that the filter is associated with. In this case, it is the DisasterType model.
    - fields: A dictionary that specifies the fields that will be used for filtering. In this case, the 'name' field is used with the 'unaccent__icontains' lookup to perform a case-insensitive containment match on the unaccented name.

    Example usage:

        filter = DisasterTypeFilter(data={'name': 'earthquake'})
        queryset = filter.qs
        # queryset now contains instances of the DisasterType model that have a name containing the word 'earthquake' (case-insensitive)

    Note:
    This class requires the django_filters package to be installed. You can install it using pip:

        pip install django_filters

    """
    class Meta:
        model = DisasterType
        fields = {
            'name': ['unaccent__icontains']
        }


class DisasterCategoryFilter(django_filters.FilterSet):
    """
    A class that defines a filter for the DisasterCategory model based on the name attribute

    Attributes:
        model (DisasterCategory): The model class to be filtered
        fields (dict): A dictionary specifying the filter fields

    Example Usage:
        # Create an instance of DisasterCategoryFilter
        category_filter = DisasterCategoryFilter(data=request.GET, queryset=DisasterCategory.objects.all())

        # Apply the filter
        filtered_categories = category_filter.qs

    """
    class Meta:
        model = DisasterCategory
        fields = {
            'name': ['unaccent__icontains']
        }


class DisasterSubCategoryFilter(django_filters.FilterSet):
    """

    DisasterSubCategoryFilter

    A class that defines filtering options for the DisasterSubCategory model.

    Usage:
        filter = DisasterSubCategoryFilter(queryset)

    Attributes:
        model (Model): The model on which the filtering options are defined.

    Methods:
        N/A

    """
    class Meta:
        model = DisasterSubCategory
        fields = {
            'name': ['unaccent__icontains']
        }


class OsvSubTypeFilter(django_filters.FilterSet):
    """
    The OsvSubTypeFilter class is a FilterSet subclass for filtering OsvSubType instances based on their name attribute. It is designed to be used with Django's filtering functionality.

    Attributes:
        model (Model): The model class to be filtered.

    Fields:
        name (list): Specifies the filter condition for the 'name' attribute. The 'icontains' lookup type is used to perform a case-insensitive containment match.

    Example usage:
        filter_set = OsvSubTypeFilter(data=request.GET, queryset=OsvSubType.objects.all())
        filtered_queryset = filter_set.qs

        This code creates an instance of OsvSubTypeFilter with request.GET as the filter data and all OsvSubType instances as the initial queryset. It then applies the filtering based on the provided data and returns the filtered queryset.

    """
    class Meta:
        model = OsvSubType
        fields = {
            'name': ['icontains']
        }


class OtherSubTypeFilter(django_filters.FilterSet):
    """
    Filter class for OtherSubType model.

    This class is a subclass of `django_filters.FilterSet` and provides filtering options for the `OtherSubType` model based on the `name` field.

    Attributes:
        model (Model): The model class for which the filter is defined.

    Fields:
        - name (list[str]): Filter options for the `name` field. The filter is case-insensitive and performs a partial match.

    Example usage:
        filter_class = OtherSubTypeFilter
        queryset = OtherSubType.objects.all()
        filtered_queryset = filter_class(data=request.GET, queryset=queryset).qs
    """
    class Meta:
        model = OtherSubType
        fields = {
            'name': ['icontains']
        }


class ContextOfViolenceFilter(django_filters.FilterSet):
    """Filterset for filtering ContextOfViolence objects based on name.

    Class:
    ContextOfViolenceFilter

    Attributes:
    - model: The model class used for filtering (ContextOfViolence).
    - fields: A dictionary defining the allowed filters and their lookup types for name field.

    Methods:
    None

    """
    class Meta:
        model = ContextOfViolence
        fields = {
            'name': ['icontains']
        }


class ViolenceFilter(django_filters.FilterSet):
    """
    Class: ViolenceFilter

    This class is a filter for the Violence model.

    Attributes:
        model (class): The model that this filter is associated with.
        fields (dict): A dictionary that maps field names to a list of filter
                       lookups. The field names should be the names of the
                       model's fields that need to be filtered.

    """
    class Meta:
        model = Violence
        fields = {
            'id': ['iexact'],
        }


class ViolenceSubTypeFilter(django_filters.FilterSet):
    """
    This class is a FilterSet for the ViolenceSubType model. It is used to filter querysets based on the 'id' field of the ViolenceSubType model.

    Attributes:
        model (class): The model that the FilterSet is being applied to.

    Example usage:
        filter_set = ViolenceSubTypeFilter(data=request.GET, queryset=queryset)
        filtered_queryset = filter_set.qs
    """
    class Meta:
        model = ViolenceSubType
        fields = {
            'id': ['iexact'],
        }


EventFilterDataType, EventFilterDataInputType = generate_type_for_filter_set(
    EventFilter,
    'event.schema.event_list',
    'EventFilterDataType',
    'EventFilterDataInputType',
    custom_new_fields_map={
        'filter_figures': graphene.Field(FigureExtractionFilterDataType),
        'aggregate_figures': graphene.Field(FigureAggregateFilterDataType),
    },
)

ActorFilterDataType, ActorFilterDataInputType = generate_type_for_filter_set(
    ActorFilter,
    'event.schema.actor_list',
    'ActorFilterDataType',
    'ActorFilterDataInputType',
)

ContextOfViolenceFilterDataType, ContextOfViolenceFilterDataInputType = generate_type_for_filter_set(
    ContextOfViolenceFilter,
    'event.schema.context_of_violence_list',
    'ContextOfViolenceFilterDataType',
    'ContextOfViolenceFilterDataInputType',
)

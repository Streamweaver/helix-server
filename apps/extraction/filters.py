from django_filters import rest_framework as df
from django.db.models import Q
from django.contrib.postgres.aggregates.general import StringAgg
from apps.crisis.models import Crisis
from apps.country.models import Country
from apps.extraction.models import ExtractionQuery
from apps.entry.models import (
    Entry,
    Figure,
)
from apps.report.models import Report
from utils.filters import (
    StringListFilter,
    IDListFilter,
    generate_type_for_filter_set,
    IDFilter,
)
from apps.entry.filters import FigureTagFilter
from apps.event.constants import OSV
from apps.common.enums import GENDER_TYPE
from apps.common.utils import EXTERNAL_ARRAY_SEPARATOR
from apps.entry.constants import STOCK, FLOW

MALE = GENDER_TYPE.MALE.name
FEMALE = GENDER_TYPE.FEMALE.name


class EntryExtractionFilterSet(df.FilterSet):
    """
    EntryExtractionFilterSet is a subclass of df.FilterSet.

    Attributes:
        filter_figure_events: An IDListFilter object used for filtering entries based on event IDs.
        filter_figure_crises: An IDListFilter object used for filtering entries based on crisis IDs.
        filter_figure_sources: An IDListFilter object used for filtering entries based on source IDs.
        filter_entry_publishers: An IDListFilter object used for filtering entries based on publisher IDs.
        filter_entry_article_title: A CharFilter object used for filtering entries based on article titles.
        filter_figure_created_by: An IDListFilter object used for filtering entries based on creator IDs.
        filter_figure_regions: An IDListFilter object used for filtering entries based on region IDs.
        filter_figure_geographical_groups: An IDListFilter object used for filtering entries based on geographical group
        IDs.
        filter_figure_countries: An IDListFilter object used for filtering entries based on country IDs.
        filter_figure_category_types: A StringListFilter object used for filtering entries based on category types.
        filter_figure_categories: A StringListFilter object used for filtering entries based on category names.
        filter_figure_start_after: A DateFilter object used for filtering entries based on start date.
        filter_figure_end_before: A DateFilter object used for filtering entries based on end date.
        filter_figure_roles: A StringListFilter object used for filtering entries based on figure roles.
        filter_figure_tags: An IDListFilter object used for filtering entries based on tag IDs.
        filter_figure_terms: An IDListFilter object used for filtering entries based"""
    # NOTE: these filter names exactly match the extraction query model field names
    filter_figure_events = IDListFilter(method='filter_figure_events_')

    filter_figure_crises = IDListFilter(method='filter_crises')

    filter_figure_sources = IDListFilter(method='filter_sources')
    filter_entry_publishers = IDListFilter(method='filter_publishers')
    filter_entry_article_title = df.CharFilter(field_name='article_title', lookup_expr='unaccent__icontains')
    filter_figure_created_by = IDListFilter(method='filter_created_by')

    filter_figure_regions = IDListFilter(method='filter_regions')
    filter_figure_geographical_groups = IDListFilter(method='filter_geographical_groups')
    filter_figure_countries = IDListFilter(method='filter_countries')
    filter_figure_category_types = StringListFilter(method='filter_filter_figure_category_types')
    filter_figure_categories = StringListFilter(method='filter_filter_figure_categories')
    filter_figure_start_after = df.DateFilter(method='filter_time_frame_after')
    filter_figure_end_before = df.DateFilter(method='filter_time_frame_before')
    filter_figure_roles = StringListFilter(method='filter_filter_figure_roles')
    filter_figure_tags = IDListFilter(method='filter_tags')
    filter_figure_terms = IDListFilter(method='filter_by_figure_terms')
    filter_figure_crisis_types = StringListFilter(method='filter_crisis_types')
    filter_figure_disaster_categories = IDListFilter(method='filter_filter_figure_disaster_categories')
    filter_figure_disaster_sub_categories = IDListFilter(method='filter_filter_figure_disaster_sub_categories')
    filter_figure_disaster_sub_types = IDListFilter(method='filter_filter_figure_disaster_sub_types')
    filter_figure_disaster_types = IDListFilter(method='filter_filter_figure_disaster_types')
    filter_figure_violence_sub_types = IDListFilter(method='filter_filter_figure_violence_sub_types')
    filter_figure_violence_types = IDListFilter(method='filter_filter_figure_violence_types')
    filter_figure_osv_sub_types = IDListFilter(method='filter_filter_figure_osv_sub_types')
    filter_figure_review_status = StringListFilter(method='filter_filter_figure_review_status')
    filter_figure_has_disaggregated_data = df.BooleanFilter(method='filter_has_disaggregated_data')
    filter_figure_approved_by = IDListFilter(method='filter_filter_figure_approved_by')
    filter_figure_has_excerpt_idu = df.BooleanFilter(method='filter_filter_figure_has_excerpt_idu')
    filter_figure_has_housing_destruction = df.BooleanFilter(method='filter_filter_figure_has_housing_destruction')
    # used in report entry table
    report_id = IDFilter(method='filter_report')
    filter_figure_context_of_violence = IDListFilter(method='filter_filter_figure_context_of_violence')
    filter_figure_is_to_be_reviewed = df.BooleanFilter(method='filter_filter_figure_is_to_be_reviewed')

    class Meta:
        model = Entry
        fields = {
        }

    def filter_created_by(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(figures__created_by__in=value)

    def filter_report(self, qs, name, value):
        if not value:
            return qs
        # Can't we just use: ReportFigureExtractionFilterSet(data=figure_filters, request=request).qs
        return qs.filter(
            id__in=Report.objects.get(id=value).report_figures.values('entry')
        )

    def filter_geographical_groups(self, qs, name, value):
        if value:
            qs = qs.filter(
                id__in=Figure.objects.filter(
                    country__geographical_group__in=value
                ).values('entry')
            )
        return qs

    def filter_regions(self, qs, name, value):
        if value:
            qs = qs.filter(
                id__in=Figure.objects.filter(
                    country__region__in=value
                ).values('entry')
            )
        return qs

    def filter_countries(self, qs, name, value):
        if value:
            return qs.filter(
                id__in=Figure.objects.filter(
                    country__in=value
                ).values('entry')
            )
        return qs

    def filter_figure_events_(self, qs, name, value):
        if value:
            return qs.filter(figures__event__in=value).distinct()
        return qs

    def filter_crises(self, qs, name, value):
        if value:
            return qs.filter(figures__event__crisis__in=value).distinct()
        return qs

    def filter_sources(self, qs, name, value):
        if value:
            return qs.filter(figures__sources__in=value).distinct()
        return qs

    def filter_publishers(self, qs, name, value):
        if value:
            return qs.filter(publishers__in=value).distinct()
        return qs

    def filter_by_figure_terms(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # coming from saved query
                return qs.filter(figures__in=Figure.objects.filter(term__in=value))

            return qs.filter(figures__term__in=[
                Figure.FIGURE_TERMS.get(item).value for item in value
            ]).distinct()
        return qs

    def filter_filter_figure_category_types(self, qs, name, value):
        if not value:
            return qs
        # NOTE: category type is saved as 'Stock' and 'Flow' on database
        # so, using capitalize on enum values 'STOCK' and 'FLOW'
        category_enums_to_filter = []
        for category_type in value:
            if category_type == STOCK:
                category_enums_to_filter += Figure.stock_list()
            if category_type == FLOW:
                category_enums_to_filter += Figure.flow_list()
        return qs.filter(figures__category__in=category_enums_to_filter).distinct()

    def filter_filter_figure_categories(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # coming from saved query
                return qs.filter(figures__category__in=value)
            return qs.filter(figures__category__in=[
                Figure.FIGURE_CATEGORY_TYPES.get(item).value for item in value
            ])
        return qs

    def filter_time_frame_after(self, qs, name, value):
        if value:
            return qs\
                .filter(
                    id__in=Figure.objects
                    .exclude(start_date__isnull=True)
                    .filter(start_date__gte=value)
                    .values('entry')
                )
        return qs

    def filter_time_frame_before(self, qs, name, value):
        if value:
            return qs\
                .filter(
                    id__in=Figure.objects
                    .exclude(end_date__isnull=True)
                    .filter(end_date__lt=value)
                    .values('entry')
                )
        return qs

    def filter_filter_figure_roles(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # coming from saved query
                return qs.filter(figures__in=Figure.objects.filter(role__in=value))
            return qs.filter(
                figures__in=Figure.objects.filter(role__in=[
                    Figure.ROLE.get(item).value for item in value
                ]))
        return qs

    def filter_tags(self, qs, name, value):
        if value:
            return qs.filter(figures__tags__in=value).distinct()
        return qs

    def filter_crisis_types(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # coming from saved query
                return qs.filter(figures__figure_cause__in=value).distinct()
            # coming from client side
            return qs.filter(figures__figure_cause__in=[
                Crisis.CRISIS_TYPE.get(item).value for item in value
            ])
        return qs

    def filter_filter_figure_disaster_categories(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figures__figure_cause=Crisis.CRISIS_TYPE.DISASTER.value
                ) | Q(figures__disaster_category__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_disaster_sub_categories(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figures__figure_cause=Crisis.CRISIS_TYPE.DISASTER.value
                ) | Q(figures__disaster_sub_category__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_disaster_sub_types(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figures__figure_cause=Crisis.CRISIS_TYPE.DISASTER.value
                ) | Q(figures__disaster_sub_type__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_disaster_types(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figures__figure_cause=Crisis.CRISIS_TYPE.DISASTER.value
                ) | Q(figures__disaster_type__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_violence_sub_types(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figures__figure_cause=Crisis.CRISIS_TYPE.CONFLICT.value
                ) | Q(figures__violence_sub_type__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_violence_types(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figures__figure_cause=Crisis.CRISIS_TYPE.CONFLICT.value
                ) | Q(figures__violence_type__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_osv_sub_types(self, qs, name, value):
        if value:
            return qs.filter(~Q(figures__event__violence__name=OSV) | Q(figures__osv_sub_type__in=value)).distinct()
        return qs

    def filter_has_disaggregated_data(self, qs, name, value):
        if value is True:
            return qs.filter(figures__is_disaggregated=True)
        if value is False:
            return qs.filter(figures__is_disaggregated=False)
        return qs

    def filter_filter_figure_context_of_violence(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(figures__context_of_violence__in=value).distinct()

    def filter_filter_figure_review_status(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                return qs.filter(figures__review_status__in=value)
            return qs.filter(
                figures__review_status__in=[Figure.FIGURE_REVIEW_STATUS.get(item).value for item in value]
            )
        return qs

    def filter_filter_figure_approved_by(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(figures__approved_by__in=value)

    def filter_filter_figure_has_excerpt_idu(self, qs, name, value):
        if value is None:
            return qs
        return qs.filter(figures__include_idu=value)

    def filter_filter_figure_has_housing_destruction(self, qs, name, value):
        if value is None:
            return qs
        return qs.filter(figures__is_housing_destruction=value)

    def filter_filter_figure_is_to_be_reviewed(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(
            Q(figures__role=Figure.ROLE.RECOMMENDED) |
            Q(figures__event__include_triangulation_in_qa=True)
        )

    @property
    def qs(self):
        return super().qs.distinct()


class BaseFigureExtractionFilterSet(df.FilterSet):
    """

    BaseFigureExtractionFilterSet

    This class extends the df.FilterSet class and provides a set of filters for extracting figures. These filters are
    used to query the Figure model.

    Attributes:
    filter_figure_regions: Filter for filtering figures based on geographical regions (IDListFilter)
    filter_figure_geographical_groups: Filter for filtering figures based on geographical groups (IDListFilter)
    filter_figure_countries: Filter for filtering figures based on countries (IDListFilter)
    filter_figure_events: Filter for filtering figures based on events (IDListFilter)
    filter_figure_crises: Filter for filtering figures based on crises (IDListFilter)
    filter_figure_sources: Filter for filtering figures based on sources (IDListFilter)
    filter_entry_publishers: Filter for filtering figures based on publishers (IDListFilter)
    filter_figure_category_types: Filter for filtering figures based on category types (StringListFilter)
    filter_figure_categories: Filter for filtering figures based on categories (StringListFilter)
    filter_figure_start_after: Filter for filtering figures based on start date (DateFilter)
    filter_figure_end_before: Filter for filtering figures based on end date (DateFilter)
    filter_figure_roles: Filter for filtering figures based on roles (StringListFilter)
    filter_entry_article_title: Filter for filtering figures based on article title (CharFilter)
    filter_figure_tags: Filter for filtering figures based on tags (IDListFilter)
    filter_figure_crisis_types: Filter for filtering figures based on crisis types (StringListFilter)
    filter_figure_created_by: Filter for filtering figures based on created by (IDListFilter)
    filter_figure_terms: Filter for filtering figures based on terms (IDListFilter)
    filter_figure_disaster_categories: Filter for filtering figures based on"""
    # NOTE: these filter names exactly match the extraction query model field names
    filter_figure_regions = IDListFilter(method='filter_regions')
    filter_figure_geographical_groups = IDListFilter(method='filter_geographical_groups')
    filter_figure_countries = IDListFilter(method='filter_countries')
    filter_figure_events = IDListFilter(method='filter_figure_events_')
    filter_figure_crises = IDListFilter(method='filter_crises')
    filter_figure_sources = IDListFilter(method='filter_sources')
    filter_entry_publishers = IDListFilter(method='filter_publishers')
    filter_figure_category_types = StringListFilter(method='filter_filter_figure_category_types')
    filter_figure_categories = StringListFilter(method='filter_filter_figure_categories')
    filter_figure_start_after = df.DateFilter(method='filter_time_frame_after')
    filter_figure_end_before = df.DateFilter(method='filter_time_frame_before')
    filter_figure_roles = StringListFilter(method='filter_filter_figure_roles')
    filter_entry_article_title = df.CharFilter(field_name='entry__article_title', lookup_expr='unaccent__icontains')
    filter_figure_tags = IDListFilter(method='filter_tags')
    filter_figure_crisis_types = StringListFilter(method='filter_crisis_types')
    filter_figure_created_by = IDListFilter(method='filter_filter_figure_created_by')
    filter_figure_terms = IDListFilter(method='filter_by_figure_terms')
    filter_figure_disaster_categories = IDListFilter(method='filter_filter_figure_disaster_categories')
    filter_figure_disaster_sub_categories = IDListFilter(method='filter_filter_figure_disaster_sub_categories')
    filter_figure_disaster_sub_types = IDListFilter(method='filter_filter_figure_disaster_sub_types')
    filter_figure_disaster_types = IDListFilter(method='filter_filter_figure_disaster_types')
    filter_figure_violence_sub_types = IDListFilter(method='filter_filter_figure_violence_sub_types')
    filter_figure_violence_types = IDListFilter(method='filter_filter_figure_violence_types')
    filter_figure_osv_sub_types = IDListFilter(method='filter_filter_figure_osv_sub_types')
    filter_figure_has_disaggregated_data = df.BooleanFilter(method='filter_has_disaggregated_data')
    # used in report entry table
    report_id = IDFilter(method='filter_report')
    filter_figure_context_of_violence = IDListFilter(method='filter_filter_figure_context_of_violence')
    filter_figure_review_status = StringListFilter(method='filter_filter_figure_review_status')
    filter_figure_approved_by = IDListFilter(method='filter_filter_figure_approved_by')
    filter_figure_is_to_be_reviewed = df.BooleanFilter(method='filter_filter_figure_is_to_be_reviewed')
    filter_figure_has_excerpt_idu = df.BooleanFilter(method='filter_filter_figure_has_excerpt_idu')
    filter_figure_has_housing_destruction = df.BooleanFilter(method='filter_filter_figure_has_housing_destruction')
    filter_figure_entry = df.CharFilter(field_name='entry', lookup_expr='exact')

    class Meta:
        model = Figure
        fields = []

    def filter_filter_figure_created_by(self, qs, name, value):
        if value:
            return qs.filter(created_by__in=value)
        return qs

    def filter_time_frame_after(self, qs, name, value):
        if value:
            return qs.exclude(start_date__isnull=True)\
                .filter(start_date__gte=value).distinct()
        return qs

    def filter_time_frame_before(self, qs, name, value):
        if value:
            return qs.exclude(end_date__isnull=True).\
                filter(end_date__lt=value).distinct()
        return qs

    def filter_report(self, qs, name, value):
        if not value:
            return qs

        report = Report.objects.get(id=value)
        return ReportFigureExtractionFilterSet(
            queryset=qs,
            data=report.get_filter_kwargs,
        ).qs

    def filter_geographical_groups(self, qs, name, value):
        if value:
            qs = qs.filter(
                country__in=Country.objects.filter(
                    geographical_group__in=value
                )
            )
        return qs

    def filter_regions(self, qs, name, value):
        if value:
            qs = qs.filter(
                country__in=Country.objects.filter(
                    region__in=value
                )
            )
        return qs

    def filter_countries(self, qs, name, value):
        if value:
            return qs.filter(country__in=value).distinct()
        return qs

    def filter_figure_events_(self, qs, name, value):
        if value:
            return qs.filter(event__in=value).distinct()
        return qs

    def filter_crises(self, qs, name, value):
        if value:
            return qs.filter(event__crisis__in=value).distinct()
        return qs

    def filter_sources(self, qs, name, value):
        if value:
            return qs.filter(sources__in=value).distinct()
        return qs

    def filter_publishers(self, qs, name, value):
        if value:
            return qs.filter(entry__publishers__in=value).distinct()
        return qs

    def filter_filter_figure_category_types(self, qs, name, value):
        if not value:
            return qs
        # NOTE: category type is saved as 'Stock' and 'Flow' on database
        # so, using capitalize on enum values 'STOCK' and 'FLOW'
        category_enums_to_filter = []
        for category_type in value:
            if category_type == STOCK:
                category_enums_to_filter = category_enums_to_filter + Figure.stock_list()
            if category_type == FLOW:
                category_enums_to_filter = category_enums_to_filter + Figure.flow_list()
        return qs.filter(category__in=category_enums_to_filter).distinct()

    def filter_filter_figure_categories(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # coming from saved query
                return qs.filter(category__in=value)
            return qs.filter(category__in=[
                Figure.FIGURE_CATEGORY_TYPES.get(item).value for item in value
            ])
        return qs

    def filter_filter_figure_roles(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # coming from saved query
                return qs.filter(role__in=value)
            else:
                # coming from client side
                return qs.filter(
                    role__in=[Figure.ROLE.get(item).value for item in value]
                )
        return qs

    def filter_tags(self, qs, name, value):
        if value:
            return qs.filter(tags__in=value).distinct()
        return qs

    def filter_crisis_types(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # coming from saved query
                return qs.filter(figure_cause__in=value).distinct()
            else:
                # coming from client side
                return qs.filter(figure_cause__in=[
                    Crisis.CRISIS_TYPE.get(item).value for item in value
                ])
        return qs

    def filter_filter_figure_has_excerpt_idu(self, qs, name, value):
        if value is None:
            return qs
        return qs.filter(include_idu=value)

    def filter_filter_figure_has_housing_destruction(self, qs, name, value):
        if value is None:
            return qs
        return qs.filter(is_housing_destruction=value)

    def filter_by_figure_terms(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # coming from saved query
                return qs.filter(term__in=value)
            return qs.filter(term__in=[
                Figure.FIGURE_TERMS.get(item).value for item in value
            ])
        return qs

    def filter_filter_figure_disaster_categories(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figure_cause=Crisis.CRISIS_TYPE.DISASTER.value
                ) | Q(disaster_category__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_disaster_sub_categories(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figure_cause=Crisis.CRISIS_TYPE.DISASTER.value
                ) | Q(disaster_sub_category__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_disaster_sub_types(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figure_cause=Crisis.CRISIS_TYPE.DISASTER.value
                ) | Q(disaster_sub_type__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_disaster_types(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figure_cause=Crisis.CRISIS_TYPE.DISASTER.value
                ) | Q(disaster_type__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_violence_sub_types(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figure_cause=Crisis.CRISIS_TYPE.CONFLICT.value
                ) | Q(violence_sub_type__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_violence_types(self, qs, name, value):
        if value:
            return qs.filter(
                ~Q(
                    figure_cause=Crisis.CRISIS_TYPE.CONFLICT.value
                ) | Q(violence_type__in=value)
            ).distinct()
        return qs

    def filter_filter_figure_osv_sub_types(self, qs, name, value):
        if value:
            return qs.filter(~Q(event__violence__name=OSV) | Q(osv_sub_type__in=value)).distinct()
        return qs

    def filter_has_disaggregated_data(self, qs, name, value):
        if value is True:
            return qs.filter(is_disaggregated=True)
        if value is False:
            return qs.filter(is_disaggregated=False)
        return qs

    def filter_filter_figure_context_of_violence(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(context_of_violence__in=value).distinct()

    def filter_filter_figure_review_status(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                return qs.filter(review_status__in=value)
            return qs.filter(
                review_status__in=[Figure.FIGURE_REVIEW_STATUS.get(item).value for item in value]
            )
        return qs

    def filter_filter_figure_approved_by(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(approved_by__in=value)

    def filter_filter_figure_is_to_be_reviewed(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(
            Q(role=Figure.ROLE.RECOMMENDED) |
            Q(event__include_triangulation_in_qa=True)
        )

    @property
    def qs(self):
        # FIXME: using this prefetch_related results in calling count after a
        # subquery. This has a severe performance penalty
        return super().qs.distinct()


class FigureExtractionFilterSet(BaseFigureExtractionFilterSet):
    """

    Class: FigureExtractionFilterSet

    This class is a subclass of BaseFigureExtractionFilterSet. It represents a filter set for extracting figures.

    Attributes:
    - filter_figure_start_after (df.DateFilter): A DateFilter object representing the filter for figures starting after
    a specific date.
    - filter_figure_end_before (df.DateFilter): A DateFilter object representing the filter for figures ending before a
    specific date.

    Methods:
    - noop(self, qs, *args): This method takes a queryset (qs) and additional arguments (*args) and returns the same
    queryset without any modifications.

    Properties:
    - qs: This property returns the combined queryset of filtered figures for both stock and flow. It first calls the qs
    property of the superclass, then annotates the queryset with stock and flow dates and geolocations. It also
    annotates the queryset with sources reliability. Finally, it applies the filters for figure start date and figure
    end date to the queryset using the Figure.filtered_nd_figures_for_listing and
    Figure.filtered_idp_figures_for_listing methods. The result is the combined queryset of filtered figures for both
    stock and flow.

    """
    filter_figure_start_after = df.DateFilter(method='noop')
    filter_figure_end_before = df.DateFilter(method='noop')

    def noop(self, qs, *args):
        return qs

    @property
    def qs(self):
        queryset = super().qs.annotate(
            **Figure.annotate_stock_and_flow_dates(),
            geolocations=StringAgg('geo_locations__display_name', EXTERNAL_ARRAY_SEPARATOR),
            **Figure.annotate_sources_reliability(),
        )
        start_date = self.data.get('filter_figure_start_after')
        end_date = self.data.get('filter_figure_end_before')

        flow_qs = Figure.filtered_nd_figures_for_listing(
            queryset, start_date, end_date
        )
        stock_qs = Figure.filtered_idp_figures_for_listing(
            queryset, start_date, end_date
        )
        return flow_qs | stock_qs


class ReportFigureExtractionFilterSet(BaseFigureExtractionFilterSet):
    """
    Class: ReportFigureExtractionFilterSet

    This class is a subclass of BaseFigureExtractionFilterSet and is used for filtering figure extraction reports.

    Attributes:
    - filter_figure_start_after: A DateFilter object used for filtering the start date of the figures in the report.
    - filter_figure_end_before: A DateFilter object used for filtering the end date of the figures in the report.

    Methods:
    - noop(qs, *args): A method that returns the passed queryset as is without any modifications.

    Properties:
    - qs: A property that returns the filtered queryset based on the start and end dates provided.

    Example Usage:
        filter_set = ReportFigureExtractionFilterSet()
        filter_set.filter_figure_start_after = DateFilter()
        filter_set.filter_figure_end_before = DateFilter()
        figures = filter_set.qs
    """
    filter_figure_start_after = df.DateFilter(method='noop')
    filter_figure_end_before = df.DateFilter(method='noop')

    def noop(self, qs, *args):
        return qs

    @property
    def qs(self):
        queryset = super().qs
        start_date = self.data.get('filter_figure_start_after')
        end_date = self.data.get('filter_figure_end_before')

        flow_qs = Figure.filtered_nd_figures_for_listing(
            queryset, start_date, end_date
        )
        stock_qs = Figure.filtered_idp_figures_for_listing(
            queryset, start_date, end_date
        )
        return flow_qs | stock_qs


class FigureExtractionBulkOperationFilterSet(ReportFigureExtractionFilterSet):
    """

    Class: FigureExtractionBulkOperationFilterSet

    This class is a filter set that extends the ReportFigureExtractionFilterSet class.
    It provides filters for the figure IDs to include or exclude from the queryset.

    Attributes:
    - filter_figure_ids: An IDListFilter object used for filtering the queryset based on included figure IDs.
    - filter_figure_exclude_ids: An IDListFilter object used for filtering the queryset based on excluded figure IDs.

    Methods:
    - filter_ids(qs, _, value): This method applies the filter to include figures with specified IDs in the queryset.
      Parameters:
        - qs (QuerySet): The original queryset to be filtered.
        - _ (str): Unused parameter (django-filter convention).
        - value (list): The list of figure IDs to include.
      Returns:
        - QuerySet: The filtered queryset with only the figures whose IDs are included in the value list.

    - filter_exclude_ids(qs, _, value): This method applies the filter to exclude figures with specified IDs from the
    queryset.
      Parameters:
        - qs (QuerySet): The original queryset to be filtered.
        - _ (str): Unused parameter (django-filter convention).
        - value (list): The list of figure IDs to exclude.
      Returns:
        - QuerySet: The filtered queryset with all figures except those whose IDs are in the value list.

    Note: This class inherits other attributes and methods from the ReportFigureExtractionFilterSet class.

    """
    filter_figure_ids = IDListFilter(method='filter_ids')
    filter_figure_exclude_ids = IDListFilter(method='filter_exclude_ids')

    def filter_ids(self, qs, _, value):
        if value:
            return qs.filter(id__in=value)
        return qs

    def filter_exclude_ids(self, qs, _, value):
        if value:
            return qs.exclude(id__in=value)
        return qs


class ExtractionQueryFilter(df.FilterSet):
    """
    ExtractionQueryFilter class is a subclass of df.FilterSet.

    This class is used to filter ExtractionQuery objects based on specified fields and values.

    Attributes:
        Meta: A nested class which specifies the model to be filtered (ExtractionQuery)
              and the fields to be used for filtering.

    Methods:
        qs: A property method that returns a filtered queryset based on the specified fields and values.
            The method filters the queryset based on the 'created_by' field if the request user is authenticated,
            otherwise it returns an empty queryset.

    Example usage:
        filter = ExtractionQueryFilter(request=request)  # Create an instance of ExtractionQueryFilter
        queryset = filter.qs  # Apply the filter and get the filtered queryset

    Note: This class requires the django-filter library (df) to be installed.
    """
    class Meta:
        model = ExtractionQuery
        fields = {
            'id': ('exact',),
            'name': ('unaccent__icontains',),
        }

    @property
    def qs(self):
        if self.request.user.is_authenticated:
            return super().qs.filter(created_by=self.request.user)
        return ExtractionQuery.objects.none()


FigureExtractionFilterDataType, FigureExtractionFilterDataInputType = generate_type_for_filter_set(
    FigureExtractionFilterSet,
    'entry.schema.figure_list',
    'FigureExtractionFilterDataType',
    'FigureExtractionFilterDataInputType',
)

EntryExtractionFilterDataType, EntryExtractionFilterDataInputType = generate_type_for_filter_set(
    EntryExtractionFilterSet,
    'entry.schema.entry_list',
    'EntryExtractionFilterDataType',
    'EntryExtractionFilterDataInputType',
)


FigureExtractionBulkOperationFilterDataType, FigureExtractionBulkOperationFilterDataInputType = generate_type_for_filter_set(
    FigureExtractionBulkOperationFilterSet,
    'entry.schema.figure_list',
    'FigureExtractionBulkOperationFilterDataType',
    'FigureExtractionBulkOperationFilterDataInputType',
)


FigureTagFilterDataType, FigureTagFilterDataInputType = generate_type_for_filter_set(
    FigureTagFilter,
    'entry.schema.figure_tag_list',
    'FigureTagFilterDataType',
    'FigureTagFilterDataInputType',
)

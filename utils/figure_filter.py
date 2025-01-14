import typing
import datetime
import graphene
import django_filters
from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from django.db import models
from django.http import HttpRequest

from utils.filters import SimpleInputFilter, generate_type_for_filter_set
from apps.report.models import Report
from apps.country.models import Country
from apps.crisis.models import Crisis
from apps.event.models import Event
from apps.extraction.filters import (
    ReportFigureExtractionFilterSet,
    FigureExtractionFilterDataInputType,
    FigureExtractionFilterDataType,
)


class FigureFilterHelper:
    """

    """
    @staticmethod
    def get_report_id_from_filter_data(aggregate_figures_filter: typing.Optional[dict]) -> typing.Optional[int]:
        return (
            (
                aggregate_figures_filter or {}
            ).get('filter_figures') or {}
        ).get('report_id')

    @staticmethod
    def get_report(report_id: int) -> Report:
        report = Report.objects.filter(id=report_id).first()
        if report is None:
            raise ValidationError(gettext('Provided Report does not exist'))
        return report

    @staticmethod
    def filter_using_figure_filters(qs: models.QuerySet, filters: dict, request: HttpRequest) -> models.QuerySet:
        if not filters:
            return qs
        figure_qs = ReportFigureExtractionFilterSet(data=filters, request=request).qs
        outer_ref_field = None
        if qs.model is Country:
            outer_ref_field = 'country'
        elif qs.model is Event:
            outer_ref_field = 'event'
        elif qs.model is Crisis:
            outer_ref_field = 'event__crisis'

        if outer_ref_field is None:
            raise Exception(f'Unknown model used for `by figure filter`. {qs.model}')

        return qs.filter(
            id__in=figure_qs.values(outer_ref_field)
        )

    @classmethod
    def aggregate_data_generate(
        cls,
        aggregate_figures_filter: typing.Optional[dict],
        request: HttpRequest,
    ) -> typing.Tuple[
        typing.Optional[models.QuerySet],
        typing.Optional[datetime.datetime],
    ]:
        report_id = cls.get_report_id_from_filter_data(aggregate_figures_filter)
        report = report_id and cls.get_report(report_id)

        figure_filters = (aggregate_figures_filter or {}).get('filter_figures') or {}
        figure_qs = None
        reference_date = None
        if report:
            figure_qs = report.report_figures
            reference_date = report.filter_figure_end_before

        if figure_filters:
            figure_qs = ReportFigureExtractionFilterSet(data=figure_filters, request=request).qs

        return figure_qs, reference_date


# -- Filters
class FigureAggregateFilter(django_filters.FilterSet):
    """
    A filter set class for aggregating figures.

    This class extends the `FilterSet` class from the `django_filters` package and
    provides a filter for figures.

    Attributes:
        filter_figures (SimpleInputFilter): A filter for figures based on the
            `FigureExtractionFilterDataInputType` input type.
    """
    filter_figures = SimpleInputFilter(FigureExtractionFilterDataInputType, method='noop')

    def noop(self, qs, *_):
        return qs


class CountryFigureAggregateFilter(FigureAggregateFilter):
    """
    A class that represents a filter for country figure aggregates.

    :class: `CountryFigureAggregateFilter` inherits from `FigureAggregateFilter` class.

    Attributes:
        year (int): The year to filter the figures by.

    """
    year = django_filters.NumberFilter(method='noop')


FigureAggregateFilterDataType, FigureAggregateFilterDataInputType = generate_type_for_filter_set(
    FigureAggregateFilter,
    'entry.schema.figure_list',
    'FigureAggregateFilterDataType',
    'FigureAggregateFilterDataInputType',
    custom_new_fields_map={
        'filter_figures': graphene.Field(FigureExtractionFilterDataType),
    },
)

CountryFigureAggregateFilterDataType, CountryFigureAggregateFilterDataInputType = generate_type_for_filter_set(
    CountryFigureAggregateFilter,
    'entry.schema.figure_list',
    'CountryFigureAggregateFilterDataType',
    'CountryFigureAggregateFilterDataInputType',
    custom_new_fields_map={
        'filter_figures': graphene.Field(FigureExtractionFilterDataType),
    },
)

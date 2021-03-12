from collections import OrderedDict
from functools import cached_property
import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.postgres.aggregates import StringAgg
from django.db.models.functions import Extract
from django.db.models import (
    Sum,
    Count,
    Q,
    F,
    Exists,
    Subquery,
    Min,
    Max,
    OuterRef,
)
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django_enumfield import enum

from apps.contrib.models import MetaInformationArchiveAbstractModel
from apps.country.models import CountryPopulation
from apps.crisis.models import Crisis
from apps.entry.constants import STOCK, FLOW
from apps.entry.models import FigureDisaggregationAbstractModel, Figure
from apps.extraction.models import QueryAbstractModel
from apps.report.utils import excel_column_key
# from utils.permissions import cache_me
from utils.fields import CachedFileField

logger = logging.getLogger(__name__)
User = get_user_model()


class Report(MetaInformationArchiveAbstractModel,
             QueryAbstractModel,
             FigureDisaggregationAbstractModel,
             models.Model):
    class REPORT_TYPE(enum.Enum):
        GROUP = 0
        MASTERFACT = 1

    TOTAL_FIGURE_DISAGGREGATIONS = dict(
        total_stock_conflict=Sum(
            'total_figures',
            filter=Q(category__type=STOCK,
                     role=Figure.ROLE.RECOMMENDED,
                     entry__event__event_type=Crisis.CRISIS_TYPE.CONFLICT)
        ),
        total_flow_conflict=Sum(
            'total_figures',
            filter=Q(category__type=FLOW,
                     role=Figure.ROLE.RECOMMENDED,
                     entry__event__event_type=Crisis.CRISIS_TYPE.CONFLICT)
        ),
        total_stock_disaster=Sum(
            'total_figures',
            filter=Q(category__type=STOCK,
                     role=Figure.ROLE.RECOMMENDED,
                     entry__event__event_type=Crisis.CRISIS_TYPE.DISASTER)
        ),
        total_flow_disaster=Sum(
            'total_figures',
            filter=Q(category__type=FLOW,
                     role=Figure.ROLE.RECOMMENDED,
                     entry__event__event_type=Crisis.CRISIS_TYPE.DISASTER)
        ),
    )

    generated_from = enum.EnumField(REPORT_TYPE,
                                    blank=True, null=True, editable=False)
    # TODO: Remove me after next migration run
    generated = models.BooleanField(verbose_name=_('Generated'), default=True,
                                    editable=False)
    reports = models.ManyToManyField('self', verbose_name=_('Reports (old groups)'),
                                     blank=True, related_name='masterfact_reports',
                                     symmetrical=False)
    # Do not access me, instead access report_figures property
    figures = models.ManyToManyField('entry.Figure',
                                     blank=True)
    # query fields but modified
    filter_figure_start_after = models.DateField(verbose_name=_('From Date'), null=True)
    filter_figure_end_before = models.DateField(verbose_name=_('To Date'), null=True)
    # user entered fields
    analysis = models.TextField(verbose_name=_('Analysis'),
                                blank=True, null=True)
    methodology = models.TextField(verbose_name=_('Methodology'), blank=True, null=True)
    significant_updates = models.TextField(verbose_name=_('Significant Updates'),
                                           blank=True, null=True)
    challenges = models.TextField(verbose_name=_('Challenges'), blank=True, null=True)

    # TODO: remove reported?
    reported = models.PositiveIntegerField(verbose_name=_('Reported Figures'), default=0, editable=False)
    total_figures = models.PositiveIntegerField(verbose_name=_('Total Figures'), default=0,
                                                editable=False)
    # old fields will be migrated into summary
    summary = models.TextField(verbose_name=_('Summary'), blank=True, null=True,
                               help_text=_('It will store master fact information:'
                                           'Comment, Source Excerpt, IDU Excerpt, Breakdown & '
                                           'Reliability, and Caveats'))
    is_signed_off = models.BooleanField(default=False)
    is_signed_off_by = models.ForeignKey(User, verbose_name=_('Last signed off by'),
                                         blank=True, null=True,
                                         related_name='signed_off_reports', on_delete=models.CASCADE)

    @property
    def report_figures(self):
        # TODO: use generated_from after next migration
        if self.generated_from or not self.generated:
            figures_ids = (Report.objects.filter(id=self.id) |
                           Report.objects.get(id=self.id).masterfact_reports.all()).values('figures')
        else:
            figures_ids = self.extract_figures
        return Figure.objects.filter(id__in=figures_ids)

    @property
    # @cache_me(3000)
    def countries_report(self) -> list:
        return self.report_figures.select_related(
            'country'
        ).values('country').order_by().distinct().annotate(
            # id is needed by apollo-client
            id=F('country_id'),
            **self.TOTAL_FIGURE_DISAGGREGATIONS,
        )

    @property
    # @cache_me(3000)
    def events_report(self) -> list:
        return self.report_figures.select_related(
            'entry__event'
        ).prefetch_related(
            'entry__event__countries'
        ).values('entry__event').order_by().distinct().annotate(
            # id is needed by apollo-client
            id=F('entry__event_id'),
            **self.TOTAL_FIGURE_DISAGGREGATIONS,
        )

    @property
    # @cache_me(3000)
    def entries_report(self) -> list:
        from apps.entry.filters import (
            reviewed_subquery,
            signed_off_subquery,
            under_review_subquery,
        )

        return self.report_figures.select_related(
            'entry'
        ).values('entry').order_by().distinct().annotate(
            # id is needed by apollo-client
            id=F('entry_id'),
            is_reviewed=Exists(reviewed_subquery),
            is_under_review=Exists(under_review_subquery),
            is_signed_off=Exists(signed_off_subquery),
            **self.TOTAL_FIGURE_DISAGGREGATIONS,
        )

    @property
    # @cache_me(3000)
    def crises_report(self) -> list:
        return self.report_figures.filter(
            entry__event__crisis__isnull=False
        ).select_related(
            'entry__event__crisis'
        ).values('entry__event__crisis').order_by().distinct().annotate(
            # id is needed by apollo-client
            id=F('entry__event__crisis_id'),
            name=F('entry__event__crisis__name'),
            crisis_type=F('entry__event__crisis__crisis_type'),
            **self.TOTAL_FIGURE_DISAGGREGATIONS,
        )

    @property
    # @cache_me(3000)
    def total_disaggregation(self) -> dict:
        return self.report_figures.annotate(
            **self.TOTAL_FIGURE_DISAGGREGATIONS,
        ).aggregate(
            total_stock_conflict_sum=Sum('total_stock_conflict'),
            total_flow_conflict_sum=Sum('total_flow_conflict'),
            total_stock_disaster_sum=Sum('total_stock_disaster'),
            total_flow_disaster_sum=Sum('total_flow_disaster'),
        )

    @cached_property
    def is_approved(self):
        if self.last_generation:
            return self.last_generation.is_approved
        return None

    @cached_property
    def approvals(self):
        if self.last_generation:
            return self.last_generation.approvals.all()
        return ReportApproval.objects.none()

    @cached_property
    def active_generation(self):
        # NOTE: There should be at most one active generation
        return self.generations.filter(is_signed_off=False).first()

    @cached_property
    def last_generation(self):
        return self.generations.annotate(
            is_approved=Exists(ReportApproval.objects.filter(
                generation=OuterRef('pk'),
                is_approved=True,
            ))
        ).order_by('-created_at').first()

    def sign_off(self, done_by: 'User'):
        current_gen = ReportGeneration.objects.get(
            report=self,
            is_signed_off=False,
        )
        current_gen.is_signed_off = True
        current_gen.is_signed_off_by = done_by
        current_gen.is_signed_off_on = timezone.now()
        current_gen.save(
            update_fields=[
                'is_signed_off', 'is_signed_off_by', 'is_signed_off_on'
            ]
        )

    class Meta:
        # TODO: implement the side effects of report sign off
        permissions = (
            ('sign_off_report', 'Can sign off the report'),
            ('approve_report', 'Can approve the report'),
        )

    def __str__(self):
        return self.name


class ReportComment(MetaInformationArchiveAbstractModel, models.Model):
    body = models.TextField(verbose_name=_('Body'))
    report = models.ForeignKey('Report', verbose_name=_('Report'),
                               related_name='comments', on_delete=models.CASCADE)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.body and self.body[:50]


class ReportApproval(MetaInformationArchiveAbstractModel, models.Model):
    generation = models.ForeignKey('ReportGeneration', verbose_name=_('Report'),
                                   related_name='approvals', on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, verbose_name=_('Approved By'),
                                   related_name='approvals', on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=True)

    class Meta:
        unique_together = (('generation', 'created_by'),)

    def __str__(self):
        return f'{self.generation.report} {"approved" if self.is_approved else "disapproved"} by {self.created_by}'


class ReportGeneration(MetaInformationArchiveAbstractModel, models.Model):
    '''
    A report can be generated multiple times, each called a generation
    '''
    FULL_REPORT_FOLDER = 'reports/full'
    SNAPSHOT_REPORT_FOLDER = 'reports/snaps'

    report = models.ForeignKey('Report', verbose_name=_('Report'),
                               related_name='generations', on_delete=models.CASCADE)
    is_signed_off = models.BooleanField(default=False)
    is_signed_off_on = models.DateTimeField(
        verbose_name=_('Is signed off on'),
        null=True
    )
    is_signed_off_by = models.ForeignKey(User, verbose_name=_('Is Signed Off By'),
                                         blank=True, null=True,
                                         related_name='signed_off_generations', on_delete=models.CASCADE)
    approvers = models.ManyToManyField(User, verbose_name=_('Approvers'),
                                       through='ReportApproval',
                                       through_fields=('generation', 'created_by'),
                                       related_name='approved_generations')
    # TODO schedule a task on create to generate following files
    full_report = CachedFileField(verbose_name=_('full report'),
                                  blank=True, null=True,
                                  upload_to=FULL_REPORT_FOLDER)
    snapshot = CachedFileField(verbose_name=_('report snapshot'),
                               blank=True, null=True,
                               upload_to=SNAPSHOT_REPORT_FOLDER)

    @cached_property
    def is_approved(self):
        return self.approvals.filter(is_approved=True).exists()

    @property
    def stat_flow_country(self):
        headers = {
            'country__iso3': 'ISO3',
            'country__name': 'Country',
            'country__region__name': 'Region',
            'conflict_total': f'Conflict FLOW {self.report.name}',
            'disaster_total': f'Disaster FLOW {self.report.name}',
            'total': f'Total FLOW {self.report.name}',
        }
        data = self.report.report_figures.values('country').order_by().annotate(
            conflict_total=Sum('total_figures', filter=Q(
                category__type=FLOW,
                role=Figure.ROLE.RECOMMENDED,
                entry__event__event_type=Crisis.CRISIS_TYPE.CONFLICT
            )),
            disaster_total=Sum('total_figures', filter=Q(
                category__type=FLOW,
                role=Figure.ROLE.RECOMMENDED,
                entry__event__event_type=Crisis.CRISIS_TYPE.DISASTER
            )),
        ).annotate(
            total=F('conflict_total') + F('disaster_total')
        ).values(
            'country__iso3',
            'country__name',
            'country__region__name',
            'conflict_total',
            'disaster_total',
            'total',
        )
        return headers, data, dict()

    @cached_property
    def stat_flow_region(self):
        headers = {
            'country__region__name': 'Region',
            'conflict_total': f'Conflict FLOW {self.report.name}',
            'disaster_total': f'Disaster FLOW {self.report.name}',
            'total': f'Total FLOW {self.report.name}',
        }
        data = self.report.report_figures.values('country__region').order_by().annotate(
            conflict_total=Sum('total_figures', filter=Q(
                category__type=FLOW,
                role=Figure.ROLE.RECOMMENDED,
                entry__event__event_type=Crisis.CRISIS_TYPE.CONFLICT
            )),
            disaster_total=Sum('total_figures', filter=Q(
                category__type=FLOW,
                role=Figure.ROLE.RECOMMENDED,
                entry__event__event_type=Crisis.CRISIS_TYPE.DISASTER
            )),
        ).annotate(
            total=F('conflict_total') + F('disaster_total')
        ).values(
            'country__region__name',
            'conflict_total',
            'disaster_total',
            'total',
        )
        return headers, data, dict()

    @cached_property
    def stat_conflict_country(self):
        headers = OrderedDict(dict(
            iso3='ISO3',
            name='Country',
            country_population='Population',
            flow_total=f'Flow {self.report.name}',
            stock_total=f'Stock {self.report.name}',
            flow_total_last_year='Flow Last Year',
            flow_historical_average='Flow Historical Average',
            stock_total_last_year='Stoc Last Year',
            stock_historical_average='Stock Historical Average',
            # provisional and returns
            # historical average for flow an stock NOTE: coming from different db
        ))

        def get_key(header):
            return excel_column_key(headers, header)

        # NOTE: {{ }} turns into { } after the first .format
        formula = {
            'Flow per 100k population': '=(100000 * {key1}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('country_population')
            ),
            'Flow percent variation wrt last year': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('flow_total_last_year')
            ),
            'Flow percent variation wrt average': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('flow_historical_average')
            ),
            'Stock per 100k population': '=(100000 * {key1}{{row}})/{key2}{{row}}'.format(
                key1=get_key('stock_total'), key2=get_key('country_population')
            ),
            'Stock percent variation wrt last year': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('stock_total'), key2=get_key('stock_total_last_year')
            ),
            'Stock percent variation wrt average': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('stock_total'), key2=get_key('stock_historical_average')
            ),
        }
        global_filter = dict(
            role=Figure.ROLE.RECOMMENDED,
            entry__event__event_type=Crisis.CRISIS_TYPE.CONFLICT
        )

        data = self.report.report_figures.values('country').order_by().annotate(
            country_population=Subquery(
                CountryPopulation.objects.filter(
                    year=int(self.report.filter_figure_start_after.year),
                    country=OuterRef('country'),
                ).values('population')
            ),
            iso3=F('country__iso3'),
            name=F('country__name'),
            flow_total=Sum('total_figures', filter=Q(
                category__type=FLOW,
                **global_filter
            )),
            flow_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__year=int(self.report.filter_figure_start_after.year) - 1,
                    country=OuterRef('country'),
                    category__type=FLOW,
                    **global_filter
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            flow_historical_average=Subquery(
                Figure.objects.filter(
                    start_date__lt=self.report.filter_figure_start_after,
                    country=OuterRef('country'),
                    category__type=FLOW,
                    **global_filter
                ).annotate(
                    min_year=Min(Extract('start_date', 'year')),
                    max_year=Max(Extract('start_date', 'year')),
                ).annotate(
                    _total=Sum('total_figures') / (F('max_year') - F('min_year') + 1)
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            stock_total=Sum('total_figures', filter=Q(
                category__type=STOCK,
                **global_filter
            )),
            stock_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__lt=self.report.filter_figure_start_after,
                    country=OuterRef('country'),
                    category__type=STOCK,
                    **global_filter
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            stock_historical_average=Subquery(
                Figure.objects.filter(
                    start_date__lt=self.report.filter_figure_start_after,
                    country=OuterRef('country'),
                    category__type=STOCK,
                    **global_filter
                ).annotate(
                    min_year=Min(Extract('start_date', 'year')),
                    max_year=Max(Extract('start_date', 'year')),
                ).annotate(
                    _total=Sum('total_figures') / (F('max_year') - F('min_year') + 1)
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
        )
        return headers, data, formula

    @cached_property
    def stat_conflict_region(self):
        headers = OrderedDict(dict(
            name='Region',
            region_population='Population',
            flow_total=f'Flow {self.report.name}',
            stock_total=f'Stock {self.report.name}',
            flow_total_last_year='Flow Last Year',
            flow_historical_average='Flow Historical Average',
            stock_total_last_year='Stock Last Year',
            stock_historical_average='Stock Historical Average',
            # provisional and returns
        ))

        def get_key(header):
            return excel_column_key(headers, header)

        # NOTE: {{ }} turns into { } after the first .format
        formula = {
            'Flow per 100k population': '=(100000 * {key1}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('region_population')
            ),
            'Flow percent variation wrt last year': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('flow_total_last_year')
            ),
            'Flow percent variation wrt average': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('flow_historical_average')
            ),
            'Stock per 100k population': '=(100000 * {key1}{{row}})/{key2}{{row}}'.format(
                key1=get_key('stock_total'), key2=get_key('region_population')
            ),
            'Stock percent variation wrt last year': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('stock_total'), key2=get_key('stock_total_last_year')
            ),
            'Stock percent variation wrt average': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('stock_total'), key2=get_key('stock_historical_average')
            ),
        }
        global_filter = dict(
            role=Figure.ROLE.RECOMMENDED,
            entry__event__event_type=Crisis.CRISIS_TYPE.CONFLICT
        )

        data = self.report.report_figures.annotate(
            region=F('country__region')
        ).values('region').order_by().annotate(
            region_population=Subquery(
                CountryPopulation.objects.values('country__region').order_by().annotate(
                    total_population=Sum('population', filter=Q(
                        year=int(self.report.filter_figure_start_after.year),
                        country__region=OuterRef('region'),
                    ))
                ).values('total_population')
            ),
            name=F('country__region__name'),
            flow_total=Sum('total_figures', filter=Q(
                category__type=FLOW,
                **global_filter
            )),
            flow_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__year=int(self.report.filter_figure_start_after.year) - 1,
                    country__region=OuterRef('region'),
                    category__type=FLOW,
                    **global_filter
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            flow_historical_average=Subquery(
                Figure.objects.filter(
                    start_date__lt=self.report.filter_figure_start_after,
                    country__region=OuterRef('region'),
                    category__type=FLOW,
                    **global_filter
                ).annotate(
                    min_year=Min(Extract('start_date', 'year')),
                    max_year=Max(Extract('start_date', 'year')),
                ).annotate(
                    _total=Sum('total_figures') / (F('max_year') - F('min_year') + 1)
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            stock_total=Sum('total_figures', filter=Q(
                category__type=STOCK,
                **global_filter
            )),
            stock_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__lt=self.report.filter_figure_start_after,
                    country__region=OuterRef('region'),
                    category__type=STOCK,
                    **global_filter
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            stock_historical_average=Subquery(
                Figure.objects.filter(
                    start_date__lt=int(self.report.filter_figure_start_after.year) - 1,
                    country__region=OuterRef('region'),
                    category__type=STOCK,
                    **global_filter
                ).annotate(
                    min_year=Min(Extract('start_date', 'year')),
                    max_year=Max(Extract('start_date', 'year')),
                ).annotate(
                    _total=Sum('total_figures') / (F('max_year') - F('min_year') + 1)
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
        )
        return headers, data, formula

    @cached_property
    def stat_conflict_typology(self):
        headers = OrderedDict(dict(
            iso3='ISO3',
            name='IDMC Short Name',
            typology='Conflict Typology',
            total='Figure',
        ))
        formula = dict()
        filtered_report_figures = self.report.report_figures.filter(
            role=Figure.ROLE.RECOMMENDED,
            entry__event__event_type=Crisis.CRISIS_TYPE.CONFLICT,
            category__type=FLOW,
        ).values('country').order_by()

        data = filtered_report_figures.filter(disaggregation_conflict__gt=0).annotate(
            name=models.F('country__name'),
            iso3=models.F('country__iso3'),
            total=models.Sum('disaggregation_conflict', filter=models.Q(disaggregation_conflict__gt=0)),
            typology=models.Value('Armed Conflict', output_field=models.CharField())
        ).values('name', 'iso3', 'total', 'typology').union(
            filtered_report_figures.filter(disaggregation_conflict_political__gt=0).annotate(
                name=models.F('country__name'),
                iso3=models.F('country__iso3'),
                total=models.Sum('disaggregation_conflict_political',
                                 filter=models.Q(disaggregation_conflict_political__gt=0)),
                typology=models.Value('Violence - Political', output_field=models.CharField())
            ).values('name', 'iso3', 'total', 'typology'),
            filtered_report_figures.filter(disaggregation_conflict_criminal__gt=0).annotate(
                name=models.F('country__name'),
                iso3=models.F('country__iso3'),
                total=models.Sum('disaggregation_conflict_criminal',
                                 filter=models.Q(disaggregation_conflict_criminal__gt=0)),
                typology=models.Value('Violence - Criminal', output_field=models.CharField())
            ).values('name', 'iso3', 'total', 'typology'),
            filtered_report_figures.filter(disaggregation_conflict_communal__gt=0).annotate(
                name=models.F('country__name'),
                iso3=models.F('country__iso3'),
                total=models.Sum('disaggregation_conflict_communal',
                                 filter=models.Q(disaggregation_conflict_communal__gt=0)),
                typology=models.Value('Violence - Communal', output_field=models.CharField())
            ).values('name', 'iso3', 'total', 'typology'),
            filtered_report_figures.filter(disaggregation_conflict_other__gt=0).annotate(
                name=models.F('country__name'),
                iso3=models.F('country__iso3'),
                total=models.Sum('disaggregation_conflict_other', filter=models.Q(disaggregation_conflict_other__gt=0)),
                typology=models.Value('Other', output_field=models.CharField())
            ).values('name', 'iso3', 'total', 'typology')
        ).values('name', 'iso3', 'typology', 'total').order_by('typology')

        # further aggregation
        aggregation_headers = OrderedDict(dict(
            typology='Conflict Typology',
            total='Sum of Figure',
        ))
        aggregation_formula = dict()

        filtered_report_figures = self.report.report_figures.filter(
            role=Figure.ROLE.RECOMMENDED,
            entry__event__event_type=Crisis.CRISIS_TYPE.CONFLICT,
            category__type=FLOW,
        )

        aggregation_data = filtered_report_figures.aggregate(
            total_conflict=Sum('disaggregation_conflict'),
            total_conflict_political=Sum('disaggregation_conflict_political'),
            total_conflict_other=Sum('disaggregation_conflict_other'),
            total_conflict_criminal=Sum('disaggregation_conflict_criminal'),
            total_conflict_communal=Sum('disaggregation_conflict_communal'),
        )
        aggregation_data = [
            dict(
                typology='Armed Conflict',
                total=aggregation_data['total_conflict'],
            ),
            dict(
                typology='Violence - Political',
                total=aggregation_data['total_conflict_political'],
            ),
            dict(
                typology='Violence - Criminal',
                total=aggregation_data['total_conflict_criminal'],
            ),
            dict(
                typology='Violence - Communal',
                total=aggregation_data['total_conflict_communal'],
            ),
            dict(
                typology='Other',
                total=aggregation_data['total_conflict_other'],
            ),
        ]

        return headers, data, formula, dict(
            headers=aggregation_headers,
            formulae=aggregation_formula,
            data=aggregation_data,
        )

    @cached_property
    def global_numbers(self):
        ...

    @cached_property
    def disaster_event(self):
        headers = OrderedDict(dict(
            event_id='Event ID',
            event_name='Event Name',
            event_year='Event Year',
            event_start_date='Start Date',
            event_end_date='End Date',
            event_category='Category',
            event_sub_category='Sub-Category',
            dtype='Hazard Type',
            dsub_type='Hazard Sub-Type',
            affected_iso3='Affected ISO3',
            affected_names='Affected Countries',
            affected_countries='Number of Affected Countries',
            flow_total='ND' + self.report.name,
        ))

        def get_key(header):
            return excel_column_key(headers, header)

        # NOTE: {{ }} turns into { } after the first .format
        formula = {
        }
        global_filter = dict(
            role=Figure.ROLE.RECOMMENDED,
            entry__event__event_type=Crisis.CRISIS_TYPE.DISASTER
        )

        data = self.report.report_figures.filter(
            **global_filter
        ).values('entry__event').order_by().annotate(
            event_id=F('entry__event_id'),
            event_name=F('entry__event__name'),
            event_year=Extract('entry__event__start_date', 'year'),
            event_start_date=F('entry__event__start_date'),
            event_end_date=F('entry__event__end_date'),
            event_category=F('entry__event__disaster_category__name'),
            event_sub_category=F('entry__event__disaster_sub_category__name'),
            dtype=F('entry__event__disaster_type__name'),
            dsub_type=F('entry__event__disaster_sub_type__name'),
            # # FIXME: this is not FLOW but should be category = New Displacement
            flow_total=Sum('total_figures', filter=Q(category__type=FLOW)),
            affected_countries=Count('country', distinct=True),
            affected_iso3=StringAgg('country__iso3', delimiter=', ', distinct=True),
            affected_names=StringAgg('country__name', delimiter=' | ', distinct=True),
        )
        return headers, data, formula, None

    @cached_property
    def disaster_region(self):
        headers = OrderedDict(dict(
            region_name='Region',
            events_count='Number of Events',
            region_population='Region Population',
            flow_total=f'ND {self.report.name}',
            flow_total_last_year='ND Flow Last Year',
            flow_historical_average='ND Flow Historical Average',
        ))

        def get_key(header):
            return excel_column_key(headers, header)

        formulae = {
            'Flow per 100k population': '=(100000 * {key1}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('region_population')
            ),
            'Flow percent variation wrt last year': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('flow_total_last_year')
            ),
            'Flow percent variation wrt average': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('flow_historical_average')
            ),
        }
        global_filter = dict(
            role=Figure.ROLE.RECOMMENDED,
            entry__event__event_type=Crisis.CRISIS_TYPE.DISASTER,
        )
        data = self.report.report_figures.filter(
            **global_filter
        ).values('country__region').order_by().annotate(
            region_name=F('country__region__name'),
            country_region=F('country__region__name'),
            events_count=Count('entry__event', distinct=True),
            region_population=Subquery(
                CountryPopulation.objects.values('country__region').order_by().annotate(
                    total_population=Sum('population', filter=Q(
                        year=int(self.report.filter_figure_start_after.year),
                        country__region=OuterRef('country__region'),
                    ))
                ).values('total_population')
            ),
            flow_total=Sum('total_figures', filter=Q(
                # FIXME
                category__type=FLOW,
                **global_filter
            )),
            flow_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__year=int(self.report.filter_figure_start_after.year) - 1,
                    country__region=OuterRef('country__region'),
                    # FIXME
                    category__type=FLOW,
                    **global_filter
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            flow_historical_average=Subquery(
                Figure.objects.filter(
                    start_date__lt=self.report.filter_figure_start_after,
                    country__region=OuterRef('country__region'),
                    # FIXME
                    category__type=FLOW,
                    **global_filter
                ).annotate(
                    min_year=Min(Extract('start_date', 'year')),
                    max_year=Max(Extract('start_date', 'year')),
                ).annotate(
                    _total=Sum('total_figures') / (F('max_year') - F('min_year') + 1)
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
        )

        return headers, data, formulae, None

    @cached_property
    def disaster_country(self):
        headers = OrderedDict(dict(
            country_iso3='ISO3',
            country_name='Name',
            country_region='Region',
            events_count='Number of Events',
            country_population='Country Population',
            flow_total=f'ND {self.report.name}',
            flow_total_last_year='ND Flow Last Year',
            flow_historical_average='ND Flow Historical Average',
        ))

        def get_key(header):
            return excel_column_key(headers, header)

        formulae = {
            'Flow per 100k population': '=(100000 * {key1}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('country_population')
            ),
            'Flow percent variation wrt last year': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('flow_total_last_year')
            ),
            'Flow percent variation wrt average': '=100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}'.format(
                key1=get_key('flow_total'), key2=get_key('flow_historical_average')
            ),
        }
        global_filter = dict(
            role=Figure.ROLE.RECOMMENDED,
            entry__event__event_type=Crisis.CRISIS_TYPE.DISASTER,
        )
        data = self.report.report_figures.filter(
            **global_filter
        ).values('country').order_by().annotate(
            country_iso3=F('country__iso3'),
            country_name=F('country__name'),
            country_region=F('country__region__name'),
            events_count=Count('entry__event', distinct=True),
            country_population=Subquery(
                CountryPopulation.objects.filter(
                    year=int(self.report.filter_figure_start_after.year),
                    country=OuterRef('country'),
                ).values('population')
            ),
            flow_total=Sum('total_figures', filter=Q(
                category__type=FLOW,
                **global_filter
            )),
            flow_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__year=int(self.report.filter_figure_start_after.year) - 1,
                    country=OuterRef('country'),
                    category__type=FLOW,
                    **global_filter
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            flow_historical_average=Subquery(
                Figure.objects.filter(
                    start_date__lt=self.report.filter_figure_start_after,
                    country=OuterRef('country'),
                    category__type=FLOW,
                    **global_filter
                ).annotate(
                    min_year=Min(Extract('start_date', 'year')),
                    max_year=Max(Extract('start_date', 'year')),
                ).annotate(
                    _total=Sum('total_figures') / (F('max_year') - F('min_year') + 1)
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
        )

        return headers, data, formulae, None

    def get_excel_sheets_data(self):
        '''
        Returns title and corresponding computed property
        '''
        return {
            # 'Flow Country': self.stat_flow_country,
            # 'Flow Region': self.stat_flow_region,
            # 'Conflict Country': self.stat_conflict_country,
            # 'Conflict Region': self.stat_conflict_region,
            # 'Conflict Typology': self.stat_conflict_typology,
            # 'Disaster Event': self.disaster_event,
            # 'Disaster Country': self.disaster_country,
            'Disaster Region': self.disaster_region,
        }

    def __str__(self):
        return f'{self.created_by} signed off {self.report} on {self.created_at}'

from django.db import models
from django.db.models import Sum, Q, F
from django.utils.translation import gettext_lazy as _

from apps.contrib.models import MetaInformationArchiveAbstractModel
from apps.crisis.models import Crisis
from apps.entry.constants import STOCK, FLOW
from apps.entry.models import FigureDisaggregationAbstractModel, Figure
from apps.extraction.models import QueryAbstractModel
from utils.permissions import cache_me


class Report(MetaInformationArchiveAbstractModel,
             QueryAbstractModel,
             FigureDisaggregationAbstractModel,
             models.Model):
    # migrated or generated
    generated = models.BooleanField(verbose_name=_('Generated'), default=True,
                                    editable=False)
    reports = models.ManyToManyField('self', verbose_name=_('Reports (old groups)'),
                                     blank=True, related_name='masterfact_reports',
                                     symmetrical=False)
    figures = models.ManyToManyField('entry.Figure',
                                     blank=True)
    # query fields but modified
    figure_start_after = models.DateField(verbose_name=_('From Date'), null=True)
    figure_end_before = models.DateField(verbose_name=_('To Date'), null=True)
    # user entered fields
    analysis = models.TextField(verbose_name=_('Analysis'),
                                blank=True, null=True)
    methodology = models.TextField(verbose_name=_('Methodology'), blank=True, null=True)
    significant_updates = models.TextField(verbose_name=_('Significant Updates'),
                                           blank=True, null=True)
    challenges = models.TextField(verbose_name=_('Challenges'), blank=True, null=True)

    reported = models.PositiveIntegerField(verbose_name=_('Reported Figures'), default=0, editable=False)
    total_figures = models.PositiveIntegerField(verbose_name=_('Total Figures'), default=0,
                                                editable=False)
    # old fields will be migrated into summary
    summary = models.TextField(verbose_name=_('Summary'), blank=True, null=True,
                               help_text=_('It will store master fact information:'
                                           'Comment, Source Excerpt, IDU Excerpt, Breakdown & '
                                           'Reliability, and Caveats'))

    @property
    def report_figures(self):
        if not self.generated:
            return Figure.objects.filter(
                id__in=(
                    Report.objects.filter(id=self.id) |
                    Report.objects.get(id=self.id).masterfact_reports.all()
                ).values('figures'))
        else:
            return Figure.objects.filter(
                start_date__gte=self.figure_start_after,
                start_date__lt=self.figure_end_before,
            )

    @property
    # @cache_me(3000)
    def countries_report(self) -> list:
        return self.report_figures.select_related(
            'country'
        ).values('country').order_by().distinct().annotate(
            id=F('country_id'),
            name=F('country__name'),
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

    @property
    # @cache_me(3000)
    def events_report(self) -> list:
        return self.report_figures.select_related(
            'event__entry'
        ).values('entry__event').order_by().distinct().annotate(
            event=F('entry__event'),
            id=F('entry__event_id'),
            name=F('entry__event__name'),
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

    class Meta:
        # TODO: implement the side effects of report sign off
        permissions = (('sign_off_report', 'Can sign off the report'),)

    def __str__(self):
        return self.name

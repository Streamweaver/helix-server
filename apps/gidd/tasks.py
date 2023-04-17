import datetime
import logging
from helix.celery import app as celery_app

from django.db.models import (
    Sum, Case, When, IntegerField, Value,
    F, Subquery, OuterRef
)
from apps.entry.models import Figure
from apps.event.models import Event
from apps.event.models import Crisis
from .models import Conflict, Disaster


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def annotate_conflict(qs, year):
    return qs.annotate(
        year=Value(year, output_field=IntegerField()),
    ).values('year', 'country__idmc_short_name', 'country__iso3').annotate(
        total_displacement=Sum(
            Case(
                When(
                    category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
                    then=F('total_figures')
                ),
                output_field=IntegerField(),
                default=0
            )
        ),
        new_displacement=Sum(
            Case(
                When(
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                    then=F('total_figures')
                ),
                output_field=IntegerField(),
                default=0
            )
        ),
        country=F('country'),
    ).order_by('year')


@celery_app.task
def sync_gidd_data():
    # Delete all the conflicts TODO: Find way to update records
    Conflict.objects.all().delete()

    # Delete disasters
    Disaster.objects.all().delete()

    figure_queryset = Figure.objects.filter(
        role=Figure.ROLE.RECOMMENDED
    )
    start_year = 2016
    end_year = 2023
    for year in range(start_year, end_year):
        nd_figure_qs = Figure.filtered_nd_figures(
            qs=figure_queryset,
            start_date=datetime.datetime(year=year, month=1, day=1),
            end_date=datetime.datetime(year=year, month=12, day=31),
        )
        stock_figure_qs = Figure.filtered_idp_figures(
            qs=figure_queryset,
            start_date=datetime.datetime(year=year, month=1, day=1),
            end_date=datetime.datetime(year=year, month=12, day=31),
        )
        conflict_nd_figure_qs = nd_figure_qs.filter(event__event_type=Crisis.CRISIS_TYPE.CONFLICT)
        conflict_stock_figure_qs = stock_figure_qs.filter(event__event_type=Crisis.CRISIS_TYPE.CONFLICT)
        conflict_figure_qs = conflict_nd_figure_qs | conflict_stock_figure_qs
        qs = annotate_conflict(Figure.objects.filter(id__in=conflict_figure_qs.values('id')), year)

        # Create new conflict figures
        Conflict.objects.bulk_create(
            [
                Conflict(
                    country_id=figure['country'],
                    total_displacement=figure['total_displacement'],
                    new_displacement=figure['new_displacement'],
                    year=figure['year'],
                    iso3=figure['country__iso3'],
                    country_name=figure['country__idmc_short_name'],
                ) for figure in qs
            ]
        )

        # Sync disaster data
        events = Event.objects.filter(
            disaster_category__isnull=False,
            disaster_type__isnull=False
        ).annotate(
            **{
                'new_displacement': Subquery(
                    Figure.filtered_nd_figures(
                        figure_queryset.filter(
                            event=OuterRef('pk'),
                        ),
                        start_date=datetime.datetime(year=year, month=1, day=1),
                        end_date=datetime.datetime(year=year, month=12, day=31),
                    ).order_by().values('event').annotate(
                        _total=Sum('total_figures')
                    ).values('_total')[:1],
                    output_field=IntegerField()
                ),
            },
            year=Value(year, output_field=IntegerField()),
            hazard_category=F('disaster_category__name'),
            hazard_sub_category=F('disaster_sub_category__name'),
            hazard_type=F('disaster_type__name'),
            hazard_sub_type=F('disaster_sub_type__name'),
            country=F('figures__country'),
            iso3=F('figures__country__iso3'),
            country_name=F('figures__country__name'),
        ).filter(
            new_displacement__isnull=False,
        ).order_by('year').values(
            'year',
            'id',
            'start_date',
            'start_date_accuracy',
            'end_date',
            'end_date_accuracy',
            'hazard_category',
            'hazard_sub_category',
            'hazard_type',
            'hazard_sub_type',
            'new_displacement',
            'country',
            'iso3',
            'country_name',
        ).distinct(
            'year',
            'id',
            'start_date',
            'start_date_accuracy',
            'end_date',
            'end_date_accuracy',
            'hazard_category',
            'hazard_sub_category',
            'hazard_type',
            'hazard_sub_type',
            'new_displacement',
            'country',
            'iso3',
            'country_name',
        )
        Disaster.objects.bulk_create(
            [
                Disaster(
                    event_id=item['id'],
                    year=item['year'],
                    start_date=item['start_date'],
                    start_date_accuracy=item['start_date_accuracy'],
                    end_date=item['end_date'],
                    end_date_accuracy=item['end_date_accuracy'],
                    hazard_category=item['hazard_category'],
                    hazard_sub_category=item['hazard_sub_category'],
                    hazard_type=item['hazard_type'],
                    hazard_sub_type=item['hazard_sub_type'],
                    new_displacement=item['new_displacement'],
                    iso3=item['iso3'],
                    country_id=item['country'],
                    country_name=item['country_name'],
                ) for item in events
            ]
        )
    logger.info('Gidd synced.')

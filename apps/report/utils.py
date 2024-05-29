from django.utils import timezone
from django.db.models.functions import Extract, Coalesce
from django.db import models
from django.db.models import (
    Sum,
    Count,
    Q,
    F,
    Subquery,
    OuterRef,
    Min,
    Max,
    Value,
)
from django.contrib.postgres.aggregates import StringAgg
from collections import OrderedDict
from datetime import timedelta
from apps.entry.models import Figure
from apps.crisis.models import Crisis
from apps.country.models import (
    CountryPopulation,
    Country,
    CountryRegion,
)
from apps.common.utils import EXTERNAL_ARRAY_SEPARATOR
from utils.common import is_grid_or_myu_report

EXCEL_FORMULAE = {
    'per_100k': '=IF({key2}{{row}} <> "", (100000 * {key1}{{row}})/{key2}{{row}}, "")',
    'percent_variation': '=IF({key2}{{row}}, 100 * ({key1}{{row}} - {key2}{{row}})/{key2}{{row}}, "")',
}


def excel_column_key(headers, header) -> str:
    """

    :param headers: Dictionary containing column headers as keys
    :param header: The header for which to find the corresponding column key
    :return: The column key corresponding to the given header
    :rtype: str
    """
    seed = ord('A')
    return chr(list(headers.keys()).index(header) + seed)


def report_global_numbers(report):
    """
    Calculate the global numbers for a given report.

    Parameters:
    - report: The report for which to calculate the global numbers.

    Returns:
    - A dictionary containing the following keys:
      - headers: A dictionary containing formatted headers for the data.
      - data: A list of dictionaries containing the calculated data.
      - formulae: A dictionary for any additional formulas, if needed.

    Example Usage:
        report = get_report()  # Get the report object
        global_numbers = report_global_numbers(report)
        print(global_numbers)

    Example Output:
    {
        'headers': {
            'one': '',
            'two': '',
            'three': '',
        },
        'data': [
            {'one': 'Conflict'},
            {'one': 'Data'},
            {'one': 'Sum of ND Report', 'two': 'Sum of IDPs Report'},
            {'one': 800, 'two': 1200},
            {'one': ''},
            {'one': 'Disaster'},
            {'one': 'Data'},
            {'one': 'Sum of ND Report', 'two': 'Number of Events of Report'},
            {'one': 500, 'two': 3},
            {'one': ''},
            {'one': 'Total Internal Displacements (Conflict + Disaster)', 'two': 1300},
            {'one': 'Conflict', 'two': '61.54%'},
            {'one': 'Disaster', 'two': '38.46%'},
            {'one': ''},
            {'one': 'Number of countries with figures', 'two': 10},
            {'one': 'Conflict', 'two': 5},
            {'one': 'Disaster', 'two': 5}
        ],
        'formulae': {}
    }
    """
    conflict_filter = dict(
        role=Figure.ROLE.RECOMMENDED,
        event__event_type=Crisis.CRISIS_TYPE.CONFLICT,
    )
    disaster_filter = dict(
        role=Figure.ROLE.RECOMMENDED,
        event__event_type=Crisis.CRISIS_TYPE.DISASTER,
    )
    data = report.report_figures.aggregate(
        flow_disaster_total=Coalesce(
            Sum(
                'total_figures',
                filter=Q(
                    **disaster_filter,
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                )
            ), 0
        ),
        flow_conflict_total=Coalesce(
            Sum(
                'total_figures',
                filter=Q(
                    **conflict_filter,
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                )
            ), 0
        ),
        stock_conflict_total=Coalesce(
            Sum(
                'total_figures',
                filter=Q(
                    Q(
                        end_date__isnull=True,
                    ) | Q(
                        end_date__isnull=False,
                        end_date__gte=report.filter_figure_end_before or timezone.now().date(),
                    ),
                    **conflict_filter,
                    category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
                )
            ), 0
        ),
        event_disaster_count=Coalesce(
            Count(
                'event',
                filter=Q(
                    **disaster_filter,
                ),
                distinct=True
            ), 0
        ),
        conflict_countries_count=Coalesce(
            Count(
                'country',
                filter=Q(
                    **conflict_filter,
                ),
                distinct=True
            ), 0
        ),
        disaster_countries_count=Coalesce(
            Count(
                'country',
                filter=Q(
                    **disaster_filter,
                ),
                distinct=True
            ), 0
        ),
    )
    data['countries_count'] = data['conflict_countries_count'] + data['disaster_countries_count']
    data['flow_total'] = data['flow_disaster_total'] + data['flow_conflict_total']
    data['flow_conflict_percent'] = 100 * data['flow_conflict_total'] / data['flow_total'] if data['flow_total'] else 0
    data['flow_disaster_percent'] = 100 * data['flow_disaster_total'] / data['flow_total'] if data['flow_total'] else 0

    # this is simply for placeholder
    formatted_headers = {
        'one': '',
        'two': '',
        'three': '',
    }
    formatted_data = [
        dict(
            one='Conflict',
        ),
        dict(
            one='Data',
        ),
        dict(
            one=f'Sum of ND {report.name}',
            two=f'Sum of IDPs {report.name}',
        ),
        dict(
            one=data['flow_conflict_total'],
            two=data['stock_conflict_total'],
        ),
        dict(
            one='',
        ),
        dict(
            one='Disaster',
        ),
        dict(
            one='Data',
        ),
        dict(
            one=f'Sum of ND {report.name}',
            two=f'Number of Events of {report.name}',
        ),
        dict(
            one=data['flow_disaster_total'],
            two=data['event_disaster_count'],
        ),
        dict(
            one='',
        ),
        dict(
            one='Total Internal Displacements (Conflict + Disaster)',
            two=data['flow_total']
        ),
        dict(
            one='Conflict',
            two=f"{data['flow_conflict_percent']}%",
        ),
        dict(
            one='Disaster',
            two=f"{data['flow_disaster_percent']}%",
        ),
        dict(
            one='',
        ),
        dict(
            one='Number of countries with figures',
            two=data['countries_count']
        ),
        dict(
            one='Conflict',
            two=data['conflict_countries_count'],
        ),
        dict(
            one='Disaster',
            two=data['disaster_countries_count'],
        ),
    ]

    return dict(
        headers=formatted_headers,
        data=formatted_data,
        formulae=dict(),
    )


def report_stat_flow_country(report):
    """
    Method: report_stat_flow_country

    This method generates a report for statistical flow by country. It takes a report object as a parameter.

    Parameters:
        - report (object): The report object containing the necessary data for generating the report.

    Returns:
        - dictionary: A dictionary containing the following keys:
            - 'headers': A dictionary mapping the column names to the corresponding data fields.
            - 'data': A queryset containing the report data for each country.
            - 'formulae': A dictionary containing any formulae used in the report.

    Example usage:

        report = <report object>

        result = report_stat_flow_country(report)
    """
    headers = {
        'id': 'ID',
        'iso3': 'ISO3',
        'idmc_short_name': 'Country',
        'region__name': 'Region',
        Country.ND_CONFLICT_ANNOTATE: f'Conflict ND {report.name}',
        Country.ND_DISASTER_ANNOTATE: f'Disaster ND {report.name}',
        'total': f'Total ND {report.name}'
    }

    def get_key(header):
        return excel_column_key(headers, header)

    formulae = {}
    data = Country.objects.filter(
        id__in=report.report_figures.values('country')
    ).annotate(
        **Country._total_figure_disaggregation_subquery(
            report.report_figures,
            ignore_dates=True,
        )
    ).annotate(
        total=Coalesce(
            F(Country.ND_CONFLICT_ANNOTATE), 0
        ) + Coalesce(
            F(Country.ND_DISASTER_ANNOTATE), 0
        )
    ).order_by('id').values(
        *list(headers.keys())
    )
    return {
        'headers': headers,
        'data': data,
        'formulae': formulae,
    }


def report_stat_flow_region(report):
    """
    Report statistics for a given flow region.

    :param report: The report object
    :return: A dictionary containing headers, data, and formulae

    The `report_stat_flow_region` method calculates and returns statistical data for a given flow region based on the provided report. The method takes a single parameter `report`, which is the report object.

    The method starts by defining a dictionary `headers` that maps column names to their corresponding labels. The column names are 'id', 'name', 'Conflict ND {report.name}', 'Disaster ND {report.name}', and 'Total ND {report.name}'. These labels are used to display the column headers in the output.

    Next, the method defines an empty dictionary `formulae` that will hold the calculated formulas.

    The method then retrieves data from the `CountryRegion` model using a filter to get the relevant regions based on the report's country regions. The retrieved data is annotated with the total figure disaggregation subquery for the report, ignoring dates.

    After that, the method calculates the total value by summing the 'Conflict ND' and 'Disaster ND' values for each region using the `Coalesce` and `F` functions. The result is annotated as 'total' for each row.

    Finally, the method returns a dictionary containing the headers, the retrieved data, and the formulae.

    Example usage:
        report = ...
        result = report_stat_flow_region(report)
        headers = result['headers']
        data = result['data']
        formulae = result['formulae']
    """
    headers = {
        'id': 'ID',
        'name': 'Region',
        CountryRegion.ND_CONFLICT_ANNOTATE: f'Conflict ND {report.name}',
        CountryRegion.ND_DISASTER_ANNOTATE: f'Disaster ND {report.name}',
        'total': f'Total ND {report.name}',
    }

    # NOTE: {{ }} turns into { } after the first .format
    formulae = {}
    data = CountryRegion.objects.filter(
        id__in=report.report_figures.values('country__region')
    ).annotate(
        **CountryRegion._total_figure_disaggregation_subquery(
            report.report_figures,
            ignore_dates=True,
        )
    ).annotate(
        total=Coalesce(
            F(CountryRegion.ND_CONFLICT_ANNOTATE), 0
        ) + Coalesce(
            F(CountryRegion.ND_DISASTER_ANNOTATE), 0
        )
    ).values(
        *list(headers.keys())
    )
    return {
        'headers': headers,
        'data': data,
        'formulae': formulae,
    }


def report_stat_conflict_country(report, include_history):
    """
    Report statistics by conflict country.

    Parameters:
    - report: The report object containing the figures.
    - include_history: Flag indicating whether to include historical data.

    Returns:
    A dictionary containing the following keys:
    - headers: An ordered dictionary of the headers and their corresponding labels.
    - data: The aggregated data for each country, including population, figures for new displacement (flow) and IDPs (stock).
    - formulae: A dictionary of formulae for calculations based on the aggregated data.
    - aggregation: None (not used in the current implementation).
    """
    headers = OrderedDict(dict(
        iso3='ISO3',
        name='Country',
        country_population='Population',
        flow_total=f'ND {report.name}',
        stock_total=f'IDPs {report.name}',
        flow_total_last_year='ND last year',
        stock_total_last_year='IDPs last year',
        flow_historical_average='ND historical average',
        stock_historical_average='IDPs historical average',
        # provisional and returns
        # historical average for flow an stock NOTE: coming from different db
    ))

    def get_key(header):
        return excel_column_key(headers, header)

    # NOTE: {{ }} turns into { } after the first .format
    formulae = {
        'ND per 100k population': EXCEL_FORMULAE['per_100k'].format(
            key1=get_key('flow_total'), key2=get_key('country_population')
        ),
        'ND percent variation wrt last year':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('flow_total'), key2=get_key('flow_total_last_year')
        ),
        'ND percent variation wrt average':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('flow_total'), key2=get_key('flow_historical_average')
        ),
        'IDPs per 100k population': EXCEL_FORMULAE['per_100k'].format(
            key1=get_key('stock_total'), key2=get_key('country_population')
        ),
        'IDPs percent variation wrt last year':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('stock_total'), key2=get_key('stock_total_last_year')
        ),
        'IDPs percent variation wrt average':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('stock_total'), key2=get_key('stock_historical_average')
        ),
    }
    global_filter = dict(
        role=Figure.ROLE.RECOMMENDED,
        event__event_type=Crisis.CRISIS_TYPE.CONFLICT
    )

    data = report.report_figures.values('country').order_by().annotate(
        country_population=Subquery(
            CountryPopulation.objects.filter(
                year=int(report.filter_figure_start_after.year),
                country=OuterRef('country'),
            ).values('population')
        ),
        iso3=F('country__iso3'),
        name=F('country__idmc_short_name'),
        flow_total=Sum('total_figures', filter=Q(
            category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
            **global_filter
        )),
        stock_total=Sum('total_figures', filter=Q(
            Q(
                end_date__isnull=True,
            ) | Q(
                end_date__isnull=False,
                end_date__gte=report.filter_figure_end_before or timezone.now().date(),
            ),
            category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
            **global_filter
        )),
    )

    if is_grid_or_myu_report(report.filter_figure_start_after, report.filter_figure_end_before) and include_history:
        data = data.annotate(
            flow_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__gte=report.filter_figure_start_after - timedelta(days=365),
                    end_date__lte=report.filter_figure_end_before - timedelta(days=365),
                    country=OuterRef('country'),
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                    **global_filter
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            flow_historical_average=Subquery(
                Figure.objects.filter(
                    start_date__lt=report.filter_figure_start_after,
                    # only consider the figures in the given month range
                    start_date__month__gte=report.filter_figure_start_after.month,
                    end_date__month__lte=report.filter_figure_end_before.month,
                    country=OuterRef('country'),
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                    **global_filter
                ).annotate(
                    min_year=Min(Extract('start_date', 'year')),
                    max_year=Max(Extract('start_date', 'year')),
                ).annotate(
                    _total=Sum('total_figures') / (F('max_year') - F('min_year') + 1)
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            stock_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__lte=report.filter_figure_end_before - timedelta(days=365),
                    country=OuterRef('country'),
                    category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
                    **global_filter
                ).filter(
                    Q(
                        end_date__isnull=False,
                        end_date__gte=report.filter_figure_end_before - timedelta(days=365)
                    ) | Q(
                        end_date__isnull=True
                    ),
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            # TODO: we will need to handle each year separately for idp figures to get the average
            stock_historical_average=Value('...', output_field=models.CharField()),
        )
    return {
        'headers': headers,
        'data': data,
        'formulae': formulae,
        'aggregation': None,
    }


def report_stat_conflict_region(report, include_history):
    """

    This method generates a report on statistical conflict regions based on the given report and include_history parameter. It returns a dictionary with the following keys:

    - headers: an OrderedDict containing the column headers for the report. The keys represent the column names and the values represent the column labels.
    - data: a queryset that contains the data for the report. It includes the following fields: region, region_population, name, flow_total, stock_total.
    - formulae: an OrderedDict containing the formulas to calculate additional statistics for each region. The keys represent the statistic names and the values represent the formula templates.
    - aggregation: currently set to None.

    Parameters:
    - report: the report object.
    - include_history: a boolean indicating whether to include historical data in the report.

    Example usage:
    report = ...
    include_history = True
    result = report_stat_conflict_region(report, include_history)

    """
    headers = OrderedDict(dict(
        name='Region',
        region_population='Population',
        flow_total=f'ND {report.name}',
        stock_total=f'IDPs {report.name}',
        flow_total_last_year='ND Last Year',
        stock_total_last_year='IDPs Last Year',
        flow_historical_average='ND Historical Average',
        stock_historical_average='IDPs Historical Average',
        # provisional and returns
    ))

    def get_key(header):
        return excel_column_key(headers, header)

    # NOTE: {{ }} turns into { } after the first .format
    formulae = OrderedDict({
        'ND per 100k population': EXCEL_FORMULAE['per_100k'].format(
            key1=get_key('flow_total'), key2=get_key('region_population')
        ),
        'ND percent variation wrt last year':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('flow_total'), key2=get_key('flow_total_last_year')
        ),
        'ND percent variation wrt average':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('flow_total'), key2=get_key('flow_historical_average')
        ),
        'IDPs per 100k population': EXCEL_FORMULAE['per_100k'].format(
            key1=get_key('stock_total'), key2=get_key('region_population')
        ),
        'IDPs percent variation wrt last year':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('stock_total'), key2=get_key('stock_total_last_year')
        ),
        'IDPs percent variation wrt average':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('stock_total'), key2=get_key('stock_historical_average')
        ),
    })
    global_filter = dict(
        role=Figure.ROLE.RECOMMENDED,
        event__event_type=Crisis.CRISIS_TYPE.CONFLICT
    )

    data = report.report_figures.annotate(
        region=F('country__region')
    ).values('region').order_by().annotate(
        region_population=Subquery(
            CountryPopulation.objects.filter(
                year=int(report.filter_figure_start_after.year),
                country__region=OuterRef('region'),
            ).annotate(
                total_population=Sum('population'),
            ).values('total_population')[:1]
        ),
        name=F('country__region__name'),
        flow_total=Sum('total_figures', filter=Q(
            category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
            **global_filter
        )),
        stock_total=Sum('total_figures', filter=Q(
            Q(
                end_date__isnull=True,
            ) | Q(
                end_date__isnull=False,
                end_date__gte=report.filter_figure_end_before or timezone.now().date(),
            ),
            category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
            **global_filter,
        )),
    )

    if is_grid_or_myu_report(report.filter_figure_start_after, report.filter_figure_end_before) and include_history:
        data = data.annotate(
            flow_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__gte=report.filter_figure_start_after - timedelta(days=365),
                    end_date__lte=report.filter_figure_end_before - timedelta(days=365),
                    country__region=OuterRef('region'),
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                    **global_filter
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            flow_historical_average=Subquery(
                Figure.objects.filter(
                    start_date__lt=report.filter_figure_start_after,
                    # only consider the figures in the given month range
                    start_date__month__gte=report.filter_figure_start_after.month,
                    country__region=OuterRef('region'),
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                    **global_filter
                ).annotate(
                    min_year=Min(Extract('start_date', 'year')),
                    max_year=Max(Extract('start_date', 'year')),
                ).annotate(
                    _total=Sum('total_figures') / (F('max_year') - F('min_year') + 1)
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            stock_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__lte=report.filter_figure_end_before - timedelta(days=365),
                    country__region=OuterRef('region'),
                    category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
                    **global_filter
                ).filter(
                    Q(
                        end_date__isnull=False,
                        end_date__gte=report.filter_figure_end_before - timedelta(days=365)
                    ) | Q(
                        end_date__isnull=True
                    ),
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            # TODO: stock historical average must be pre-calculated for each year
            stock_historical_average=Value('...', output_field=models.CharField()),
        )
    return {
        'headers': headers,
        'data': data,
        'formulae': formulae,
        'aggregation': None,
    }


def report_stat_conflict_typology(report):
    """
    Report Stat Conflict Typology

    This method takes a 'report' object as a parameter and generates a statistical report on conflict typologies.

    Parameters:
    - report: The report object containing the data for analysis

    Returns:
    This method returns a dictionary containing the following keys:
    - 'headers': An ordered dictionary with the following keys:
        - 'iso3': ISO3 code
        - 'name': IDMC short name
        - 'typology': Conflict typology
        - 'total': Figure
    - 'data': A queryset containing the filtered and annotated data for each conflict typology
    - 'formulae': An empty dictionary
    - 'aggregation': A sub-dictionary containing the aggregated data:
        - 'headers': An ordered dictionary with the following keys:
            - 'typology': Conflict typology
            - 'total': Sum of figure
        - 'formulae': An empty dictionary
        - 'data': A list of dictionaries containing the aggregated data for each conflict typology

    Note: The method uses OrderedDict and models from Django to perform the data processing and aggregation.

    Example Usage:
    report = get_report()  # get the report object
    result = report_stat_conflict_typology(report)  # analyze the conflict typologies in the report
    print(result)  # display the generated statistical report
    """
    headers = OrderedDict(dict(
        iso3='ISO3',
        name='IDMC short name',
        typology='Conflict typology',
        total='Figure',
    ))
    filtered_report_figures = report.report_figures.filter(
        role=Figure.ROLE.RECOMMENDED,
        event__event_type=Crisis.CRISIS_TYPE.CONFLICT,
        category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
    ).values('country').order_by()

    data = filtered_report_figures.filter(disaggregation_conflict__gt=0).annotate(
        name=F('country__idmc_short_name'),
        iso3=F('country__iso3'),
        total=Sum('disaggregation_conflict', filter=Q(disaggregation_conflict__gt=0)),
        typology=models.Value('Armed Conflict', output_field=models.CharField())
    ).values('name', 'iso3', 'total', 'typology').union(
        filtered_report_figures.filter(disaggregation_conflict_political__gt=0).annotate(
            name=F('country__idmc_short_name'),
            iso3=F('country__iso3'),
            total=Sum(
                'disaggregation_conflict_political',
                filter=Q(disaggregation_conflict_political__gt=0)
            ),
            typology=models.Value('Violence - Political', output_field=models.CharField())
        ).values('name', 'iso3', 'total', 'typology'),
        filtered_report_figures.filter(disaggregation_conflict_criminal__gt=0).annotate(
            name=F('country__idmc_short_name'),
            iso3=F('country__iso3'),
            total=Sum(
                'disaggregation_conflict_criminal',
                filter=Q(disaggregation_conflict_criminal__gt=0)
            ),
            typology=models.Value('Violence - Criminal', output_field=models.CharField())
        ).values('name', 'iso3', 'total', 'typology'),
        filtered_report_figures.filter(disaggregation_conflict_communal__gt=0).annotate(
            name=F('country__idmc_short_name'),
            iso3=F('country__iso3'),
            total=Sum(
                'disaggregation_conflict_communal',
                filter=Q(disaggregation_conflict_communal__gt=0)
            ),
            typology=models.Value('Violence - Communal', output_field=models.CharField())
        ).values('name', 'iso3', 'total', 'typology'),
        filtered_report_figures.filter(disaggregation_conflict_other__gt=0).annotate(
            name=F('country__idmc_short_name'),
            iso3=F('country__iso3'),
            total=Sum(
                'disaggregation_conflict_other',
                filter=Q(disaggregation_conflict_other__gt=0)
            ),
            typology=models.Value('Other', output_field=models.CharField())
        ).values('name', 'iso3', 'total', 'typology')
    ).values('name', 'iso3', 'typology', 'total').order_by('typology')

    # further aggregation
    aggregation_headers = OrderedDict(dict(
        typology='Conflict typology',
        total='Sum of figure',
    ))
    aggregation_formula = dict()

    filtered_report_figures = report.report_figures.filter(
        role=Figure.ROLE.RECOMMENDED,
        event__event_type=Crisis.CRISIS_TYPE.CONFLICT,
        category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
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

    return {
        'headers': headers,
        'data': data,
        'formulae': dict(),
        'aggregation': dict(
            headers=aggregation_headers,
            formulae=aggregation_formula,
            data=aggregation_data,
        )
    }


def report_disaster_event(report):
    """

    report_disaster_event(report)

    This method generates a report for a given disaster event.

    Parameters:
    - report: The report object for which the disaster event report needs to be generated.

    Returns:
    A dictionary containing the following keys:
    - 'headers': An ordered dictionary containing the column names and their corresponding display names for the report.
    - 'data': The data for the report in the form of a queryset.
    - 'formulae': A dictionary containing formulae used for calculations in the report.

    Example Usage:

        report = Report.objects.get(id=1)
        result = report_disaster_event(report)
        headers = result['headers']
        data = result['data']
        formulae = result['formulae']

    """
    headers = OrderedDict(dict(
        event_id='Event ID',
        event_name='Event name',
        event_year='Event year',
        event_start_date='Start date',
        event_end_date='End date',
        event_category='Hazard category',
        event_sub_category='Hazard sub category',
        dtype='Hazard type',
        dsub_type='Hazard sub type',
        affected_iso3='Affected ISO3',
        affected_names='Affected countries',
        affected_countries='Number of affected countries',
        flow_total='ND' + report.name,
    ))

    def get_key(header):
        return excel_column_key(headers, header)

    # NOTE: {{ }} turns into { } after the first .format
    global_filter = dict(
        role=Figure.ROLE.RECOMMENDED,
        event__event_type=Crisis.CRISIS_TYPE.DISASTER
    )

    data = report.report_figures.filter(
        **global_filter
    ).values('event').order_by().annotate(
        event_id=F('event_id'),
        event_name=F('event__name'),
        event_year=Extract('event__end_date', 'year'),
        event_start_date=F('event__start_date'),
        event_end_date=F('event__end_date'),
        event_category=F('event__disaster_category__name'),
        event_sub_category=F('event__disaster_sub_category__name'),
        dtype=F('event__disaster_type__name'),
        dsub_type=F('event__disaster_sub_type__name'),
        flow_total=Sum('total_figures', filter=Q(category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT)),
        affected_countries=Count('country', distinct=True),
        affected_iso3=StringAgg('country__iso3', EXTERNAL_ARRAY_SEPARATOR, distinct=True),
        affected_names=StringAgg('country__idmc_short_name', EXTERNAL_ARRAY_SEPARATOR, distinct=True),
    )
    return {
        'headers': headers,
        'data': data,
        'formulae': dict(),
    }


def report_disaster_country(report, include_history):
    """
    Reports the disaster data for each country.

    Parameters:
    - report (Report): The report object representing the dataset for the report.
    - include_history (bool): Flag indicating whether to include historical data.

    Returns:
    - dict: A dictionary containing the following keys:
            - 'headers': An ordered dictionary representing the headers of the data.
            - 'data': The queried data for each country.
            - 'formulae': A dictionary of formulas for calculated values.
            - 'aggregation': None (not used in this method).
    """
    headers = OrderedDict(dict(
        country_iso3='ISO3',
        country_name='Name',
        country_region='Region',
        events_count='Events count',
        country_population='Country population',
        flow_total=f'ND {report.name}',
        flow_total_last_year='ND last year',
        flow_historical_average='ND historical average',
    ))

    def get_key(header):
        return excel_column_key(headers, header)

    formulae = {
        'ND per 100k population': EXCEL_FORMULAE['per_100k'].format(
            key1=get_key('flow_total'), key2=get_key('country_population')
        ),
        'ND percent variation wrt last year':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('flow_total'), key2=get_key('flow_total_last_year')
        ),
        'ND percent variation wrt average':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('flow_total'), key2=get_key('flow_historical_average')
        ),
    }
    global_filter = dict(
        role=Figure.ROLE.RECOMMENDED,
        event__event_type=Crisis.CRISIS_TYPE.DISASTER,
    )
    data = report.report_figures.filter(
        **global_filter
    ).values('country').order_by().annotate(
        country_iso3=F('country__iso3'),
        country_name=F('country__idmc_short_name'),
        country_region=F('country__region__name'),
        events_count=Count('event', distinct=True),
        country_population=Subquery(
            CountryPopulation.objects.filter(
                year=int(report.filter_figure_start_after.year),
                country=OuterRef('country'),
            ).values('population')
        ),
        flow_total=Sum('total_figures', filter=Q(
            category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
            **global_filter
        )),
    )

    if is_grid_or_myu_report(report.filter_figure_start_after, report.filter_figure_end_before) and include_history:
        data = data.annotate(
            flow_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__gte=report.filter_figure_start_after - timedelta(days=365),
                    end_date__lte=report.filter_figure_end_before - timedelta(days=365),
                    country=OuterRef('country'),
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                    **global_filter
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            flow_historical_average=Subquery(
                Figure.objects.filter(
                    start_date__lt=report.filter_figure_start_after,
                    # only consider the figures in the given month range
                    start_date__month__gte=report.filter_figure_start_after.month,
                    end_date__month__lte=report.filter_figure_end_before.month,
                    country=OuterRef('country'),
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                    **global_filter
                ).annotate(
                    min_year=Min(Extract('start_date', 'year')),
                    max_year=Max(Extract('start_date', 'year')),
                ).annotate(
                    _total=Sum('total_figures') / (F('max_year') - F('min_year') + 1)
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
        )

    return {
        'headers': headers,
        'data': data,
        'formulae': formulae,
        'aggregation': None,
    }


def report_disaster_region(report, include_history):
    """
    Report disaster region.

    :param report: The report object.
    :param include_history: Whether to include historical data or not.

    :return: A dictionary containing headers, data, and formulae.
    """
    headers = OrderedDict(dict(
        region_name='Region',
        events_count='Events count',
        region_population='Region population',
        flow_total=f'ND {report.name}',
        flow_total_last_year='ND last year',
        flow_historical_average='ND historical average',
    ))

    def get_key(header):
        return excel_column_key(headers, header)

    formulae = {
        'ND per 100k population': EXCEL_FORMULAE['per_100k'].format(
            key1=get_key('flow_total'), key2=get_key('region_population')
        ),
        'ND percent variation wrt last year':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('flow_total'), key2=get_key('flow_total_last_year')
        ),
        'ND percent variation wrt average':
            EXCEL_FORMULAE['percent_variation'].format(
            key1=get_key('flow_total'), key2=get_key('flow_historical_average')
        ),
    }
    global_filter = dict(
        role=Figure.ROLE.RECOMMENDED,
        event__event_type=Crisis.CRISIS_TYPE.DISASTER,
    )
    data = report.report_figures.filter(
        **global_filter
    ).annotate(
        region=F('country__region')
    ).values('country__region').order_by().annotate(
        region_name=F('country__region__name'),
        country_region=F('country__region__name'),
        events_count=Count('event', distinct=True),
        region_population=Subquery(
            CountryPopulation.objects.filter(
                country__region=OuterRef('region'),
                year=int(report.filter_figure_start_after.year),
            ).annotate(
                total_population=Sum('population')
            ).values('total_population')[:1]
        ),
        flow_total=Sum('total_figures', filter=Q(
            category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
            **global_filter
        )),
    )

    if is_grid_or_myu_report(report.filter_figure_start_after, report.filter_figure_end_before) and include_history:
        data = data.annotate(
            flow_total_last_year=Subquery(
                Figure.objects.filter(
                    start_date__gte=report.filter_figure_start_after - timedelta(days=365),
                    end_date__lte=report.filter_figure_end_before - timedelta(days=365),
                    country__region=OuterRef('country__region'),
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                    **global_filter
                ).annotate(
                    _total=Sum('total_figures')
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
            flow_historical_average=Subquery(
                Figure.objects.filter(
                    start_date__lt=report.filter_figure_start_after,
                    # only consider the figures in the given month range
                    start_date__month__gte=report.filter_figure_start_after.month,
                    end_date__month__lte=report.filter_figure_end_before.month,
                    country__region=OuterRef('country__region'),
                    category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                    **global_filter
                ).annotate(
                    min_year=Min(Extract('start_date', 'year')),
                    max_year=Max(Extract('start_date', 'year')),
                ).annotate(
                    _total=Sum('total_figures') / (F('max_year') - F('min_year') + 1)
                ).values('_total').annotate(total=F('_total')).values('total')
            ),
        )

    return {
        'headers': headers,
        'data': data,
        'formulae': formulae,
    }


def report_get_excel_sheets_data(report, include_history=False):
    """
    Get the data for each sheet in the report Excel file.

    Parameters:
    - report (str): The path to the report Excel file.
    - include_history (bool, optional): Include historical data if True. Default is False.

    Returns:
    (dict): A dictionary containing the data for each sheet in the report Excel file.
    The keys are the sheet names and the values are the data specific to each sheet.

    Example usage:
    report = 'path/to/report.xlsx'
    data = report_get_excel_sheets_data(report, include_history=True)
    """
    return {
        'Global Numbers': report_global_numbers(report),
        'ND Country': report_stat_flow_country(report),
        'ND Region': report_stat_flow_region(report),
        'Conflict Country': report_stat_conflict_country(report, include_history),
        'Conflict Region': report_stat_conflict_region(report, include_history),
        'Conflict Typology': report_stat_conflict_typology(report),
        'Disaster Event': report_disaster_event(report),
        'Disaster Country': report_disaster_country(report, include_history),
        'Disaster Region': report_disaster_region(report, include_history)
    }

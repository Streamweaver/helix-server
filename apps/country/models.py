import typing
from datetime import datetime

from collections import OrderedDict
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.aggregates.general import StringAgg
from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Count, OuterRef, Subquery
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django_enumfield import enum

from apps.contrib.models import MetaInformationArchiveAbstractModel, ArchiveAbstractModel, MetaInformationAbstractModel
from apps.entry.models import Entry, Figure
from apps.crisis.models import Crisis
from apps.users.models import User, Portfolio
from apps.users.enums import USER_ROLE
from apps.common.utils import EXTERNAL_ARRAY_SEPARATOR, EXTERNAL_TUPLE_SEPARATOR
from utils.fields import generate_full_media_url


class GeographicalGroup(models.Model):
    """
    GeographicalGroup

    This class represents a geographical group.

    Attributes:
        name (str): The name of the geographical group.

    Methods:
        __str__()
            Returns the name of the geographical group as a string.

    """
    name = models.CharField(verbose_name=_('Name'), max_length=256)

    def __str__(self):
        return self.name


class CountryRegion(models.Model):
    """
    Class representing a CountryRegion.

    Attributes:
        ND_CONFLICT_ANNOTATE (str): The annotation for total flow conflict figures.
        ND_DISASTER_ANNOTATE (str): The annotation for total flow disaster figures.
        IDP_CONFLICT_ANNOTATE (str): The annotation for total stock conflict figures.
        IDP_DISASTER_ANNOTATE (str): The annotation for total stock disaster figures.
        name (CharField): The name of the country region.

    Methods:
        _total_figure_disaggregation_subquery(figures=None, ignore_dates=False): Returns the subqueries
            for figure sum annotations.
        __str__(): Returns the string representation of the CountryRegion.

    """
    # NOTE: following are the figure disaggregation fields
    ND_CONFLICT_ANNOTATE = 'total_flow_conflict'
    ND_DISASTER_ANNOTATE = 'total_flow_disaster'
    IDP_CONFLICT_ANNOTATE = 'total_stock_conflict'
    IDP_DISASTER_ANNOTATE = 'total_stock_disaster'

    name = models.CharField(verbose_name=_('Name'), max_length=256)

    @classmethod
    def _total_figure_disaggregation_subquery(
        cls,
        figures=None,
        ignore_dates=False,
    ):
        '''
        returns the subqueries for figures sum annotations
        '''
        figures = figures or Figure.objects.all()
        if ignore_dates:
            start_date = None
            end_date = None
        else:
            now = timezone.now()
            start_date = datetime(year=now.year, month=1, day=1)
            end_date = now.date()

        return {
            cls.ND_CONFLICT_ANNOTATE: models.Subquery(
                Figure.filtered_nd_figures(
                    figures.filter(
                        country__region=OuterRef('pk'),
                        role=Figure.ROLE.RECOMMENDED,
                        event__event_type=Crisis.CRISIS_TYPE.CONFLICT,
                    ),
                    # TODO: what about date range
                    start_date=start_date,
                    end_date=end_date
                ).order_by().values('country__region').annotate(
                    _total=models.Sum('total_figures')
                ).values('_total')[:1],
                output_field=models.IntegerField()
            ),
            cls.ND_DISASTER_ANNOTATE: models.Subquery(
                Figure.filtered_nd_figures(
                    figures.filter(
                        country__region=OuterRef('pk'),
                        role=Figure.ROLE.RECOMMENDED,
                        event__event_type=Crisis.CRISIS_TYPE.DISASTER,
                    ),
                    # TODO: what about date range
                    start_date=start_date,
                    end_date=end_date,
                ).order_by().values('country__region').annotate(
                    _total=models.Sum('total_figures')
                ).values('_total')[:1],
                output_field=models.IntegerField()
            ),
            cls.IDP_CONFLICT_ANNOTATE: models.Subquery(
                Figure.filtered_idp_figures(
                    figures.filter(
                        country__region=OuterRef('pk'),
                        role=Figure.ROLE.RECOMMENDED,
                        event__event_type=Crisis.CRISIS_TYPE.CONFLICT,
                    ),
                    start_date=start_date,
                    end_date=end_date,
                ).order_by().values('country__region').annotate(
                    _total=models.Sum('total_figures')
                ).values('_total')[:1],
                output_field=models.IntegerField()
            ),
            cls.IDP_DISASTER_ANNOTATE: models.Subquery(
                Figure.filtered_idp_figures(
                    figures.filter(
                        country__region=OuterRef('pk'),
                        role=Figure.ROLE.RECOMMENDED,
                        event__event_type=Crisis.CRISIS_TYPE.DISASTER,
                    ),
                    start_date=start_date,
                    end_date=end_date,
                ).order_by().values('country__region').annotate(
                    _total=models.Sum('total_figures')
                ).values('_total')[:1],
                output_field=models.IntegerField()
            ),
        }

    def __str__(self):
        return self.name


class MonitoringSubRegion(models.Model):
    """

    MonitoringSubRegion class

    This class represents a monitoring sub-region. It contains methods and properties related to monitoring data for the sub-region.

    Attributes:
        name (str): The name of the monitoring sub-region.
        countries (models.QuerySet['Country']): QuerySet of countries within the sub-region.

    Methods:
        get_excel_sheets_data(user_id, filters)
            Retrieves Excel sheets data for the monitoring sub-region.

            Parameters:
                user_id (int): The ID of the user.
                filters (dict): Filters for retrieving data.

            Returns:
                dict: A dictionary containing the headers, data, formulae, and transformer for the Excel sheets.

    Properties:
        unmonitored_countries_count (int): The number of unmonitored countries within the sub-region.
        unmonitored_countries_names (str): The names of unmonitored countries within the sub-region.
        regional_coordinator (typing.Optional[Portfolio]): The portfolio of the regional coordinator for the sub-region.
        monitoring_experts_count (int): The number of monitoring experts within the sub-region.

    """
    name = models.CharField(verbose_name=_('Name'), max_length=256)

    countries: models.QuerySet['Country']

    @classmethod
    def get_excel_sheets_data(cls, user_id, filters):
        class DummyRequest:
            def __init__(self, user):
                self.user = user

        headers = OrderedDict(
            id='Region ID',
            country__monitoring_sub_region__name='Region name',
            regional_coordinator='Regional coordinator',
            user__full_name='Monitoring expert',
            countries_count='No. of countries',
            monitored_countries='Countries',
            monitored_iso3='ISO3',
        )

        portfolios = Portfolio.objects.filter(
            role=USER_ROLE.MONITORING_EXPERT
        ).values(
            'user__full_name',
            'country__monitoring_sub_region__name',
        ).order_by(
            'country__monitoring_sub_region__name',
            'user__full_name',
        ).annotate(
            id=models.F('country__monitoring_sub_region__id'),
            monitored_countries=StringAgg(
                'country__idmc_short_name',
                EXTERNAL_ARRAY_SEPARATOR,
            ),
            monitored_iso3=StringAgg(
                'country__iso3',
                EXTERNAL_ARRAY_SEPARATOR,
            ),
            countries_count=Count('country'),
            regional_coordinator=Subquery(
                Portfolio.objects.filter(
                    role=USER_ROLE.REGIONAL_COORDINATOR,
                    monitoring_sub_region=models.OuterRef('country__monitoring_sub_region'),
                ).values('monitoring_sub_region').annotate(
                    user_full_names=StringAgg(
                        'user__full_name',
                        EXTERNAL_TUPLE_SEPARATOR,
                    ),
                ).values('user_full_names')[:1],
            ),
        )

        return {
            'headers': headers,
            'data': portfolios.values(*[header for header in headers.keys()]),
            'formulae': None,
            'transformer': None,
        }

    @property
    def unmonitored_countries_count(self) -> int:
        country_portfolios = Portfolio.objects.filter(
            role=USER_ROLE.MONITORING_EXPERT,
            country__isnull=False,
        ).values_list('country')
        q = self.countries.filter(
            ~models.Q(id__in=country_portfolios)
        )
        return q.count()

    @property
    def unmonitored_countries_names(self) -> str:
        country_portfolios = Portfolio.objects.filter(
            role=USER_ROLE.MONITORING_EXPERT,
            country__isnull=False,
        ).values_list('country')
        q = self.countries.filter(
            ~models.Q(id__in=country_portfolios)
        )
        return EXTERNAL_ARRAY_SEPARATOR.join(q.values_list('idmc_short_name', flat=True))

    @property
    def regional_coordinator(self) -> typing.Optional[Portfolio]:
        if Portfolio.objects.filter(monitoring_sub_region=self,
                                    role=USER_ROLE.REGIONAL_COORDINATOR).exists():
            return Portfolio.objects.get(monitoring_sub_region=self,
                                         role=USER_ROLE.REGIONAL_COORDINATOR)

    @property
    def monitoring_experts_count(self) -> int:
        return Portfolio.objects.filter(
            monitoring_sub_region=self,
            role=USER_ROLE.MONITORING_EXPERT,
        ).values('user').distinct().count()

    def __str__(self):
        return self.name


class CountrySubRegion(models.Model):
    """
    Class representing a country subregion.

    Attributes:
        name (str): The name of the subregion.

    Methods:
        __str__(): Returns a string representation of the subregion.
    """
    name = models.CharField(verbose_name=_('Name'), max_length=256)

    def __str__(self):
        return self.name


class Country(models.Model):
    """
    :class:`Country`

    Model representing a country.

    Attributes:
        GEOJSON_PATH (str): The path to the directory containing the geojson files.
        ND_CONFLICT_ANNOTATE (str): The field name for the total flow conflict figure.
        ND_DISASTER_ANNOTATE (str): The field name for the total flow disaster figure.
        IDP_CONFLICT_ANNOTATE (str): The field name for the total stock conflict figure.
        IDP_DISASTER_ANNOTATE (str): The field name for the total stock disaster figure.
        name (str): The name of the country.
        geographical_group (`GeographicalGroup`): The geographical group of the country.
        region (`CountryRegion`): The region of the country.
        sub_region (`CountrySubRegion`): The sub region of the country.
        monitoring_sub_region (`MonitoringSubRegion`): The monitoring sub region of the country.
        iso2 (str): The ISO2 code of the country.
        iso3 (str): The ISO3 code of the country.
        country_code (int): The country code.
        idmc_short_name (str): The IDMC short name of the country.
        idmc_full_name (str): The IDMC full name of the country.
        centroid (list[float]): The centroid of the country.
        bounding_box (list[float]): The bounding box of the country.
        idmc_short_name_es (str): The IDMC short name in Spanish.
        idmc_short_name_fr (str): The IDMC short name in French.
        idmc_short_name_ar (str): The IDMC short name in Arabic.
        contextual_analyses (`QuerySet['ContextualAnalysis']`): The queryset of contextual analyses associated with the country.
        summaries (`QuerySet['Summary']`): The queryset of summaries associated with the country.
    """
    GEOJSON_PATH = 'geojsons'
    # NOTE: following are the figure disaggregation fields
    ND_CONFLICT_ANNOTATE = 'total_flow_conflict'
    ND_DISASTER_ANNOTATE = 'total_flow_disaster'
    IDP_CONFLICT_ANNOTATE = 'total_stock_conflict'
    IDP_DISASTER_ANNOTATE = 'total_stock_disaster'

    name = models.CharField(verbose_name=_('Name'), max_length=256)
    geographical_group = models.ForeignKey('GeographicalGroup', verbose_name=_('Geographical Group'), null=True,
                                           on_delete=models.SET_NULL)
    region = models.ForeignKey('CountryRegion', verbose_name=_('Region'),
                               related_name='countries', on_delete=models.PROTECT)
    sub_region = models.ForeignKey('CountrySubRegion', verbose_name=_('Sub Region'), null=True,
                                   related_name='countries', on_delete=models.PROTECT)
    monitoring_sub_region = models.ForeignKey('MonitoringSubRegion', verbose_name=_('Monitoring Sub-Region'), null=True,
                                              related_name='countries', on_delete=models.PROTECT)

    iso2 = models.CharField(verbose_name=_('ISO2'), max_length=4,
                            null=True, blank=True)
    iso3 = models.CharField(verbose_name=_('ISO3'), max_length=5,
                            null=True, blank=True)
    country_code = models.PositiveSmallIntegerField(verbose_name=_('Country Code'), null=True, blank=False)
    idmc_short_name = models.CharField(
        verbose_name=_('IDMC Short Name'),
        max_length=256,
        blank=False
    )
    idmc_full_name = models.CharField(verbose_name=_('IDMC Full Name'), max_length=256, null=True, blank=False)
    centroid = ArrayField(verbose_name=_('Centroid'), base_field=models.FloatField(blank=False), null=True)
    bounding_box = ArrayField(verbose_name=_('Bounding Box'),
                              base_field=models.FloatField(blank=False), null=True)
    idmc_short_name_es = models.CharField(verbose_name=_('IDMC Short Name Es'), max_length=256, null=True)
    idmc_short_name_fr = models.CharField(verbose_name=_('IDMC Short Name Fr'), max_length=256, null=True)
    idmc_short_name_ar = models.CharField(verbose_name=_('IDMC Short Name Ar'), max_length=256, null=True)

    contextual_analyses: models.QuerySet['ContextualAnalysis']
    summaries: models.QuerySet['Summary']

    @classmethod
    def _total_figure_disaggregation_subquery(
        cls,
        figures=None,
        ignore_dates=False,
        start_date=None,
        end_date=None,
        year=None
    ):
        '''
        returns the subqueries for figures sum annotations
        '''
        if figures is None:
            figures = Figure.objects.all()
        if start_date is None and end_date is None:
            if year:
                start_date = datetime(year=int(year), month=1, day=1)
                end_date = datetime(year=int(year), month=12, day=31)
            else:
                start_date = datetime(year=timezone.now().year, month=1, day=1)
                end_date = datetime(year=timezone.now().year, month=12, day=31)
        if ignore_dates:
            start_date = None
            end_date = None

        return {
            cls.ND_CONFLICT_ANNOTATE: models.Subquery(
                Figure.filtered_nd_figures(
                    figures.filter(
                        country=OuterRef('pk'),
                        role=Figure.ROLE.RECOMMENDED,
                        event__event_type=Crisis.CRISIS_TYPE.CONFLICT,
                    ),
                    # TODO: what about date range
                    start_date=start_date,
                    end_date=end_date
                ).order_by().values('country').annotate(
                    _total=models.Sum('total_figures')
                ).values('_total')[:1],
                output_field=models.IntegerField()
            ),
            cls.ND_DISASTER_ANNOTATE: models.Subquery(
                Figure.filtered_nd_figures(
                    figures.filter(
                        country=OuterRef('pk'),
                        role=Figure.ROLE.RECOMMENDED,
                        event__event_type=Crisis.CRISIS_TYPE.DISASTER,
                    ),
                    # TODO: what about date range
                    start_date=start_date,
                    end_date=end_date,
                ).order_by().values('country').annotate(
                    _total=models.Sum('total_figures')
                ).values('_total')[:1],
                output_field=models.IntegerField()
            ),
            cls.IDP_CONFLICT_ANNOTATE: models.Subquery(
                Figure.filtered_idp_figures(
                    figures.filter(
                        country=OuterRef('pk'),
                        role=Figure.ROLE.RECOMMENDED,
                        event__event_type=Crisis.CRISIS_TYPE.CONFLICT,
                    ),
                    start_date=start_date,
                    end_date=end_date,
                ).order_by().values('country').annotate(
                    _total=models.Sum('total_figures')
                ).values('_total')[:1],
                output_field=models.IntegerField()
            ),
            cls.IDP_DISASTER_ANNOTATE: models.Subquery(
                Figure.filtered_idp_figures(
                    figures.filter(
                        country=OuterRef('pk'),
                        role=Figure.ROLE.RECOMMENDED,
                        event__event_type=Crisis.CRISIS_TYPE.DISASTER,
                    ),
                    start_date=start_date,
                    end_date=end_date,
                ).order_by().values('country').annotate(
                    _total=models.Sum('total_figures')
                ).values('_total')[:1],
                output_field=models.IntegerField()
            ),
        }

    @classmethod
    def get_excel_sheets_data(cls, user_id, filters):
        from apps.country.filters import CountryFilter

        class DummyRequest:
            def __init__(self, user):
                self.user = user

        str_year = filters.get('year', '')
        headers = OrderedDict(
            id='ID',
            geographical_group__name='Geographical group',
            region__name='Region',
            sub_region__name='Sub region',
            name='Name',
            iso2='ISO2',
            iso3='ISO3',
            country_code='Country code',
            idmc_short_name='IDMC short name',
            idmc_full_name='IDMC full name',
            crises_count='Crises count',
            events_count='Events count',
            entries_count='Entries count',
            figures_count='Figures count',
            **{
                cls.IDP_DISASTER_ANNOTATE: f'IDPs disaster figure {str_year}',
                cls.ND_CONFLICT_ANNOTATE: f'ND conflict figure {str_year}',
                cls.IDP_CONFLICT_ANNOTATE: f'IDPs conflict figure {str_year}',
                cls.ND_DISASTER_ANNOTATE: f'ND disaster figure {str_year}',
            }
        )
        data = CountryFilter(
            data=filters,
            request=DummyRequest(user=User.objects.get(id=user_id)),
        ).qs.annotate(
            crises_count=Count('crises', distinct=True),
            events_count=Count('events', distinct=True),
            # NOTE: Subquery was relatively faster than JOINs
            # entries_count=Count('events__entries', distinct=True),
            entries_count=models.Subquery(
                Entry.objects.filter(
                    figures__country=OuterRef('pk')
                ).order_by().values('figures__country').annotate(
                    _count=Count('figures__entry', distinct=True)
                ).values('_count')[:1],
                output_field=models.IntegerField()
            ),
            figures_count=models.Subquery(
                Figure.objects.filter(
                    country=OuterRef('pk')
                ).order_by().values('country').annotate(
                    _count=Count('pk')
                ).values('_count')[:1],
                output_field=models.IntegerField()
            ),
            # contacts_count=Count('contacts', distinct=True),
            # operating_contacts_count=Count('operating_contacts', distinct=True),
        ).order_by('idmc_short_name')

        return {
            'headers': headers,
            'data': data.values(*[header for header in headers.keys()]),
            'formulae': None,
            'transformer': None,
        }

    @classmethod
    def geojson_path(cls, iso3):
        if iso3:
            return f'{cls.GEOJSON_PATH}/{iso3.upper()}.json'

    @classmethod
    def geojson_url(cls, iso3):
        if iso3:
            file_path = f'{cls.GEOJSON_PATH}/{iso3.upper()}.json'
            return generate_full_media_url(file_path)

    @property
    def entries(self) -> QuerySet:
        return Entry.objects.filter(figures__event__countries=self.pk).distinct()

    @property
    def last_contextual_analysis(self):
        return self.contextual_analyses.last()

    @property
    def regional_coordinator(self) -> Portfolio:
        return self.monitoring_sub_region.regional_coordinator

    @property
    def monitoring_expert(self) -> typing.Optional[Portfolio]:
        return Portfolio.objects.filter(
            country=self,
            role=USER_ROLE.MONITORING_EXPERT,
        ).first()

    @property
    def last_summary(self):
        return self.summaries.last()

    def __str__(self):
        return self.name


class CountryPopulation(models.Model):
    """

    The `CountryPopulation` model represents the population data of a country for a specific year.

    Attributes:
        - country (ForeignKey): Represents the country associated with the population data.
        - population (PositiveIntegerField): Represents the population value.
        - year (PositiveIntegerField): Represents the year for which the population data is recorded.

    Meta:
        - unique_together: Specifies that the combination of `country` and `year` should be unique.

    """
    country = models.ForeignKey('Country', verbose_name=_('Country'),
                                related_name='populations', on_delete=models.CASCADE)
    population = models.PositiveIntegerField('Population')
    year = models.PositiveIntegerField('Year',
                                       validators=[
                                           MinValueValidator(1800, 'The date is invalid.'),
                                           MaxValueValidator(9999, 'The date is invalid.'),
                                       ])

    class Meta:
        unique_together = (('country', 'year'),)


class ContextualAnalysis(MetaInformationArchiveAbstractModel, models.Model):
    """
    ContextualAnalysis class represents an analysis of a specific context in relation to a country.

    Attributes:
        country (ForeignKey): A foreign key to the Country model representing the country associated with the analysis.
        update (TextField): A text field storing the analysis update.
        publish_date (DateField): A field representing the date when the analysis was published. Can be blank and null.
        crisis_type (EnumField): An enum field representing the type of crisis associated with the analysis. Can be blank and null.

    """
    country = models.ForeignKey('Country', verbose_name=_('Country'),
                                on_delete=models.CASCADE, related_name='contextual_analyses')
    update = models.TextField(verbose_name=_('Update'), blank=False)
    publish_date = models.DateField(verbose_name=_('Published Date'),
                                    blank=True,
                                    null=True)
    crisis_type = enum.EnumField(Crisis.CRISIS_TYPE,
                                 verbose_name=_('Cause'),
                                 blank=True,
                                 null=True)


class Summary(MetaInformationArchiveAbstractModel, models.Model):
    """
    A model for storing summary information related to a country.

    Attributes:
        country (ForeignKey): The country associated with the summary.
        summary (TextField): The summary text. Cannot be blank.
    """
    country = models.ForeignKey('Country', verbose_name=_('Country'),
                                on_delete=models.CASCADE, related_name='summaries')
    summary = models.TextField(verbose_name=_('Summary'), blank=False)


class HouseholdSize(ArchiveAbstractModel, MetaInformationAbstractModel):
    """
    Class representing the household size for a specific country and year.

    Attributes:
        country (ForeignKey): Foreign key to the Country model representing the country associated with the household size.
        year (PositiveSmallIntegerField): The year for which the household size is recorded.
        size (FloatField): The size of the household.
        data_source_category (CharField): The category of the data source.
        source (CharField): The source of the data.
        source_link (CharField): The link to the source of the data.
        notes (TextField): Additional notes regarding the household size.
        is_active (BooleanField): Indicates if the household size is currently active.
        country_id (int): The ID of the country associated with the household size.

    Methods:
        __str__(): Returns a string representation of the HouseholdSize instance.

    """
    country = models.ForeignKey('Country',
                                related_name='household_sizes', on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(verbose_name=_('Year'))
    size = models.FloatField(verbose_name=_('Size'), default=1.0,
                             validators=[
                                 MinValueValidator(0, message="Should be positive")])

    data_source_category = models.CharField(verbose_name=_('Data Source Category'), max_length=255)
    source = models.CharField(verbose_name=_('Source'), max_length=255)
    source_link = models.CharField(verbose_name=_('Source Link'), max_length=255)
    notes = models.TextField(verbose_name=_('Notes'), blank=True, null=True)
    is_active = models.BooleanField(
        verbose_name=_('Is active?'),
        default=False
    )

    country_id: int

    def __str__(self):
        return f'PK:{self.pk}-Country-ID:{self.country_id}-Year:{self.year}'

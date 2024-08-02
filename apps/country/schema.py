import graphene
from graphene.types.utils import get_type
from graphene_django import DjangoObjectType
from graphene_django_extras import (
    DjangoObjectField,
)
from utils.graphene.enums import EnumDescription

from apps.contact.schema import ContactListType
from apps.country.models import (
    Country,
    CountryRegion,
    CountrySubRegion,
    MonitoringSubRegion,
    ContextualAnalysis,
    Summary,
    HouseholdSize,
    GeographicalGroup,
)
from apps.country.filters import (
    CountryFilter,
    CountryRegionFilter,
    GeographicalGroupFilter,
    MonitoringSubRegionFilter,
    ContextualAnalysisFilter,
    CountrySummaryFilter,
)
from apps.crisis.enums import CrisisTypeGrapheneEnum
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount


class MonitoringSubRegionType(DjangoObjectType):
    """
    Class representing a Monitoring SubRegion Type.

    Attributes:
        model (Model): The model class for the Monitoring SubRegion.
        exclude_fields (tuple): A tuple of fields to be excluded from the GraphQL schema.

    Methods:
        countries: A dynamic method that returns a list of CountryType objects.
        regional_coordinator: Returns the PortfolioType object representing the regional coordinator.
        monitoring_experts_count: Returns the count of monitoring experts.
        unmonitored_countries_count: Returns the count of unmonitored countries.
        unmonitored_countries_names: Returns a string representing the names of unmonitored countries.
        countries_count: Returns the count of countries in the subregion.

    Usage:
        Use this class to define a Monitoring SubRegion GraphQL ObjectType in your schema.
    """
    class Meta:
        model = MonitoringSubRegion
        exclude_fields = ('portfolios',)

    countries = graphene.Dynamic(
        lambda: graphene.List(
            graphene.NonNull(get_type('apps.country.schema.CountryType'))
        )
    )
    # TODO: Add dataloaders
    regional_coordinator = graphene.Field('apps.users.schema.PortfolioType')
    monitoring_experts_count = graphene.Int(required=True)
    unmonitored_countries_count = graphene.Int(required=True)
    unmonitored_countries_names = graphene.String(required=True)
    countries_count = graphene.Int(required=True)

    def resolve_countries_count(root, info, **kwargs):
        return info.context.monitoring_sub_region_country_count_loader.load(root.id)

    def resolve_countries(root, info, **kwargs):
        return info.context.monitoring_sub_region_country_loader.load(root.id)


class MonitoringSubRegionListType(CustomDjangoListObjectType):
    """
    A class representing a list of monitoring sub-regions.

    Parameters:
        CustomDjangoListObjectType (class): Parent class providing Django model-based list object functionality.

    Attributes:
        Meta (class): Inner class defining additional metadata for the MonitoringSubRegionListType class.
            model (class): The Django model associated with the monitoring sub-regions.
            filterset_class (class): The filterset class used for filtering the monitoring sub-regions.

    """
    class Meta:
        model = MonitoringSubRegion
        filterset_class = MonitoringSubRegionFilter


class CountrySubRegionType(DjangoObjectType):
    """
    A GraphQL Object Type representing a country subregion.

    This class is a subclass of `DjangoObjectType`, which is a type defined by the Django Graphene library for working
    with Django models in GraphQL.

    Attributes:
        model (django.db.models.Model): The Django model representing the country subregion.

    Example usage:
        country_subregion = CountrySubRegionType()

        # Access the data fields of a country subregion object
        country_subregion.id
        country_subregion.name
        country_subregion.code
        country_subregion.region
        country_subregion.countries

    Note:
        This class does not include example code as requested.
    """
    class Meta:
        model = CountrySubRegion


class CountryRegionType(DjangoObjectType):
    """
    The `CountryRegionType` class is a DjangoObjectType subclass that represents the GraphQL object type for the
    `CountryRegion` model.

    Attributes:
        Meta (object): A nested class that contains the metadata about the `CountryRegionType` class. It specifies the
        `CountryRegion` model as the source of data for this GraphQL object type.

    """
    class Meta:
        model = CountryRegion


class CountryRegionListType(CustomDjangoListObjectType):
    """

    """
    class Meta:
        model = CountryRegion
        filterset_class = CountryRegionFilter


class GeographicalGroupType(DjangoObjectType):
    """
    A DjangoObjectType class representing a geographical group.

    Attributes:
        model (Django Model): The Django Model that represents a geographical group.
    """
    class Meta:
        model = GeographicalGroup


class GeographicalGroupListType(CustomDjangoListObjectType):
    """
    A class representing a list of geographical groups.

    This class inherits from CustomDjangoListObjectType, which is a custom Django type for creating list objects.

    Attributes:
        model: The model associated with the geographical group list.
        filterset_class: The filterset class used for filtering the geographical group list.

    """
    class Meta:
        model = GeographicalGroup
        filterset_class = GeographicalGroupFilter


class ContextualAnalysisType(DjangoObjectType):
    """

    ContextualAnalysisType

    A class representing the GraphQL ObjectType for the ContextualAnalysis model in Django.

    Attributes:
        Meta: A nested class that holds metadata information for the ObjectType.
            - model: The model class to be used for the ObjectType.
            - exclude_fields: A tuple of fields to be excluded from the ObjectType.
        created_by: A field representing the creator of the ContextualAnalysis.
        last_modified_by: A field representing the last user who modified the ContextualAnalysis.
        crisis_type: A field representing the crisis type of the ContextualAnalysis.
        crisis_type_display: A field representing the display value of the crisis type.

    """
    class Meta:
        model = ContextualAnalysis
        exclude_fields = ('country',)

    created_by = graphene.Field('apps.users.schema.UserType')
    last_modified_by = graphene.Field('apps.users.schema.UserType')
    crisis_type = graphene.Field(CrisisTypeGrapheneEnum)
    crisis_type_display = EnumDescription(source='get_crisis_type_display')


class ContextualAnalysisListType(CustomDjangoListObjectType):
    """
    Class: ContextualAnalysisListType

    Inherits From: CustomDjangoListObjectType

    Description:
    This class represents a GraphQL list type for ContextualAnalysis objects. It provides the necessary fields and
    filters to perform contextual analysis queries.

    Attributes:
    - model (class): The Django model associated with the list type.
    - filterset_class (class): The filterset class used to filter the list of ContextualAnalysis objects.

    Example Usage:
    contextual_analysis_list = ContextualAnalysisListType()
    """
    class Meta:
        model = ContextualAnalysis
        filterset_class = ContextualAnalysisFilter


class SummaryType(DjangoObjectType):
    """
    A class representing a summary type in the application.

    Attributes:
        model (class): The model class representing the summary type.
        exclude_fields (tuple): A tuple of fields to be excluded from the summary type.

        last_modified_by (graphene.Field): A field representing the user who last modified the summary.
        created_by (graphene.Field): A field representing the user who created the summary.

    """
    class Meta:
        model = Summary
        exclude_fields = ('country',)

    last_modified_by = graphene.Field('apps.users.schema.UserType')
    created_by = graphene.Field('apps.users.schema.UserType')


class SummaryListType(CustomDjangoListObjectType):
    """
    A class representing a custom Django list object type for summaries.

    This class extends the `CustomDjangoListObjectType` class and provides functionality related to summaries.

    Attributes:
        Meta: A nested class defining metadata for the `SummaryListType` class.
              It specifies the model to use and the filterset class to apply.

    """
    class Meta:
        model = Summary
        filterset_class = CountrySummaryFilter


class CountryType(DjangoObjectType):
    """
    The CountryType class is a DjangoObjectType that represents a country.

    Attributes:
        model (Class): The model class for the country.
        exclude_fields (Tuple): A tuple of fields to exclude from the GraphQL schema.

    Fields:
        last_summary (graphene.Field): A field representing the last summary of the country.
        last_contextual_analysis (graphene.Field): A field representing the last contextual analysis of the country.
        contacts (DjangoPaginatedListObjectField): A field representing a paginated list of contacts related to the
        country.
        operating_contacts (DjangoPaginatedListObjectField): A field representing a paginated list of operating contacts
        related to the country.
        contextual_analyses (DjangoPaginatedListObjectField): A field representing a paginated list of contextual
        analyses related to the country.
        summaries (DjangoPaginatedListObjectField): A field representing a paginated list of summaries related to the
        country.
        crises (graphene.Dynamic): A field representing a dynamic paginated list of crises related to the country.
        events (graphene.Dynamic): A field representing a dynamic paginated list of events related to the country.
        entries (graphene.Dynamic): A field representing a dynamic paginated list of entries related to the country.
        figures (graphene.Dynamic): A field representing a dynamic paginated list of figures related to the country.
        total_flow_conflict (graphene.Int): A field representing the total flow of conflict-related issues in the
        country.
        total_flow_disaster (graphene.Int): A field representing the total flow of disaster-related issues in the
        country.
        total_stock_conflict (graphene.Int): A field representing the total stock of conflict-related issues in the
        country.
        total_stock_disaster (graphene.Int): A field representing the total stock of disaster-related issues in the
        country.
        geojson_url (graphene.String): A field representing the URL for the geojson of the country.
        regional_coordinator (graphene.Field): A field representing the regional coordinator of the country.
        monitoring_expert (graphene.Field): A field representing the monitoring expert of the country.

    Methods:
        resolve_total_stock_disaster(root, info, **kwargs): A method that resolves the total stock of disaster-related
        issues in the country.
        resolve_total_stock_conflict(root, info, **kwargs): A method that resolves the total stock of conflict-related
        issues in the country.
        resolve_total_flow_conflict(root, info, **kwargs): A method that resolves the total flow of conflict-related
        issues in the country.
        resolve_total_flow_disaster(root, info, **kwargs): A method that resolves the total flow of disaster-related
        issues in the country.
        resolve_geojson_url(root, info, **kwargs): A method that resolves the URL for the geojson of the country.
    """
    class Meta:
        model = Country
        exclude_fields = ('country_conflict', 'country_disaster', 'displacements')

    last_summary = graphene.Field(SummaryType)
    last_contextual_analysis = graphene.Field(ContextualAnalysisType)
    contacts = DjangoPaginatedListObjectField(
        ContactListType,
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
        related_name='contacts',
        reverse_related_name='country',
    )
    operating_contacts = DjangoPaginatedListObjectField(
        ContactListType,
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
        related_name='operating_contacts',
        reverse_related_name='countries_of_operation',
    )
    contextual_analyses = DjangoPaginatedListObjectField(
        ContextualAnalysisListType,
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
    )
    summaries = DjangoPaginatedListObjectField(
        SummaryListType,
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
    )
    crises = graphene.Dynamic(lambda: DjangoPaginatedListObjectField(
        get_type('apps.crisis.schema.CrisisListType'),
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
        related_name='crises',
    ))
    events = graphene.Dynamic(lambda: DjangoPaginatedListObjectField(
        get_type('apps.event.schema.EventListType'),
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
        related_name='events',
    ))
    entries = graphene.Dynamic(lambda: DjangoPaginatedListObjectField(
        get_type('apps.entry.schema.EntryListType'),
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
        accessor='entries',
    ))
    figures = graphene.Dynamic(lambda: DjangoPaginatedListObjectField(
        get_type('apps.entry.schema.FigureListType'),
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
        accessor='figures'
    ))
    total_flow_conflict = graphene.Int()
    total_flow_disaster = graphene.Int()
    total_stock_conflict = graphene.Int()
    total_stock_disaster = graphene.Int()
    geojson_url = graphene.String()

    regional_coordinator = graphene.Field('apps.users.schema.PortfolioType')
    monitoring_expert = graphene.Field('apps.users.schema.PortfolioType')

    def resolve_total_stock_disaster(root, info, **kwargs):
        NULL = 'null'
        value = getattr(
            root,
            Country.IDP_DISASTER_ANNOTATE,
            NULL
        )
        if value != NULL:
            return value
        return info.context.country_country_this_year_idps_disaster_loader.load(root.id)

    def resolve_total_stock_conflict(root, info, **kwargs):
        NULL = 'null'
        value = getattr(
            root,
            Country.IDP_CONFLICT_ANNOTATE,
            NULL
        )
        if value != NULL:
            return value
        return info.context.country_country_this_year_idps_conflict_loader.load(root.id)

    def resolve_total_flow_conflict(root, info, **kwargs):
        NULL = 'null'
        value = getattr(
            root,
            Country.ND_CONFLICT_ANNOTATE,
            NULL
        )
        if value != NULL:
            return value
        return info.context.country_country_this_year_nd_conflict_loader.load(root.id)

    def resolve_total_flow_disaster(root, info, **kwargs):
        NULL = 'null'
        value = getattr(
            root,
            Country.ND_DISASTER_ANNOTATE,
            NULL
        )
        if value != NULL:
            return value
        return info.context.country_country_this_year_nd_disaster_loader.load(root.id)

    def resolve_geojson_url(root, info, **kwargs):
        return info.context.request.build_absolute_uri(Country.geojson_url(root.iso3))


class CountryListType(CustomDjangoListObjectType):
    """
    A custom class for handling a list of Country objects. Inherits from CustomDjangoListObjectType.

    Attributes:
        model: The model class used for the list.
        filterset_class: The filterset class used for filtering the list.

    """
    class Meta:
        model = Country
        filterset_class = CountryFilter


class CountryHouseholdSizeType(DjangoObjectType):
    """

    class CountryHouseholdSizeType(DjangoObjectType):
        A GraphQL type that represents the household size for a country.

        This class defines a GraphQL type using DjangoObjectType. It represents the household size for a specific
        country.

        Attributes:
            model (Model): The Django model that this GraphQL type references.

        """
    class Meta:
        model = HouseholdSize


class Query:
    """
    Class Query
    ------------
    This class handles GraphQL queries related to countries, geographical groups, and household sizes.

    Attributes:
    -----------
    country: DjangoObjectField
        A DjangoObjectField representing a country.

    country_list: DjangoPaginatedListObjectField
        A DjangoPaginatedListObjectField representing a paginated list of countries.

    country_region_list: DjangoPaginatedListObjectField
        A DjangoPaginatedListObjectField representing a paginated list of country regions.

    geographical_group_list: DjangoPaginatedListObjectField
        A DjangoPaginatedListObjectField representing a paginated list of geographical groups.

    household_size: graphene.Field
        A graphene.Field representing household size related to a country and year.

    monitoring_sub_region: DjangoObjectField
        A DjangoObjectField representing a monitoring sub-region.

    monitoring_sub_region_list: DjangoPaginatedListObjectField
        A DjangoPaginatedListObjectField representing a paginated list of monitoring sub-regions.

    Methods:
    --------
    resolve_household_size(root, info, country, year)
        Resolves the query for household size based on the provided country and year.

    """
    country = DjangoObjectField(CountryType)
    country_list = DjangoPaginatedListObjectField(CountryListType,
                                                  pagination=PageGraphqlPaginationWithoutCount(
                                                      page_size_query_param='pageSize'
                                                  ))
    country_region_list = DjangoPaginatedListObjectField(CountryRegionListType)
    geographical_group_list = DjangoPaginatedListObjectField(GeographicalGroupListType)
    household_size = graphene.Field(CountryHouseholdSizeType,
                                    country=graphene.ID(required=True),
                                    year=graphene.Int(required=True))
    monitoring_sub_region = DjangoObjectField(MonitoringSubRegionType)
    monitoring_sub_region_list = DjangoPaginatedListObjectField(MonitoringSubRegionListType,
                                                                pagination=PageGraphqlPaginationWithoutCount(
                                                                    page_size_query_param='pageSize'
                                                                ))

    def resolve_household_size(root, info, country, year):
        try:
            # TODO: Update this query to support dynamic filtering of HouseholdSize in the future
            return HouseholdSize.objects.filter(country=country, year=year, is_active=True).order_by('modified_at').first()
        except HouseholdSize.DoesNotExist:
            return None

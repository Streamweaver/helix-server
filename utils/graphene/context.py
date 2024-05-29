from django.utils.functional import cached_property

from apps.country.dataloaders import (
    TotalFigureThisYearByCountryCategoryEventTypeLoader,
    MonitoringSubRegionCountryLoader,
    MonitoringSubRegionCountryCountLoader,
)
from apps.crisis.dataloaders import (
    TotalIDPFigureByCrisisLoader,
    TotalNDFigureByCrisisLoader,
    EventCountLoader,
    CrisisReviewCountLoader,
    MaxStockIDPFigureEndDateByCrisisLoader,
)
from apps.entry.dataloaders import (
    TotalIDPFigureByEntryLoader,
    TotalNDFigureByEntryLoader,
    FigureTypologyLoader,
    FigureGeoLocationLoader,
    FigureSourcesReliability,
    FigureLastReviewCommentStatusLoader,
    FigureEntryLoader,
    EntryDocumentLoader,
    EntryPreviewLoader,
)
from apps.contrib.dataloaders import (
    BulkApiOperationFailureListLoader,
    BulkApiOperationSuccessListLoader,
)
from apps.event.dataloaders import (
    TotalIDPFigureByEventLoader,
    TotalNDFigureByEventLoader,
    MaxStockIDPFigureEndDateByEventLoader,
    EventEntryCountLoader,
    EventTypologyLoader,
    EventFigureTypologyLoader,
    EventReviewCountLoader,
    EventCodeLoader,
    EventCrisisLoader,
)
from utils.graphene.dataloaders import OneToManyLoader, CountLoader
from apps.entry.models import Figure
from apps.users.dataloaders import UserPortfoliosMetadataLoader
from apps.organization.dataloaders import OrganizationCountriesLoader, OrganizationOrganizationKindLoader


class GQLContext:
    """


    GQLContext

    This class is used to manage the GraphQL context for each request.

    Attributes:
        request (HttpRequest): The request object for the current request.
        one_to_many_dataloaders (dict): A dictionary to store OneToManyLoader objects for different references.
        count_dataloaders (dict): A dictionary to store CountLoader objects for different references.

    Methods:
        user(): Returns the user object associated with the current request.
        get_dataloader(parent: str, related_name: str): Returns a OneToManyLoader object for the given parent and related name.
        get_count_loader(parent: str, child: str): Returns a CountLoader object for the given parent and child.
        entry_entry_total_stock_idp_figures(): Returns a TotalIDPFigureByEntryLoader object.
        entry_entry_total_flow_nd_figures(): Returns a TotalNDFigureByEntryLoader object.
        crisis_crisis_total_stock_idp_figures(): Returns a TotalIDPFigureByCrisisLoader object.
        crisis_crisis_total_flow_nd_figures(): Returns a TotalNDFigureByCrisisLoader object.
        crisis_stock_idp_figures_max_end_date(): Returns a MaxStockIDPFigureEndDateByCrisisLoader object.
        event_event_total_stock_idp_figures(): Returns a TotalIDPFigureByEventLoader object.
        event_event_total_flow_nd_figures(): Returns a TotalNDFigureByEventLoader object.
        event_stock_idp_figures_max_end_date(): Returns a MaxStockIDPFigureEndDateByEventLoader object.
        country_country_this_year_idps_disaster_loader(): Returns a TotalFigureThisYearByCountryCategoryEventTypeLoader object for IDPs in disaster.
        country_country_this_year_idps_conflict_loader(): Returns a TotalFigureThisYearByCountryCategoryEventTypeLoader object for IDPs in conflict.
        country_country_this_year_nd_conflict_loader(): Returns a TotalFigureThisYearByCountryCategoryEventTypeLoader object for new displacements in conflict.
        country_country_this_year_nd_disaster_loader(): Returns a TotalFigureThisYearByCountryCategoryEventTypeLoader object for new displacements in disaster.
        monitoring_sub_region_country_loader(): Returns a MonitoringSubRegionCountryLoader object.
        monitoring_sub_region_country_count_loader(): Returns a MonitoringSubRegionCountryCountLoader object.
        event_entry_count_dataloader(): Returns an EventEntryCountLoader object.
        event_typology_dataloader(): Returns an EventTypologyLoader object.
        event_figure_typology_dataloader(): Returns an EventFigureTypologyLoader object.
        figure_typology_dataloader(): Returns a FigureTypologyLoader object.
        figure_geolocations_loader(): Returns a FigureGeoLocationLoader object.
        figure_sources_reliability_loader(): Returns a FigureSourcesReliability object.
        last_review_comment_status_loader(): Returns a FigureLastReviewCommentStatusLoader object.
        event_count_dataloader(): Returns an EventCountLoader object.
        event_review_count_dataloader(): Returns an EventReviewCountLoader object.
        crisis_review_count_dataloader(): Returns a CrisisReviewCountLoader object.
        event_code_loader(): Returns an EventCodeLoader object.
        bulk_api_operation_success_list_loader(): Returns a BulkApiOperationSuccessListLoader object.
        bulk_api_operation_failure_list_loader(): Returns a BulkApiOperationFailureListLoader object.
        event_crisis_loader(): Returns an EventCrisisLoader object.
        figure_entry_loader(): Returns a FigureEntryLoader object.
        entry_document_loader(): Returns an EntryDocumentLoader object.
        organization_countries_loader(): Returns an OrganizationCountriesLoader object.
        organization_organization_kind_loader(): Returns an OrganizationOrganizationKindLoader object.
        entry_preview_loader(): Returns an EntryPreviewLoader object.
        user_portfolios_metadata(): Returns a UserPortfoliosMetadataLoader object.
    """
    def __init__(self, request):
        self.request = request
        # global dataloaders
        self.one_to_many_dataloaders = {}
        self.count_dataloaders = {}

    @cached_property
    def user(self):
        return self.request.user

    def get_dataloader(self, parent: str, related_name: str):
        # TODO: rename to get OneToManyLoader?
        # returns a different dataloader for each ref
        ref = f'{parent}_{related_name}'
        if ref not in self.one_to_many_dataloaders:
            self.one_to_many_dataloaders[ref] = OneToManyLoader()
        return self.one_to_many_dataloaders[ref]

    def get_count_loader(self, parent: str, child: str):
        ref = f'{parent}_{child}'
        if ref not in self.count_dataloaders:
            self.count_dataloaders[ref] = CountLoader()
        return self.count_dataloaders[ref]

    '''
    NOTE: As a convention, data loader should have the name as:
    AppName_NodeType_FieldName
    '''

    @cached_property
    def entry_entry_total_stock_idp_figures(self):
        return TotalIDPFigureByEntryLoader()

    @cached_property
    def entry_entry_total_flow_nd_figures(self):
        return TotalNDFigureByEntryLoader()

    @cached_property
    def crisis_crisis_total_stock_idp_figures(self):
        return TotalIDPFigureByCrisisLoader()

    @cached_property
    def crisis_crisis_total_flow_nd_figures(self):
        return TotalNDFigureByCrisisLoader()

    @cached_property
    def crisis_stock_idp_figures_max_end_date(self):
        return MaxStockIDPFigureEndDateByCrisisLoader()

    @cached_property
    def event_event_total_stock_idp_figures(self):
        return TotalIDPFigureByEventLoader()

    @cached_property
    def event_event_total_flow_nd_figures(self):
        return TotalNDFigureByEventLoader()

    @cached_property
    def event_stock_idp_figures_max_end_date(self):
        return MaxStockIDPFigureEndDateByEventLoader()

    @cached_property
    def country_country_this_year_idps_disaster_loader(self):
        from apps.crisis.models import Crisis
        return TotalFigureThisYearByCountryCategoryEventTypeLoader(
            category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
            event_type=Crisis.CRISIS_TYPE.DISASTER.value,
        )

    @cached_property
    def country_country_this_year_idps_conflict_loader(self):
        from apps.crisis.models import Crisis
        return TotalFigureThisYearByCountryCategoryEventTypeLoader(
            category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
            event_type=Crisis.CRISIS_TYPE.CONFLICT.value,
        )

    @cached_property
    def country_country_this_year_nd_conflict_loader(self):
        from apps.crisis.models import Crisis
        return TotalFigureThisYearByCountryCategoryEventTypeLoader(
            category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
            event_type=Crisis.CRISIS_TYPE.CONFLICT.value,
        )

    @cached_property
    def country_country_this_year_nd_disaster_loader(self):
        from apps.crisis.models import Crisis
        return TotalFigureThisYearByCountryCategoryEventTypeLoader(
            category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
            event_type=Crisis.CRISIS_TYPE.DISASTER.value,
        )

    @cached_property
    def monitoring_sub_region_country_loader(self):
        return MonitoringSubRegionCountryLoader()

    @cached_property
    def monitoring_sub_region_country_count_loader(self):
        return MonitoringSubRegionCountryCountLoader()

    @cached_property
    def event_entry_count_dataloader(self):
        return EventEntryCountLoader()

    @cached_property
    def event_typology_dataloader(self):
        return EventTypologyLoader()

    @cached_property
    def event_figure_typology_dataloader(self):
        return EventFigureTypologyLoader()

    @cached_property
    def figure_typology_dataloader(self):
        return FigureTypologyLoader()

    @cached_property
    def figure_geolocations_loader(self):
        return FigureGeoLocationLoader()

    @cached_property
    def figure_sources_reliability_loader(self):
        return FigureSourcesReliability()

    @cached_property
    def last_review_comment_status_loader(self):
        return FigureLastReviewCommentStatusLoader()

    @cached_property
    def event_count_dataloader(self):
        return EventCountLoader()

    @cached_property
    def event_review_count_dataloader(self):
        return EventReviewCountLoader()

    @cached_property
    def crisis_review_count_dataloader(self):
        return CrisisReviewCountLoader()

    @cached_property
    def event_code_loader(self):
        return EventCodeLoader()

    @cached_property
    def bulk_api_operation_success_list_loader(self):
        return BulkApiOperationSuccessListLoader()

    @cached_property
    def bulk_api_operation_failure_list_loader(self):
        return BulkApiOperationFailureListLoader()

    @cached_property
    def event_crisis_loader(self):
        return EventCrisisLoader()

    @cached_property
    def figure_entry_loader(self):
        return FigureEntryLoader()

    @cached_property
    def entry_document_loader(self):
        return EntryDocumentLoader()

    @cached_property
    def organization_countries_loader(self):
        return OrganizationCountriesLoader()

    @cached_property
    def organization_organization_kind_loader(self):
        return OrganizationOrganizationKindLoader()

    @cached_property
    def entry_preview_loader(self):
        return EntryPreviewLoader()

    @cached_property
    def user_portfolios_metadata(self):
        return UserPortfoliosMetadataLoader()

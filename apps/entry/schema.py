import graphene
from django.db.models import fields, JSONField, Sum, Case, When, ExpressionWrapper, Q
from django.db.models.functions import ExtractYear
from graphene import ObjectType
from graphene.types.generic import GenericScalar
from graphene_django import DjangoObjectType
from graphene_django_extras.converter import convert_django_field
from graphene_django_extras import DjangoObjectField
import logging
from utils.graphene.enums import EnumDescription

from apps.entry.enums import (
    GenderTypeGrapheneEnum,
    QuantifierGrapheneEnum,
    UnitGrapheneEnum,
    RoleGrapheneEnum,
    DisplacementOccurredGrapheneEnum,
    OSMAccuracyGrapheneEnum,
    IdentifierGrapheneEnum,
    FigureCategoryTypeEnum,
    FigureTermsEnum,
    FigureSourcesReliabilityEnum,
    FigureReviewStatusEnum,
)
from apps.entry.filters import (
    OSMNameFilter,
    DisaggregatedAgeFilter,
    FigureFilter,
    FigureTagFilter,
)
from apps.entry.models import (
    Figure,
    FigureTag,
    Entry,
    OSMName,
    DisaggregatedAge,
)
from apps.contrib.models import SourcePreview
from apps.contrib.enums import PreviewStatusGrapheneEnum
from apps.contrib.commons import DateAccuracyGrapheneEnum
from apps.organization.schema import OrganizationListType
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount
from apps.extraction.filters import (
    FigureExtractionFilterSet,
    ReportFigureExtractionFilterSet,
    FigureExtractionFilterDataInputType,
    EntryExtractionFilterSet,
)
from apps.crisis.enums import CrisisTypeGrapheneEnum
from apps.crisis.models import Crisis
from apps.event.schema import OtherSubTypeObjectType, EventType
from apps.review.enums import ReviewCommentTypeEnum, ReviewFieldTypeEnum

logger = logging.getLogger(__name__)


@convert_django_field.register(JSONField)
def convert_json_field_to_scalar(field, registry=None):
    """
    Convert a JSONField to a Scalar field in GraphQL.

    This method is used to convert a JSONField from Django models to a Scalar field in GraphQL.
    It is registered as a converter for JSONField type in the graphene-django library.

    Parameters:
    - field (JSONField): The JSONField to be converted.
    - registry (Registry): The registry used for field conversions (default: None).

    Returns:
    - GenericScalar: The converted Scalar field.

    Example:
    @convert_django_field.register(JSONField)
    def convert_json_field_to_scalar(field, registry=None):
        return GenericScalar()
    """
    # https://github.com/graphql-python/graphene-django/issues/303#issuecomment-339939955
    return GenericScalar()


class DisaggregatedAgeType(DjangoObjectType):
    """

    Class: DisaggregatedAgeType
    ----------------------------

    A class representing the DisaggregatedAgeType in the system.


    Attributes:
    -----------

    - uuid (str): The unique identifier of the DisaggregatedAgeType object.
    - age_from (int): The starting age of the DisaggregatedAgeType.
    - age_to (int): The ending age of the DisaggregatedAgeType.
    - sex (GenderTypeGrapheneEnum): The gender of the DisaggregatedAgeType.
    - sex_display (str): The display value of the gender of the DisaggregatedAgeType.


    Methods:
    --------

    None


    """
    class Meta:
        model = DisaggregatedAge
    uuid = graphene.String(required=True)
    age_from = graphene.Field(graphene.Int)
    age_to = graphene.Field(graphene.Int)
    sex = graphene.Field(GenderTypeGrapheneEnum)
    sex_display = EnumDescription(source='get_sex_display')


class DisaggregatedAgeListType(CustomDjangoListObjectType):
    """
    Class representing a DisaggregatedAgeListType.

    Inherits from CustomDjangoListObjectType.

    Attributes:
        Meta (class): Meta information for the DisaggregatedAgeListType.

    """
    class Meta:
        model = DisaggregatedAge
        filterset_class = DisaggregatedAgeFilter


class DisaggregatedStratumType(ObjectType):
    """

    Class to represent a type of disaggregated stratum.

    Attributes:
        uuid (str): The UUID of the stratum type.
        date (str): The date of the stratum.
        value (int): The value of the stratum.

    """
    uuid = graphene.String(required=True)
    date = graphene.String()  # because inside the json field
    value = graphene.Int()


class OSMNameType(DjangoObjectType):
    """

    This class, OSMNameType, is a subclass of DjangoObjectType. It is used to define the GraphQL type for OSMName model.

    Attributes:
        - model (Class): The Django model associated with the GraphQL type.

        - accuracy (Field): A graphene Field representing the accuracy of the OSMName.

        - accuracy_display (EnumDescription): An EnumDescription object that provides a source for displaying the accuracy enum value.

        - identifier (Field): A graphene Field representing the identifier of the OSMName.

        - identifier_display (EnumDescription): An EnumDescription object that provides a source for displaying the identifier enum value.

    """
    class Meta:
        model = OSMName

    accuracy = graphene.Field(OSMAccuracyGrapheneEnum)
    accuracy_display = EnumDescription(source='get_accuracy_display')
    identifier = graphene.Field(IdentifierGrapheneEnum)
    identifier_display = EnumDescription(source='get_identifier_display')


class OSMNameListType(CustomDjangoListObjectType):
    """

    OSMNameListType is a class that extends CustomDjangoListObjectType and represents a list of OSMName objects.

    Attributes:
        model (Model): The Django model associated with this list.
        filterset_class (FilterSet): The filter class used for filtering the list.

    """
    class Meta:
        model = OSMName
        filterset_class = OSMNameFilter


class FigureTagType(DjangoObjectType):
    """

    Class: FigureTagType

    A class that represents the Figure tag type.

    Attributes:
    - model (Class): The Django model for the Figure tag type.

    """
    class Meta:
        model = FigureTag


class FigureLastReviewCommentStatusType(ObjectType):
    """
    Represents the type of last review comment for a figure.

    Attributes:
        id (ID): The ID of the FigureLastReviewCommentStatusType.
        field (ReviewFieldTypeEnum): The field associated with the last review comment.
        comment_type (ReviewCommentTypeEnum): The type of the last review comment.

    """
    id = graphene.ID(required=True)
    field = graphene.Field(ReviewFieldTypeEnum, required=True)
    comment_type = graphene.Field(ReviewCommentTypeEnum, required=True)


class FigureType(DjangoObjectType):
    """
    Class: FigureType

    A class representing a GraphQL object type for Figure.

    Attributes:
    - exclude_fields: A tuple of fields to be excluded from the GraphQL object type.
    - model: The model class associated with the FigureType.

    Methods:
    - quantifier: A field representing the quantifier of the figure.
    - get_quantifier: A field description for the quantifier.
    - unit: A field representing the unit of measurement for the figure.
    - unit_display: A field description for the unit of measurement.
    - role: A field representing the role of the figure.
    - role_display: A field description for the figure's role.
    - displacement_occurred: A field representing whether displacement has occurred.
    - displacement_occurred_display: A field description for displacement occurred.
    - disaggregation_age: A field representing the disaggregation age of the figure.
    - disaggregation_strata_json: A list of disaggregated stratum types.
    - geo_locations: A field representing the geographical locations associated with the figure.
    - start_date_accuracy: A field representing the accuracy of the start date.
    - start_date_accuracy_display: A field description for the start date accuracy.
    - end_date_accuracy: A field representing the accuracy of the end date.
    - end_date_accuracy_display: A field description for the end date accuracy.
    - category: A field representing the category type of the figure.
    - category_display: A field description for the category type.
    - term: A field representing the terms of the figure.
    - term_display: A field description for the terms.
    - figure_cause: A field representing the cause of the figure.
    - figure_cause_display: A field description for the figure's cause.
    - other_sub_type: A field representing the other sub type of the figure.
    - figure_typology: A string representing the typology of the figure.
    - sources: A field representing the sources associated with the figure.
    - stock_date: A field representing the stock date of the figure.
    - stock_reporting_date: A field representing the stock reporting date of the figure.
    - flow_start_date: A field representing the flow start date of the figure.
    - flow_end_date: A field representing the flow end date of the figure.
    - geolocations: A string representing the geolocations of the figure.
    - sources_reliability: A field representing the reliability of the figure's sources.
    - review_status: A field representing the review status of the figure.
    - review_status_display: A field description for the review status.
    - last_review_comment_status: A list of last review comment statuses associated with the figure.
    - event: A field representing the event associated with the figure.
    - event_id: The ID of the event associated with the figure.
    - entry: A field representing the entry associated with the figure.
    - entry_id: The ID of the entry associated with the figure.

    Methods:
    - resolve_stock_date: Resolves the stock date of the figure.
    - resolve_stock_reporting_date: Resolves the stock reporting date of the figure.
    - resolve_flow_start_date: Resolves the flow start date of the figure.
    - resolve_flow_end_date: Resolves the flow end date of the figure.
    - resolve_figure_typology: Resolves the typology of the figure.
    - resolve_geolocations: Resolves the geolocations of the figure.
    - resolve_sources_reliability: Resolves the reliability of the figure's sources.
    - resolve_last_review_comment_status: Resolves the last review comment statuses of the figure.
    - resolve_entry: Resolves the entry associated with the figure.
    """
    class Meta:
        exclude_fields = (
            'figure_reviews',
        )
        model = Figure

    quantifier = graphene.Field(QuantifierGrapheneEnum)
    get_quantifier = EnumDescription(source='get_quantifier_display')
    unit = graphene.Field(UnitGrapheneEnum)
    unit_display = EnumDescription(source='get_unit_display')
    role = graphene.Field(RoleGrapheneEnum)
    role_display = EnumDescription(source='get_role_display')
    displacement_occurred = graphene.Field(DisplacementOccurredGrapheneEnum)
    displacement_occurred_display = EnumDescription(source='get_displacement_occurred_display')
    disaggregation_age = DjangoPaginatedListObjectField(
        DisaggregatedAgeListType,
        related_name="disaggregation_age"
    )
    disaggregation_strata_json = graphene.List(graphene.NonNull(DisaggregatedStratumType))
    geo_locations = DjangoPaginatedListObjectField(
        OSMNameListType,
        related_name='geo_locations',
    )
    start_date_accuracy = graphene.Field(DateAccuracyGrapheneEnum)
    start_date_accuracy_display = EnumDescription(source='get_start_date_accuracy_display')
    end_date_accuracy = graphene.Field(DateAccuracyGrapheneEnum)
    end_date_accuracy_display = EnumDescription(source='get_end_date_accuracy_display')
    category = graphene.Field(FigureCategoryTypeEnum)
    category_display = EnumDescription(source='get_category_display')
    term = graphene.Field(FigureTermsEnum)
    term_display = EnumDescription(source='get_term_display')
    figure_cause = graphene.Field(CrisisTypeGrapheneEnum)
    figure_cause_display = EnumDescription(source='get_figure_cause_display')
    other_sub_type = graphene.Field(OtherSubTypeObjectType)
    figure_typology = graphene.String()
    sources = DjangoPaginatedListObjectField(
        OrganizationListType,
        related_name='sources',
        reverse_related_name='sourced_figures'
    )
    stock_date = graphene.Date()
    stock_reporting_date = graphene.Date()
    flow_start_date = graphene.Date()
    flow_end_date = graphene.Date()
    geolocations = graphene.String()
    sources_reliability = graphene.Field(FigureSourcesReliabilityEnum)
    review_status = graphene.Field(FigureReviewStatusEnum)
    review_status_display = EnumDescription(source='get_review_status_display')
    last_review_comment_status = graphene.List(graphene.NonNull(FigureLastReviewCommentStatusType))
    event = graphene.Field(EventType, required=True)
    event_id = graphene.ID(required=True, source='event_id')
    entry = graphene.Field("apps.entry.schema.EntryType", required=True)
    entry_id = graphene.ID(required=True, source='entry_id')

    def resolve_stock_date(root, info, **kwargs):
        if root.category in Figure.stock_list():
            return root.start_date

    def resolve_stock_reporting_date(root, info, **kwargs):
        if root.category in Figure.stock_list():
            return root.end_date

    def resolve_flow_start_date(root, info, **kwargs):
        if root.category in Figure.flow_list():
            return root.start_date

    def resolve_flow_end_date(root, info, **kwargs):
        if root.category in Figure.flow_list():
            return root.end_date

    def resolve_figure_typology(root, info, **kwargs):
        return info.context.figure_typology_dataloader.load(root.id)

    def resolve_geolocations(root, info, **kwargs):
        return info.context.figure_geolocations_loader.load(root.id)

    def resolve_sources_reliability(root, info, **kwargs):
        return info.context.figure_sources_reliability_loader.load(root.id)

    def resolve_last_review_comment_status(root, info, **kwargs):
        return info.context.last_review_comment_status_loader.load(root.id)

    def resolve_entry(root, info, **kwargs):
        return info.context.figure_entry_loader.load(root.id)


class FigureListType(CustomDjangoListObjectType):
    """

    FigureListType - Custom Django List Object Type for Figure Model

    This class extends the CustomDjangoListObjectType class and is used to represent a list of Figure objects in the Django application.

    Attributes:
        model (Figure): The model class representing the Figure object in the Django application.
        filterset_class (FigureFilter): The filterset class to be used for filtering the list of Figure objects.

    """
    class Meta:
        model = Figure
        filterset_class = FigureFilter


class TotalFigureFilterInputType(graphene.InputObjectType):
    """
    TotalFigureFilterInputType class represents the input type for filtering figures based on various criteria.

    Attributes:
        categories (List[str]): A list of categories to filter figures by.
        filter_figure_start_after (Date): A date object representing the start date to filter figures after.
        filter_figure_end_before (Date): A date object representing the end date to filter figures before.
        roles (List[str]): A list of roles to filter figures by.

    """
    categories = graphene.List(graphene.NonNull(graphene.String))
    filter_figure_start_after = graphene.Date()
    filter_figure_end_before = graphene.Date()
    roles = graphene.List(graphene.NonNull(graphene.String))


class EntryType(DjangoObjectType):
    """

    This class represents an EntryType, which is a subclass of DjangoObjectType. It is used to define the fields and behaviors of an Entry object in the system.

    Attributes:
        - created_by (graphene.Field): A field representing the creator of the entry.
        - last_modified_by (graphene.Field): A field representing the user who last modified the entry.
        - publishers (DjangoPaginatedListObjectField): A field representing the publishers of the entry.
        - figures (graphene.List): A list of FigureType objects associated with the entry.
        - preview (graphene.Field): A field representing the preview of the entry.

    Methods:
        - resolve_figures: A method used to resolve the figures field. It retrieves the figures related to the entry and selects the related fields using a filter and select_related and prefetch_related methods.
        - resolve_document: A method used to resolve the document field. It uses a DataLoader to load the document associated with the entry.
        - resolve_preview: A method used to resolve the preview field. It uses a DataLoader to load the preview associated with the entry.

    Note: The exclude_fields attribute in the Meta class excludes certain fields from the Entry model when creating the EntryType. These fields are 'reviewers', 'review_status', 'review_comments', and 'reviewing'.

    """
    class Meta:
        model = Entry
        exclude_fields = (
            'reviewers',
            'review_status',
            'review_comments',
            'reviewing',
        )

    created_by = graphene.Field('apps.users.schema.UserType')
    last_modified_by = graphene.Field('apps.users.schema.UserType')
    publishers = DjangoPaginatedListObjectField(
        OrganizationListType,
        related_name='publishers',
        reverse_related_name='published_entries'
    )
    figures = graphene.List(graphene.NonNull(FigureType))
    preview = graphene.Field("apps.entry.schema.SourcePreviewType")

    def resolve_figures(root, info, **kwargs):
        # FIXME: this might be wrong
        return Figure.objects.filter(entry=root.id).select_related(
            'event',
            'violence',
            'violence_sub_type',
            'disaster_category',
            'disaster_sub_category',
            'disaster_type',
            'disaster_sub_type',
            'disaster_category',
            'disaster_sub_category',
            'other_sub_type',
            'osv_sub_type',
            'approved_by',
            'country',
            'event__disaster_category',
            'event__disaster_sub_category',
            'event__disaster_type',
            'event__disaster_sub_type',
            'event__disaster_category',
        ).prefetch_related(
            'tags',
            'context_of_violence',
            'geo_locations',
            'event__disaster_sub_category',
            'event__countries',
            'event__context_of_violence',
            'sources',
            'sources__countries',
            'sources__organization_kind',
        )

    def resolve_document(root, info, **kwargs):
        return info.context.entry_document_loader.load(root.id)

    def resolve_preview(root, info, **kwargs):
        return info.context.entry_preview_loader.load(root.id)


class EntryListType(CustomDjangoListObjectType):
    """
    Class EntryListType

    A custom Django list object type for querying and filtering Entry objects.

    Attributes:
        model (Model): The Entry model associated with this list type.
        filterset_class (FilterSet): The filter set class used for filtering the entries.

    """
    class Meta:
        model = Entry
        filterset_class = EntryExtractionFilterSet


class SourcePreviewType(DjangoObjectType):
    """
    A class representing a GraphQL object type for SourcePreview.

    Attributes:
        - status: A graphene Field representing the status of the preview.
        - status_display: A graphene Field representing the display value of the status.

    Methods:
        - resolve_pdf: A method that resolves the PDF property of the SourcePreview.

    """
    class Meta:
        model = SourcePreview
        exclude_fields = ('entry', 'token')

    status = graphene.Field(PreviewStatusGrapheneEnum)
    status_display = EnumDescription(source='get_status_display')

    def resolve_pdf(root, info, **kwargs):
        if root.status == SourcePreview.PREVIEW_STATUS.COMPLETED:
            return info.context.request.build_absolute_uri(root.pdf.url)
        return None


class VisualizationValueType(ObjectType):
    """
    This class represents a visualization value type.

    Attributes:
        date (Date): The date corresponding to the value.
        value (Int): The value of the visualization.

    """
    date = graphene.Date(required=True)
    value = graphene.Int(required=True)


class VisualizationFigureType(ObjectType):
    """

    Class: VisualizationFigureType
    Inherits from: ObjectType

    Description: This class represents a type of visualization figure.

    Attributes:
    - idps_conflict_figures: A list of non-null VisualizationValueType objects representing figures related to IDPs and conflicts.
    - idps_disaster_figures: A list of non-null VisualizationValueType objects representing figures related to IDPs and disasters.
    - nds_conflict_figures: A list of non-null VisualizationValueType objects representing figures related to NDS and conflicts.
    - nds_disaster_figures: A list of non-null VisualizationValueType objects representing figures related to NDS and disasters.

    """
    idps_conflict_figures = graphene.List(graphene.NonNull(VisualizationValueType))
    idps_disaster_figures = graphene.List(graphene.NonNull(VisualizationValueType))
    nds_conflict_figures = graphene.List(graphene.NonNull(VisualizationValueType))
    nds_disaster_figures = graphene.List(graphene.NonNull(VisualizationValueType))


class FigureTagListType(CustomDjangoListObjectType):
    """
    A custom class for managing a list of FigureTag objects.

    Inherits from CustomDjangoListObjectType.

    Attributes:
        model (Model): The model associated with the FigureTag list.
        filterset_class (FilterSet): The filterset class used for filtering the FigureTag list.

    """
    class Meta:
        model = FigureTag
        filterset_class = FigureTagFilter


class Query:
    """
    Class Query

    This class is responsible for defining the GraphQL queries and their resolvers.

    Attributes:
    - figure_tag (DjangoObjectField): A field to retrieve a single FigureTag object.
    - figure_tag_list (DjangoPaginatedListObjectField): A paginated list field to retrieve a list of FigureTag objects.
    - figure (DjangoObjectField): A field to retrieve a single Figure object.
    - figure_list (DjangoPaginatedListObjectField): A paginated list field to retrieve a list of Figure objects.
    - source_preview (DjangoObjectField): A field to retrieve a single SourcePreview object.
    - entry (DjangoObjectField): A field to retrieve a single Entry object.
    - entry_list (DjangoPaginatedListObjectField): A paginated list field to retrieve a list of Entry objects.
    - disaggregated_age (DjangoObjectField): A field to retrieve a single DisaggregatedAge object.
    - figure_aggregations (graphene.Field): A field to retrieve different types of aggregated figures based on filters.

    Methods:
    - resolve_figure_aggregations: A static method that resolves the figure_aggregations field by filtering and aggregating figure data.

    """
    figure_tag = DjangoObjectField(FigureTagType)
    figure_tag_list = DjangoPaginatedListObjectField(FigureTagListType,
                                                     pagination=PageGraphqlPaginationWithoutCount(
                                                         page_size_query_param='pageSize'
                                                     ))

    figure = DjangoObjectField(FigureType)
    figure_list = DjangoPaginatedListObjectField(FigureListType,
                                                 pagination=PageGraphqlPaginationWithoutCount(
                                                     page_size_query_param='pageSize',
                                                 ), filterset_class=FigureExtractionFilterSet)
    source_preview = DjangoObjectField(SourcePreviewType)
    entry = DjangoObjectField(EntryType)
    entry_list = DjangoPaginatedListObjectField(EntryListType,
                                                pagination=PageGraphqlPaginationWithoutCount(
                                                    page_size_query_param='pageSize'
                                                ))
    disaggregated_age = DjangoObjectField(DisaggregatedAgeType)
    figure_aggregations = graphene.Field(
        VisualizationFigureType,
        filters=FigureExtractionFilterDataInputType(required=True),
    )

    @staticmethod
    def resolve_figure_aggregations(_, info, filters):
        def _filter_nd_same_or_multiple_year_figures(qs, figure_cause):
            qs = qs.annotate(
                # NOTE: Once we upgrade django, let's rewrite this without two different annotations
                year_difference=ExpressionWrapper(
                    ExtractYear('end_date') - ExtractYear('start_date'),
                    output_field=fields.IntegerField()
                ),
                canonical_date=Case(
                    When(
                        Q(year_difference__gt=0),
                        then='end_date',
                    ),
                    default='start_date',
                ),
            )

            return qs.filter(
                category=Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT,
                role=Figure.ROLE.RECOMMENDED,
                figure_cause=figure_cause,
            ).values('canonical_date').annotate(value=Sum('total_figures'))

        figure_qs = ReportFigureExtractionFilterSet(data=filters).qs

        idps_conflict_figure_qs = figure_qs.filter(
            category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
            role=Figure.ROLE.RECOMMENDED,
            figure_cause=Crisis.CRISIS_TYPE.CONFLICT
        ).values('end_date').annotate(value=Sum('total_figures'))

        idps_disaster_figure_qs = figure_qs.filter(
            category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
            role=Figure.ROLE.RECOMMENDED,
            figure_cause=Crisis.CRISIS_TYPE.DISASTER
        ).values('end_date').annotate(value=Sum('total_figures'))

        nds_conflict_figure_qs = _filter_nd_same_or_multiple_year_figures(
            figure_qs,
            figure_cause=Crisis.CRISIS_TYPE.CONFLICT
        )

        nds_disaster_figure_qs = _filter_nd_same_or_multiple_year_figures(
            figure_qs,
            figure_cause=Crisis.CRISIS_TYPE.DISASTER
        )

        return VisualizationFigureType(
            idps_conflict_figures=[
                VisualizationValueType(
                    date=k['end_date'],
                    value=k['value']
                ) for k in idps_conflict_figure_qs
            ],
            idps_disaster_figures=[
                VisualizationValueType(
                    date=k['end_date'],
                    value=k['value']
                ) for k in idps_disaster_figure_qs
            ],
            nds_conflict_figures=[
                VisualizationValueType(
                    date=k['canonical_date'],
                    value=k['value']
                ) for k in nds_conflict_figure_qs
            ],
            nds_disaster_figures=[
                VisualizationValueType(
                    date=k['canonical_date'],
                    value=k['value']
                ) for k in nds_disaster_figure_qs
            ]

        )

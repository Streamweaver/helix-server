import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from utils.graphene.enums import EnumDescription

from apps.crisis.enums import CrisisTypeGrapheneEnum
from apps.crisis.filters import CrisisFilter
from apps.crisis.models import Crisis
from apps.contrib.commons import DateAccuracyGrapheneEnum
from apps.event.schema import EventListType
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount


class CrisisReviewCountType(graphene.ObjectType):
    """
    Class: CrisisReviewCountType

    This class represents the count and progress of crisis reviews.

    Attributes:
    - review_not_started_count (int, optional): The count of reviews that have not yet started.
    - review_in_progress_count (int, optional): The count of reviews that are currently in progress.
    - review_re_request_count (int, optional): The count of reviews that have been re-requested.
    - review_approved_count (int, optional): The count of reviews that have been approved.
    - total_count (int, optional): The total count of all reviews.
    - progress (float, optional): The progress of the reviews as a percentage.

    Note:
    - All attributes are optional and may be None if the corresponding count is not available.

    """
    review_not_started_count = graphene.Int(required=False)
    review_in_progress_count = graphene.Int(required=False)
    review_re_request_count = graphene.Int(required=False)
    review_approved_count = graphene.Int(required=False)
    total_count = graphene.Int(required=False)
    progress = graphene.Float(required=False)


class CrisisType(DjangoObjectType):
    """
    CrisisType

    This class represents a Crisis object in the GraphQL API. It is a subclass of DjangoObjectType.

    Attributes:
        crisis_type (graphene.Field): A field representing the crisis type as a CrisisTypeGrapheneEnum.
        crisis_type_display (EnumDescription): A description of the crisis type.
        events (DjangoPaginatedListObjectField): A field representing the events related to the crisis.
        total_stock_idp_figures (graphene.Field): A field representing the total stock IDP figures for the crisis.
        stock_idp_figures_max_end_date (graphene.Field): A field representing the maximum end date of the stock IDP figures for the crisis.
        total_flow_nd_figures (graphene.Field): A field representing the total flow ND figures for the crisis.
        start_date_accuracy (graphene.Field): A field representing the accuracy of the start date for the crisis.
        start_date_accuracy_display (EnumDescription): A description of the accuracy of the start date.
        end_date_accuracy (graphene.Field): A field representing the accuracy of the end date for the crisis.
        end_date_accuracy_display (EnumDescription): A description of the accuracy of the end date.
        event_count (graphene.Field): A field representing the number of events related to the crisis.
        review_count (CrisisReviewCountType): A field representing the number of reviews for the crisis.

    Methods:
        resolve_total_stock_idp_figures(root, info, **kwargs): Returns the total stock IDP figures for the crisis.
        resolve_stock_idp_figures_max_end_date(root, info, **kwargs): Returns the maximum end date of the stock IDP figures for the crisis.
        resolve_total_flow_nd_figures(root, info, **kwargs): Returns the total flow ND figures for the crisis.
        resolve_event_count(root, info, **kwargs): Returns the number of events related to the crisis.
        resolve_review_count(root, info, **kwargs): Returns the number of reviews for the crisis.
    """
    class Meta:
        model = Crisis

    crisis_type = graphene.Field(CrisisTypeGrapheneEnum)
    crisis_type_display = EnumDescription(source='get_crisis_type_display')
    events = DjangoPaginatedListObjectField(
        EventListType,
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
        related_name='events',
        reverse_related_name='crisis',
    )
    total_stock_idp_figures = graphene.Field(graphene.Int)
    stock_idp_figures_max_end_date = graphene.Field(graphene.Date, required=False)
    total_flow_nd_figures = graphene.Field(graphene.Int)
    start_date_accuracy = graphene.Field(DateAccuracyGrapheneEnum)
    start_date_accuracy_display = EnumDescription(source='get_start_date_accuracy_display')
    end_date_accuracy = graphene.Field(DateAccuracyGrapheneEnum)
    end_date_accuracy_display = EnumDescription(source='get_end_date_accuracy_display')
    event_count = graphene.Field(graphene.Int)
    review_count = graphene.Field(CrisisReviewCountType)

    def resolve_total_stock_idp_figures(root, info, **kwargs):
        NULL = 'null'
        value = getattr(
            root,
            Crisis.IDP_FIGURES_ANNOTATE,
            NULL
        )
        if value != NULL:
            return value
        return info.context.crisis_crisis_total_stock_idp_figures.load(root.id)

    def resolve_stock_idp_figures_max_end_date(root, info, **kwargs):
        NULL = 'null'
        value = getattr(
            root,
            Crisis.IDP_FIGURES_REFERENCE_DATE_ANNOTATE,
            NULL
        )
        if value != NULL:
            return value
        return info.context.crisis_stock_idp_figures_max_end_date.load(root.id)

    def resolve_total_flow_nd_figures(root, info, **kwargs):
        NULL = 'null'
        value = getattr(
            root,
            Crisis.ND_FIGURES_ANNOTATE,
            NULL,
        )
        if value != NULL:
            return value
        return info.context.crisis_crisis_total_flow_nd_figures.load(root.id)

    def resolve_event_count(root, info, **kwargs):
        return info.context.event_count_dataloader.load(root.id)

    def resolve_review_count(root, info, **kwargs):
        return info.context.crisis_review_count_dataloader.load(root.id)


class CrisisListType(CustomDjangoListObjectType):
    """

    CrisisListType class is a subclass of CustomDjangoListObjectType. It represents a GraphQL list type for Crisis objects.

    Attributes:
        Meta: A nested class that holds metadata of CrisisListType class.
            - model: The model class that CrisisListType is associated with (Crisis).
            - filterset_class: The filterset class used for filtering Crisis objects (CrisisFilter).

    """
    class Meta:
        model = Crisis
        filterset_class = CrisisFilter


class Query:
    """
    Class Query

    This class represents the queries available in the application.

    Attributes:
        crisis (DjangoObjectField): The field representing a single crisis object.
            It is of type CrisisType.
        crisis_list (DjangoPaginatedListObjectField): The field representing a paginated list of crisis objects.
            It is of type CrisisListType and uses PageGraphqlPaginationWithoutCount for pagination.
            The page size can be specified using the 'pageSize' query parameter.

    """
    crisis = DjangoObjectField(CrisisType)
    crisis_list = DjangoPaginatedListObjectField(CrisisListType,
                                                 pagination=PageGraphqlPaginationWithoutCount(
                                                     page_size_query_param='pageSize'
                                                 ))

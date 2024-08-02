import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
import logging

from apps.extraction.filters import ExtractionQueryFilter
from apps.extraction.models import (
    ExtractionQuery,
)
from apps.entry.schema import EntryListType

from apps.entry.enums import (
    RoleGrapheneEnum,
    FigureCategoryTypeEnum,
    FigureTermsEnum,
    FigureReviewStatusEnum,
)
from apps.crisis.enums import CrisisTypeGrapheneEnum
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount

logger = logging.getLogger(__name__)


class ExtractionQueryObjectType(DjangoObjectType):
    """
    ExtractionQueryObjectType

    DjangoObjectType subclass representing the GraphQL object type for ExtractionQuery.

    Attributes:
        entries (DjangoPaginatedListObjectField): A field representing paginated list of EntryListType objects.
        filter_figure_roles (List[RoleGrapheneEnum]): A list of RoleGrapheneEnum objects representing filter options for
        figure roles.
        filter_figure_crisis_types (List[CrisisTypeGrapheneEnum]): A list of CrisisTypeGrapheneEnum objects representing
        filter options for figure crisis types.
        filter_figure_categories (List[FigureCategoryTypeEnum]): A list of FigureCategoryTypeEnum objects representing
        filter options for figure categories.
        filter_figure_terms (List[FigureTermsEnum]): A list of FigureTermsEnum objects representing filter options for
        figure terms.
        filter_figure_review_status (List[FigureReviewStatusEnum]): A list of FigureReviewStatusEnum objects
        representing filter options for figure review status.

    """
    class Meta:
        model = ExtractionQuery

    entries = DjangoPaginatedListObjectField(EntryListType,
                                             pagination=PageGraphqlPaginationWithoutCount(
                                                 page_size_query_param='pageSize'
                                             ), accessor='entries')
    # NOTE: We need to define this at ReportType as well
    filter_figure_roles = graphene.List(graphene.NonNull(RoleGrapheneEnum))
    filter_figure_crisis_types = graphene.List(graphene.NonNull(CrisisTypeGrapheneEnum))
    filter_figure_categories = graphene.List(graphene.NonNull(FigureCategoryTypeEnum))
    filter_figure_terms = graphene.List(graphene.NonNull(FigureTermsEnum))
    filter_figure_review_status = graphene.List(graphene.NonNull(FigureReviewStatusEnum))


class ExtractionQueryListType(CustomDjangoListObjectType):
    """
    A class representing a list of ExtractionQuery objects.

    Parameters:
        CustomDjangoListObjectType : Class
            A custom Django ListObjectType class.

    Attributes:
        Meta : Class
            The inner Meta class containing metadata for the class.

    Attributes (Meta):
        model : Model
            The model class associated with the ExtractionQueryListType.
        filterset_class : Class
            The filterset class used for filtering the ExtractionQuery objects.

    """
    class Meta:
        model = ExtractionQuery
        filterset_class = ExtractionQueryFilter


class Query:
    """
    Class Query

    This class represents a query object.

    Attributes:
        extraction_query (DjangoObjectField): A field representing a single extraction query.
        extraction_query_list (DjangoPaginatedListObjectField): A field representing a paginated list of extraction
        queries.

    """
    extraction_query = DjangoObjectField(ExtractionQueryObjectType)
    extraction_query_list = DjangoPaginatedListObjectField(ExtractionQueryListType,
                                                           pagination=PageGraphqlPaginationWithoutCount(
                                                               page_size_query_param='pageSize'
                                                           ))

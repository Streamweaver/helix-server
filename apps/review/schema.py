import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from utils.graphene.enums import EnumDescription

from apps.review.enums import (
    ReviewCommentTypeEnum,
    ReviewFieldTypeEnum,
)
from apps.review.filters import UnifiedReviewCommentFilter
from apps.review.models import UnifiedReviewComment
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount


class UnifiedReviewCommentType(DjangoObjectType):
    """
    UnifiedReviewCommentType

    A class representing a unified review comment type.

    Attributes:
        comment_type (graphene.NonNull): The comment type enum field.
        comment_display (EnumDescription): The display value for the comment type.
        field (graphene.NonNull): The field enum field.
        field_display (EnumDescription): The display value for the field.

    Meta:
        model (UnifiedReviewComment): The model that this class represents.
    """
    comment_type = graphene.NonNull(ReviewCommentTypeEnum)
    comment_display = EnumDescription(source='get_comment_type_display')
    field = graphene.NonNull(ReviewFieldTypeEnum)
    field_display = EnumDescription(source='get_review_field_display')

    class Meta:
        model = UnifiedReviewComment


class UnifiedReviewCommentListType(CustomDjangoListObjectType):
    """
    This class defines a custom Django list object type for UnifiedReviewComment model. It inherits from
    CustomDjangoListObjectType.

    Attributes:
        Meta:
            A nested class that specifies metadata for the UnifiedReviewCommentListType.

    Methods:
        N/A

    """
    class Meta:
        model = UnifiedReviewComment
        filterset_class = UnifiedReviewCommentFilter


class Query(object):
    """

    This class represents a Query object.

    Attributes:
        review_comment (DjangoObjectField): A field that represents a review comment of type UnifiedReviewCommentType.
        review_comments (DjangoPaginatedListObjectField): A field that represents a paginated list of review comments of
        type UnifiedReviewCommentListType.
            It uses PageGraphqlPaginationWithoutCount for pagination with a custom page size query parameter 'pageSize'.

    """
    review_comment = DjangoObjectField(UnifiedReviewCommentType)
    review_comments = DjangoPaginatedListObjectField(
        UnifiedReviewCommentListType,
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        )
    )

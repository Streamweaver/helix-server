import graphene
from graphene.types.utils import get_type
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from utils.graphene.enums import EnumDescription

from apps.crisis.enums import CrisisTypeGrapheneEnum
from apps.contextualupdate.models import ContextualUpdate
from apps.contextualupdate.filters import ContextualUpdateFilter
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount


class ContextualUpdateType(DjangoObjectType):
    """Represents the GraphQL object type for ContextualUpdate."""
    class Meta:
        model = ContextualUpdate

    crisis_types = graphene.List(graphene.NonNull(CrisisTypeGrapheneEnum))
    crisis_types_display = EnumDescription(source='get_crisis_types_display')
    sources = graphene.Dynamic(
        lambda: DjangoPaginatedListObjectField(
            get_type('apps.organization.schema.OrganizationListType'),
            related_name='sources',
            reverse_related_name='sourced_contextual_updates',
        ))
    publishers = graphene.Dynamic(
        lambda: DjangoPaginatedListObjectField(
            get_type('apps.organization.schema.OrganizationListType'),
            related_name='publishers',
            reverse_related_name='published_contextual_updates',
        ))


class ContextualUpdateListType(CustomDjangoListObjectType):
    """
    A custom list type for ContextualUpdate objects in Django.

    This class extends the CustomDjangoListObjectType and provides a list type for ContextualUpdate model objects. It also specifies the ContextualUpdate model and the ContextualUpdateFilter as the filterset.

    Attributes:
        model (type): The ContextualUpdate model.
        filterset_class (type): The ContextualUpdateFilter filterset class.

    """
    class Meta:
        model = ContextualUpdate
        filterset_class = ContextualUpdateFilter


class Query:
    """
    Class representing a query.

    Attributes:
        contextual_update (DjangoObjectField): Represents the contextual update.
        contextual_update_list (DjangoPaginatedListObjectField): Represents the list of contextual updates.
    """
    contextual_update = DjangoObjectField(ContextualUpdateType)
    contextual_update_list = DjangoPaginatedListObjectField(ContextualUpdateListType,
                                                            pagination=PageGraphqlPaginationWithoutCount(
                                                                page_size_query_param='pageSize'
                                                            ))

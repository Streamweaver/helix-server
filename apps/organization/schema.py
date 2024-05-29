import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from utils.graphene.enums import EnumDescription

from apps.contact.schema import ContactListType
from apps.country.schema import CountryType
from apps.organization.models import Organization, OrganizationKind
from apps.organization.enums import (
    OrganizationCategoryTypeGrapheneEnum, OrganizationReliablityEnum
)
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount
from apps.organization.filters import OrganizationFilter, OrganizationKindFilter


class OrganizationType(DjangoObjectType):
    """

    OrganizationType

    A class that defines the GraphQL type for the Organization model.

    Attributes:
        category (graphene.Field): A field that represents the category of the organization.
        category_display (EnumDescription): A field that represents the display value of the category.
        contacts (DjangoPaginatedListObjectField): A field that represents the contacts related to the organization.
        organization_kind (graphene.Field): A field that represents the kind of the organization.
        countries (graphene.List): A list that represents the countries related to the organization.

    Methods:
        resolve_countries(self, root, info, **kwargs):
            Resolves the countries related to the organization.

        resolve_organization_kind(self, root, info, **kwargs):
            Resolves the organization kind for the organization.

    """
    class Meta:
        model = Organization

    category = graphene.Field(OrganizationCategoryTypeGrapheneEnum)
    category_display = EnumDescription(source='get_category_display')
    contacts = DjangoPaginatedListObjectField(ContactListType,
                                              pagination=PageGraphqlPaginationWithoutCount(
                                                  page_size_query_param='pageSize'
                                              ))
    organization_kind = graphene.Field("apps.organization.schema.OrganizationKindObjectType")
    countries = graphene.List(graphene.NonNull(CountryType), required=True)

    def resolve_countries(root, info, **kwargs):
        """
        Resolves the countries related to the organization.
        """
        return info.context.organization_countries_loader.load(root.id)

    def resolve_organization_kind(root, info, **kwargs):
        """
        Resolves the organization kind for the organization.
        """
        return info.context.organization_organization_kind_loader.load(root.id)


class OrganizationListType(CustomDjangoListObjectType):
    """
    The OrganizationListType class is a subclass of CustomDjangoListObjectType and represents a GraphQL object type for a list of organizations.

    Attributes:
        Meta.filterset_class (class): The filterset class for filtering the list of organizations.
        Meta.model (class): The Django model class representing the organization.

    """
    class Meta:
        filterset_class = OrganizationFilter
        model = Organization


class OrganizationKindObjectType(DjangoObjectType):
    """

    OrganizationKindObjectType

    A class representing a GraphQL Object Type for the OrganizationKind model in Django.

    """
    class Meta:
        model = OrganizationKind

    organizations = DjangoPaginatedListObjectField(OrganizationListType,
                                                   pagination=PageGraphqlPaginationWithoutCount(
                                                       page_size_query_param='pageSize'
                                                   ))
    reliability = graphene.Field(OrganizationReliablityEnum)
    reliability_display = EnumDescription(source='get_reliability_display_display')


class OrganizationKindListType(CustomDjangoListObjectType):
    """
    Custom Django List Object Type for OrganizationKind

    This class extends CustomDjangoListObjectType and represents a list of OrganizationKind objects.

    Attributes:
        model (Model): The Django model associated with this class.
        filterset_class (FilterSet): The Django FilterSet class used for filtering the query results.

    """
    class Meta:
        model = OrganizationKind
        filterset_class = OrganizationKindFilter


class Query:
    """
    Query class represents the GraphQL query object for performing queries related to organizations and organization kinds.

    Attributes:
        organization: A DjangoObjectField that represents querying a single organization. It takes an instance of OrganizationType as its parameter.

        organization_list: A DjangoPaginatedListObjectField that represents querying a paginated list of organizations. It takes an instance of OrganizationListType as its parameter. It also accepts pagination options using PageGraphqlPaginationWithoutCount, with the ability to set the page size query parameter.

        organization_kind: A DjangoObjectField that represents querying a single organization kind. It takes an instance of OrganizationKindObjectType as its parameter.

        organization_kind_list: A DjangoPaginatedListObjectField that represents querying a paginated list of organization kinds. It takes an instance of OrganizationKindListType as its parameter. It also accepts pagination options using PageGraphqlPaginationWithoutCount, with the ability to set the page size query parameter.
    """
    organization = DjangoObjectField(OrganizationType)
    organization_list = DjangoPaginatedListObjectField(OrganizationListType,
                                                       pagination=PageGraphqlPaginationWithoutCount(
                                                           page_size_query_param='pageSize'
                                                       ))
    organization_kind = DjangoObjectField(OrganizationKindObjectType)
    organization_kind_list = DjangoPaginatedListObjectField(OrganizationKindListType,
                                                            pagination=PageGraphqlPaginationWithoutCount(
                                                                page_size_query_param='pageSize'
                                                            ))

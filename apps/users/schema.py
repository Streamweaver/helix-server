from typing import Union

from django.contrib.auth import get_user_model
from django.db.models import Model
import graphene
from graphene import Field, ObjectType
from graphene.types.generic import GenericScalar
from graphene.types.utils import get_type
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from utils.graphene.enums import EnumDescription

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount
from apps.users.filters import UserFilter, PortfolioFilter
from apps.users.models import Portfolio

from .enums import PermissionActionEnum, PermissionModelEnum, PermissionRoleEnum

User: Model = get_user_model()

EntryListType: ObjectType = get_type('apps.entry.schema.EntryListType')


class PermissionsType(ObjectType):
    """

    :class: PermissionsType

    This class represents a permission type.

    Attributes:
        action (PermissionActionEnum): The action required for this permission.
        action_display (EnumDescription): Description of the action.
        entities (List[PermissionModelEnum]): The entities associated with this permission.

    """
    action = Field(PermissionActionEnum, required=True)
    action_display = EnumDescription(source='get_action_display')
    entities = graphene.List(graphene.NonNull(PermissionModelEnum), required=True)


class PortfolioType(DjangoObjectType):
    """

    PortfolioType class

    This class represents a GraphQL ObjectType for the Portfolio model in Django.

    Attributes:
        model (class): The Portfolio model class.

    Properties:
        role (Field): A required field of type PermissionRoleEnum.
        role_display (EnumDescription): A field that retrieves the display value of the role enum.
        permissions (List[PermissionsType]): A list of non-null PermissionsType objects.

    """
    class Meta:
        model = Portfolio

    role = Field(PermissionRoleEnum, required=True)
    role_display = EnumDescription(source='get_role_display')
    permissions = graphene.List(graphene.NonNull(PermissionsType))


class PortfolioListType(CustomDjangoListObjectType):
    """
    This class represents a list type for portfolios.

    It is a subclass of CustomDjangoListObjectType, which is a custom list object type used in Django. It provides functionality for querying and filtering portfolios.

    Attributes:
        model (Model): The model class representing the Portfolio.
        filterset_class (FilterSet): The filter set class used for filtering the portfolios.

    """
    class Meta:
        model = Portfolio
        filterset_class = PortfolioFilter


class UserPortfolioMetaDataType(graphene.ObjectType):
    """
    This class represents the meta data type for a user's portfolio.

    Attributes:
        is_admin (bool): Indicates if the user is an admin.
        is_directors_office (bool): Indicates if the user is part of the director's office.
        is_reporting_team (bool): Indicates if the user is part of the reporting team.
        portfolio_role (PermissionRoleEnum): The role of the user's portfolio.
        portfolio_role_display (str): The display name of the user's portfolio role.
    """
    is_admin = graphene.Boolean()
    is_directors_office = graphene.Boolean()
    is_reporting_team = graphene.Boolean()
    portfolio_role = Field(PermissionRoleEnum)
    portfolio_role_display = graphene.String()


class UserType(DjangoObjectType):
    """
    A class representing the UserType in the application.

    This class extends the DjangoObjectType and provides a GraphQL representation of the User model.

    Attributes:
        created_entry (DjangoPaginatedListObjectField): A field representing the paginated list of entries created by the user.
        full_name (Field): A field representing the full name of the user.
        email (graphene.String): A field representing the email of the user.
        portfolios (graphene.List): A list of portfolios associated with the user.
        portfolios_metadata (graphene.Field): A field representing the metadata of the user's portfolios.
        permissions (graphene.List): A list of permissions associated with the user.

    Methods:
        resolve_permissions(root, info, **_):
            Resolves the permissions associated with the user.
            Args:
                root: The root object.
                info: The GraphQL ResolveInfo object.
            Returns:
                The list of permissions associated with the user.

        resolve_email(root, info, **_):
            Resolves the email of the user.
            Args:
                root: The root object.
                info: The GraphQL ResolveInfo object.
            Returns:
                The email of the user.

        resolve_portfolios_metadata(user, info, **_):
            Resolves the metadata of the user's portfolios.
            Args:
                user: The user object.
                info: The GraphQL ResolveInfo object.
            Returns:
                The metadata of the user's portfolios.

        resolve_portfolios(root, info, **_):
            Resolves the portfolios associated with the user.
            Args:
                root: The root object.
                info: The GraphQL ResolveInfo object.
            Returns:
                The portfolios associated with the user.
    """
    class Meta:
        model = User
        fields = (
            'created_entry', 'date_joined', 'email', 'first_name', 'last_name',
            'full_name', 'id', 'is_active', 'last_login', 'username'
        )

    created_entry = DjangoPaginatedListObjectField(
        EntryListType,
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
        related_name='created_entry',
        reverse_related_name='created_by',
    )
    full_name = Field(graphene.String, required=True)
    email = graphene.String()
    portfolios = graphene.List(graphene.NonNull(PortfolioType))
    portfolios_metadata = graphene.Field(UserPortfolioMetaDataType, required=True)
    permissions = graphene.List(graphene.NonNull(PermissionsType))

    @staticmethod
    def resolve_permissions(root, info, **_):
        if root == info.context.request.user:
            return root.permissions

    @staticmethod
    def resolve_email(root, info, **_):
        if root == info.context.request.user:
            return root.email

    @staticmethod
    def resolve_portfolios_metadata(user, info, **_):
        return info.context.user_portfolios_metadata.load(user.id)

    @staticmethod
    def resolve_portfolios(root, info, **_):
        return Portfolio.objects.filter(user=root.id).select_related('monitoring_sub_region')


class UserListType(CustomDjangoListObjectType):
    """
    A GraphQL Object Type representing a list of User objects.

    Inherits from `CustomDjangoListObjectType` and includes metadata about the User model and filter.

    Args:
        CustomDjangoListObjectType (graphene_django.types.CustomDjangoListObjectType): Base class for defining GraphQL list types for Django models.

    Attributes:
        Meta (class): Inner class to define metadata options.

            Attributes:
                model (django.db.models.Model): The Django model associated with this GraphQL list type.
                filterset_class (django_filters.FilterSet): The filter set used to filter the list of User objects.
    """
    class Meta:
        model = User
        filterset_class = UserFilter


class Query(object):
    """
    The Query class represents a collection of GraphQL query fields. It includes fields for retrieving user-related data such as the currently logged-in user, a list of users with pagination support, a list of portfolios with pagination support, and a mapping of roles allowed in each region.

    Attributes:
        me (Field): A field that returns the currently logged-in user (UserType).
        user (DjangoObjectField): A field that returns a user object (UserType) based on a Django model object.
        users (DjangoPaginatedListObjectField): A field that returns a paginated list of user objects (UserListType) based on a Django model queryset. This field supports pagination with the PageGraphqlPaginationWithoutCount class, using the 'pageSize' query param.
        portfolios (DjangoPaginatedListObjectField): A field that returns a paginated list of portfolio objects (PortfolioListType) based on a Django model queryset. This field supports pagination with the PageGraphqlPaginationWithoutCount class, using the 'pageSize' query param.
        role_with_region_allowed_map (Field): A field that returns a generic scalar object representing a mapping of roles allowed in each region.

    Methods:
        resolve_role_with_region_allowed_map(root, info, **kwargs):
            This static method resolves the role_with_region_allowed_map field by returning the result of calling the Portfolio.get_role_allows_region_map() method.

        resolve_me(root, info, **kwargs) -> Union[User, None]:
            This static method resolves the me field by checking if the user is authenticated in the provided GraphQL execution context (info.context). If the user is authenticated, it returns the currently logged-in user (User object). If the user is not authenticated, it returns None.

    """
    me = Field(UserType)
    user = DjangoObjectField(UserType)
    users = DjangoPaginatedListObjectField(UserListType,
                                           pagination=PageGraphqlPaginationWithoutCount(
                                               page_size_query_param='pageSize'
                                           ))
    portfolios = DjangoPaginatedListObjectField(PortfolioListType,
                                                pagination=PageGraphqlPaginationWithoutCount(
                                                    page_size_query_param='pageSize'
                                                ))
    role_with_region_allowed_map = Field(GenericScalar)

    @staticmethod
    def resolve_role_with_region_allowed_map(root, info, **kwargs):
        return Portfolio.get_role_allows_region_map()

    @staticmethod
    def resolve_me(root, info, **kwargs) -> Union[User, None]:
        if info.context.user.is_authenticated:
            return info.context.user
        return None

import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from apps.resource.models import Resource, ResourceGroup


class ResourceType(DjangoObjectType):
    """
    Class to represent a resource type.

    This class is a subclass of DjangoObjectType, designed to represent a resource and its associated metadata.

    Attributes:
        model (Model): The Django model representing the resource type.

    Methods:
        N/A

    Usage:
        To use this class, simply subclass it and specify the Django model representing the resource type in the `Meta` class.

    Example:
        class CustomResourceType(ResourceType):
            class Meta:
                model = CustomResourceModel

    Note:
        Make sure to install the required dependencies, such as graphene-django and Django, before using this class.
    """
    class Meta:
        model = Resource


class ResourceGroupType(DjangoObjectType):
    """

    This class represents a GraphQL ObjectType for the ResourceGroup model in Django.

    Attributes:
        - model: The Django model that represents a resource group.

    Usage:
        - Use this class to define a GraphQL ObjectType for the ResourceGroup model in Django.

    """
    class Meta:
        model = ResourceGroup


class Query:
    """

    Class Query

    This class represents the GraphQL query type in the application. It defines the fields and their corresponding resolvers for retrieving resources and resource groups.

    Attributes:
    - resource: A DjangoObjectField representing a single resource.
    - resource_list: A List of ResourceType representing a list of resources.
    - resource_group: A DjangoObjectField representing a single resource group.
    - resource_group_list: A List of ResourceGroupType representing a list of resource groups.

    Methods:
    - resolve_resource_list: A resolver method that retrieves a list of resources based on the currently authenticated user.
    - resolve_resource_group_list: A resolver method that retrieves a list of resource groups based on the currently authenticated user.

    """
    resource = DjangoObjectField(ResourceType)
    resource_list = graphene.List(graphene.NonNull(ResourceType))
    resource_group = DjangoObjectField(ResourceType)
    resource_group_list = graphene.List(graphene.NonNull(ResourceGroupType))

    def resolve_resource_list(root, info, **kwargs):
        return Resource.objects.filter(created_by=info.context.user)

    def resolve_resource_group_list(root, info, **kwargs):
        return ResourceGroup.objects.filter(created_by=info.context.user)

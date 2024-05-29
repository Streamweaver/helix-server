from django.utils.translation import gettext
import graphene

from apps.resource.models import Resource, ResourceGroup
from apps.resource.schema import ResourceType, ResourceGroupType
from apps.resource.serializers import (
    ResourceSerializer,
    ResourceGroupSerializer,
    ResourceUpdateSerializer,
    ResourceGroupUpdateSerializer
)
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker
from utils.mutation import generate_input_type_for_serializer


ResourceCreateInputType = generate_input_type_for_serializer(
    'ResourceCreateInputType',
    ResourceSerializer
)

ResourceUpdateInputType = generate_input_type_for_serializer(
    'ResourceUpdateInputType',
    ResourceUpdateSerializer
)


class CreateResource(graphene.Mutation):
    """
    CreateResource

    A class that represents a GraphQL mutation for creating a resource.

    Attributes:
        errors (List[CustomErrorType]): A list of custom error types.
        ok (bool): A boolean indicating if the mutation was successful.
        result (ResourceType): An instance of the created resource.

    Methods:
        mutate(root, info, data)
            A static method that is called to perform the mutation.

    Example Usage:
        mutation = CreateResource(data=data)
        mutation.mutate(root, info, data)
    """
    class Arguments:
        data = ResourceCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ResourceType)

    @staticmethod
    @permission_checker(['resource.add_resource'])
    def mutate(root, info, data):
        serializer = ResourceSerializer(data=data,
                                        context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateResource(errors=errors, ok=False)
        instance = serializer.save()
        return CreateResource(result=instance, errors=None, ok=True)


class UpdateResource(graphene.Mutation):
    """
    UpdateResource class

    This class represents a mutation for updating a resource. It inherits from the `graphene.Mutation` class.

    Attributes:
        Arguments: A nested class representing the arguments for the mutation.
        - data: An instance of the ResourceUpdateInputType class representing the data for the update.

        errors: A list of CustomErrorType objects representing any errors that occurred during the mutation.
        ok: A boolean indicating whether the mutation was successful or not.
        result: An instance of the ResourceType class representing the updated resource.

    Methods:
        mutate: A static method that performs the mutation operation.

    """
    class Arguments:
        data = ResourceUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ResourceType)

    @staticmethod
    @permission_checker(['resource.change_resource'])
    def mutate(root, info, data):
        try:
            instance = Resource.objects.get(id=data['id'], created_by=info.context.user)
        except Resource.DoesNotExist:
            return UpdateResource(errors=[
                dict(field='nonFieldErrors', messages=gettext('Resource does not exist.'))
            ])
        serializer = ResourceSerializer(instance=instance,
                                        data=data,
                                        context={'request': info.context.request},
                                        partial=True)
        if errors := mutation_is_not_valid(serializer):
            return UpdateResource(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateResource(result=instance, errors=None, ok=True)


class DeleteResource(graphene.Mutation):
    """
        This class represents a GraphQL mutation to delete a resource.

        Args:
            graphene.Mutation: The base mutation class provided by the Graphene library.

        Attributes:
            id (graphene.ID): The ID of the resource to be deleted.
            errors (graphene.List[graphene.NonNull(CustomErrorType)]): List of custom error types.
            ok (graphene.Boolean): Indicates whether the deletion was successful.
            result (graphene.Field(ResourceType)): The deleted resource.

        Methods:
            mutate(root, info, id): Static method that performs the resource deletion.

        Examples:
            delete_resource = DeleteResource(id="123456")
            result = delete_resource.mutate(root, info, id)

    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ResourceType)

    @staticmethod
    @permission_checker(['resource.delete_resource'])
    def mutate(root, info, id):
        try:
            instance = Resource.objects.get(id=id, created_by=info.context.user)
        except Resource.DoesNotExist:
            return UpdateResource(errors=[
                dict(field='nonFieldErrors', messages=gettext('Resource does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteResource(result=instance, errors=None, ok=True)


ResourceGroupCreateInputType = generate_input_type_for_serializer(
    'ResourceGroupCreateInputType',
    ResourceGroupSerializer
)

ResourceGroupUpdateInputType = generate_input_type_for_serializer(
    'ResourceGroupUpdateInputType',
    ResourceGroupUpdateSerializer
)


class CreateResourceGroup(graphene.Mutation):
    """
    Class: CreateResourceGroup

    A class representing a GraphQL mutation for creating a resource group.

    Attributes:
        - Arguments:
            - data: Required argument of type ResourceGroupCreateInputType
                - Represents the data needed to create a resource group

        - errors: List of CustomErrorType
            - Represents any errors that occurred during the mutation

        - ok: Boolean
            - Indicates the success or failure of the mutation

        - result: Field of type ResourceGroupType
            - Represents the result of the mutation, i.e., the created resource group


    Methods:
        - mutate(root, info, data)
            - A static method that is responsible for executing the mutation
            - Parameters:
                - root: The root value passed for the mutation (not used in this implementation)
                - info: GraphQLResolveInfo representing the information about the execution (not used in this implementation)
                - data: Represents the input data for creating a resource group
            - Returns:
                - An instance of CreateResourceGroup with the result field set to the created resource group and errors field set to None, and ok field set to True if the mutation was successful
                - An instance of CreateResourceGroup with errors field set to a list of errors and ok field set to False if the mutation was not valid
    """
    class Arguments:
        data = ResourceGroupCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ResourceGroupType)

    @staticmethod
    @permission_checker(['resource.add_resource'])
    def mutate(root, info, data):
        serializer = ResourceGroupSerializer(data=data,
                                             context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateResourceGroup(errors=errors, ok=False)
        instance = serializer.save()
        return CreateResourceGroup(result=instance, errors=None, ok=True)


class UpdateResourceGroup(graphene.Mutation):
    """

    UpdateResourceGroup class

    This class is a mutation class for updating a resource group. It inherits from the `graphene.Mutation` class.

    Attributes:
        data (ResourceGroupUpdateInputType): Input data for updating the resource group.
        errors (List[CustomErrorType]): List of errors that occurred during the mutation.
        ok (Boolean): Indicates whether the mutation was successful or not.
        result (ResourceGroupType): Updated resource group.

    Methods:
        mutate(root, info, data)
            This method is responsible for executing the mutation and updating the resource group.

    """
    class Arguments:
        data = ResourceGroupUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ResourceGroupType)

    @staticmethod
    @permission_checker(['resource.change_resource'])
    def mutate(root, info, data):
        try:
            instance = ResourceGroup.objects.get(id=data['id'], created_by=info.context.user)
        except ResourceGroup.DoesNotExist:
            return UpdateResourceGroup(errors=[
                dict(field='nonFieldErrors', messages=gettext('Resource group does not exist.'))
            ])
        serializer = ResourceGroupSerializer(instance=instance,
                                             data=data,
                                             context={'request': info.context.request},
                                             partial=True)
        if errors := mutation_is_not_valid(serializer):
            return UpdateResourceGroup(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateResourceGroup(result=instance, errors=None, ok=True)


class DeleteResourceGroup(graphene.Mutation):
    """
    The `DeleteResourceGroup` class is a mutation class in a GraphQL schema that is used to delete a resource group. It takes an `id` argument and deletes the resource group with the corresponding ID.

    Attributes:
        - `errors`: A list of custom error types.
        - `ok`: A boolean indicating whether the deletion was successful.
        - `result`: A field of type `ResourceGroupType` that represents the deleted resource group.

    Methods:
        - `mutate(root, info, id)`: This is a static method decorated with the `permission_checker` decorator. It is called when the mutation is executed. It takes the `root` object, `info` object, and the `id` argument as parameters. In this method, it tries to retrieve the resource group instance from the database based on the provided ID and the authenticated user. If the resource group does not exist, it returns an error with a message indicating that the resource group does not exist. If the resource group can be deleted, it deletes the instance from the database. Finally, it returns the result of the deletion along with any errors that occurred during the deletion process.

    Usage Example:
        mutation {
            deleteResourceGroup(id: "1") {
                errors {
                    field
                    messages
                }
                ok
                result {
                    id
                    name
                    ...
                }
            }
        }
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ResourceGroupType)

    @staticmethod
    @permission_checker(['resource.delete_resource'])
    def mutate(root, info, id):
        try:
            instance = ResourceGroup.objects.get(id=id, created_by=info.context.user)
        except ResourceGroup.DoesNotExist:
            return DeleteResourceGroup(errors=[
                dict(field='nonFieldErrors', messages=gettext('Resource group does not exist.'))
            ])
        can_delete, msg = instance.can_delete()
        if not can_delete:
            return DeleteResourceGroup(errors=[
                dict(field='nonFieldErrors', messages=msg)
            ])
        instance.delete()
        instance.id = id
        return DeleteResourceGroup(result=instance, errors=None, ok=True)


class Mutation:
    """

    Mutation class

    This class defines the mutations available in the system for creating, updating, and deleting resources and resource groups.

    Attributes:
        create_resource: Mutation field for creating a resource.
        update_resource: Mutation field for updating a resource.
        delete_resource: Mutation field for deleting a resource.
        create_resource_group: Mutation field for creating a resource group.
        update_resource_group: Mutation field for updating a resource group.
        delete_resource_group: Mutation field for deleting a resource group.

    """
    create_resource = CreateResource.Field()
    update_resource = UpdateResource.Field()
    delete_resource = DeleteResource.Field()
    create_resource_group = CreateResourceGroup.Field()
    update_resource_group = UpdateResourceGroup.Field()
    delete_resource_group = DeleteResourceGroup.Field()

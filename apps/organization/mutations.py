from django.utils.translation import gettext
import graphene

from apps.contrib.mutations import ExportBaseMutation
from apps.contrib.models import ExcelDownload
from apps.organization.models import Organization, OrganizationKind
from apps.organization.schema import OrganizationType, OrganizationKindObjectType
from apps.organization.filters import OrganizationFilterDataInputType
from apps.organization.serializers import (
    OrganizationSerializer,
    OrganizationUpdateSerializer,
    OrganizationKindSerializer,
    OrganizationKindUpdateSerializer,
)
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker
from utils.mutation import generate_input_type_for_serializer


# organization kind

OrganizationKindCreateInputType = generate_input_type_for_serializer(
    'OrganizationKindCreateInputType',
    OrganizationKindSerializer
)

OrganizationKindUpdateInputType = generate_input_type_for_serializer(
    'OrganizationKindUpdateInputType',
    OrganizationKindUpdateSerializer
)


class CreateOrganizationKind(graphene.Mutation):
    """
    create_organization_kind

    A class representing a GraphQL mutation to create a new organization kind.

    Attributes:
        Arguments:
            data (OrganizationKindCreateInputType): The input data for creating a new organization kind.

        errors (List[CustomErrorType]): A list of custom error types.

        ok (bool): A boolean indicating if the mutation was successful.

        result (OrganizationKindObjectType): The created organization kind object.

    Methods:
        mutate:
            Executes the mutation to create a new organization kind.

    """
    class Arguments:
        data = OrganizationKindCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(OrganizationKindObjectType)

    @staticmethod
    @permission_checker(['organization.add_organizationkind'])
    def mutate(root, info, data):
        serializer = OrganizationKindSerializer(data=data)
        if errors := mutation_is_not_valid(serializer):
            return CreateOrganizationKind(errors=errors, ok=False)
        instance = serializer.save()
        return CreateOrganizationKind(result=instance, errors=None, ok=True)


class UpdateOrganizationKind(graphene.Mutation):
    """
    UpdateOrganizationKind class is a mutation class that is used to update an instance of OrganizationKind.

    Arguments:
        - data (OrganizationKindUpdateInputType): The data to be updated for the OrganizationKind instance. This argument is required.

    Attributes:
        - errors (List[CustomErrorType]): A list of custom error objects. Each error object contains the field name and corresponding error messages.
        - ok (Boolean): Indicates whether the mutation was successful or not.
        - result (OrganizationKindObjectType): The updated OrganizationKind instance.

    Methods:
        - mutate(root, info, data): This method is called to perform the mutation operation. It receives the root and info objects as parameters, which provide information about the GraphQL execution context. The 'data' parameter contains the input data for the mutation. It first tries to retrieve the OrganizationKind instance with the provided ID from the database. If it doesn't exist, it returns an error indicating that the OrganizationKind type does not exist. Then, it creates a serializer instance with the retrieved instance and the update data. If the mutation data is not valid, it returns an error with the validation errors. Otherwise, it saves the updated instance and returns it along with the 'ok' flag indicating a successful mutation.

    Note: This class requires the permission 'organization.change_organizationkind' to be used."""
    class Arguments:
        data = OrganizationKindUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(OrganizationKindObjectType)

    @staticmethod
    @permission_checker(['organization.change_organizationkind'])
    def mutate(root, info, data):
        try:
            instance = OrganizationKind.objects.get(id=data['id'])
        except OrganizationKind.DoesNotExist:
            return UpdateOrganizationKind(errors=[
                dict(field='nonFieldErrors', messages=gettext('Organization type does not exist.'))
            ])
        serializer = OrganizationKindSerializer(instance=instance, data=data, partial=True)
        if errors := mutation_is_not_valid(serializer):
            return UpdateOrganizationKind(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateOrganizationKind(result=instance, errors=None, ok=True)


class DeleteOrganizationKind(graphene.Mutation):
    """
    The `DeleteOrganizationKind` class is a mutation class in a GraphQL schema. It is used to delete an instance of the `OrganizationKind` model.

    Args:
        id (graphene.ID): The ID of the `OrganizationKind` instance to be deleted. (required)

    Attributes:
        errors (graphene.List): A list of `CustomErrorType` objects representing any errors that occurred during the mutation.
        ok (graphene.Boolean): A boolean indicating whether the mutation was successful or not.
        result (graphene.Field): A field of type `OrganizationKindObjectType` representing the deleted `OrganizationKind` instance, if successful.

    Methods:
        mutate(root, info, id):
            This method is a static method and is decorated with the `permission_checker` decorator.
            It is called when the mutation is executed.

            Args:
                root: The root value of the GraphQL query.
                info: The information about the execution of the query.
                id (graphene.ID): The ID of the `OrganizationKind` instance to be deleted.

            Returns:
                An instance of `DeleteOrganizationKind` with the result and errors set accordingly.
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(OrganizationKindObjectType)

    @staticmethod
    @permission_checker(['organization.delete_organizationkind'])
    def mutate(root, info, id):
        try:
            instance = OrganizationKind.objects.get(id=id)
        except OrganizationKind.DoesNotExist:
            return DeleteOrganizationKind(errors=[
                dict(field='nonFieldErrors', messages=gettext('Organization type does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteOrganizationKind(result=instance, errors=None, ok=True)


# organization


OrganizationCreateInputType = generate_input_type_for_serializer(
    'OrganizationCreateInputType',
    OrganizationSerializer
)

OrganizationUpdateInputType = generate_input_type_for_serializer(
    'OrganizationUpdateInputType',
    OrganizationUpdateSerializer
)


class CreateOrganization(graphene.Mutation):
    """
    Class: CreateOrganization

    This class represents a GraphQL mutation for creating an organization.

    Attributes:
    - errors (List[CustomErrorType]): A list of custom errors.
    - ok (bool): Indicates if the mutation was successful.
    - result (OrganizationType): The created organization.

    Methods:
    - mutate(root, info, data) -> CreateOrganization: A static method that performs the mutation and returns a CreateOrganization instance.

    """
    class Arguments:
        data = OrganizationCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(OrganizationType)

    @staticmethod
    @permission_checker(['organization.add_organization'])
    def mutate(root, info, data):
        serializer = OrganizationSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateOrganization(errors=errors, ok=False)
        instance = serializer.save()
        return CreateOrganization(result=instance, errors=None, ok=True)


class UpdateOrganization(graphene.Mutation):
    """

    The `UpdateOrganization` class is a mutation class that allows the user to update an existing organization.

    Attributes:
        - `errors`: A list of `CustomErrorType` objects representing any errors that occurred during the mutation.
        - `ok`: A boolean value indicating if the mutation was successful or not.
        - `result`: An instance of `OrganizationType` representing the updated organization.

    Methods:
        - `mutate(root, info, data)`: This static method is the main method of the class and is responsible for performing the mutation logic. It takes three parameters:
            - `root`: The root value.
            - `info`: An object containing information about the execution and the GraphQL schema.
            - `data`: An instance of `OrganizationUpdateInputType` representing the data to update the organization.

        Returns:
            - If the organization with the given ID does not exist, returns an instance of `UpdateOrganization` with the `errors` attribute set to a list containing a dictionary with the `field` set to `'nonFieldErrors'` and the `messages` set to `'Organization does not exist.'`.
            - If there are any errors during the mutation, returns an instance of `UpdateOrganization` with the `errors` attribute set to a list of `CustomErrorType` objects representing the errors, the `ok` attribute set to `False`, and the `result` attribute set to `None`.
            - If the mutation is successful, returns an instance of `UpdateOrganization` with the `result` attribute set to an instance of `OrganizationType` representing the updated organization, the `errors` attribute set to `None`, and the `ok` attribute set to `True`.
    """
    class Arguments:
        data = OrganizationUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(OrganizationType)

    @staticmethod
    @permission_checker(['organization.change_organization'])
    def mutate(root, info, data):
        try:
            instance = Organization.objects.get(id=data['id'])
        except Organization.DoesNotExist:
            return UpdateOrganization(errors=[
                dict(field='nonFieldErrors', messages=gettext('Organization does not exist.'))
            ])
        serializer = OrganizationSerializer(
            instance=instance, data=data, partial=True,
            context={'request': info.context.request}
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateOrganization(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateOrganization(result=instance, errors=None, ok=True)


class DeleteOrganization(graphene.Mutation):
    """
    The DeleteOrganization class is a mutation class that is used to delete an organization object from the database.

    Arguments:
        id (graphene.ID): The ID of the organization to be deleted. This argument is required.

    Attributes:
        errors (graphene.List[graphene.NonNull[CustomErrorType]]): A list of errors that occurred during the mutation process.
        ok (graphene.Boolean): Indicates whether the mutation was successful or not.
        result (graphene.Field[OrganizationType]): The deleted organization object.

    Methods:
        mutate(root, info, id):
            This method is a static method that performs the mutation operation.

            Parameters:
                root: The root value or object.
                info: The resolver info.
                id (graphene.ID): The ID of the organization to be deleted.

            Returns:
                DeleteOrganization: The mutated DeleteOrganization object.

    Usage:
        To delete an organization, create a DeleteOrganization object and call the mutate method with the appropriate arguments.

    Example:
        delete_org = DeleteOrganization()
        result = delete_org.mutate(root, info, id)
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(OrganizationType)

    @staticmethod
    @permission_checker(['organization.delete_organization'])
    def mutate(root, info, id):
        try:
            instance = Organization.objects.get(id=id)
        except Organization.DoesNotExist:
            return DeleteOrganization(errors=[
                dict(field='nonFieldErrors', messages=gettext('Organization does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteOrganization(result=instance, errors=None, ok=True)


class ExportOrganizations(ExportBaseMutation):
    """

    This class is responsible for exporting organizations data in Excel format.

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = OrganizationFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.ORGANIZATION


class Mutation(object):
    """
    This class represents a collection of mutation fields for performing various operations on organizations.

    Attributes:
        create_organization: A GraphQL mutation field for creating a new organization.
        update_organization: A GraphQL mutation field for updating an existing organization.
        delete_organization: A GraphQL mutation field for deleting an organization.
        create_organization_kind: A GraphQL mutation field for creating a new organization kind.
        update_organization_kind: A GraphQL mutation field for updating an existing organization kind.
        delete_organization_kind: A GraphQL mutation field for deleting an organization kind.
        export_organizations: A GraphQL mutation field for exporting a list of organizations.

    Note: This class does not contain any methods, as it is intended to be used as a collection of mutation fields.
    """
    create_organization = CreateOrganization.Field()
    update_organization = UpdateOrganization.Field()
    delete_organization = DeleteOrganization.Field()
    create_organization_kind = CreateOrganizationKind.Field()
    update_organization_kind = UpdateOrganizationKind.Field()
    delete_organization_kind = DeleteOrganizationKind.Field()
    export_organizations = ExportOrganizations.Field()

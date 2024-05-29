import graphene
from django.utils.translation import gettext

from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker
from utils.mutation import generate_input_type_for_serializer
from apps.contrib.models import ExcelDownload
from apps.contrib.mutations import ExportBaseMutation
from apps.crisis.models import Crisis
from apps.crisis.filters import CrisisFilterDataInputType
from apps.crisis.schema import CrisisType
from apps.crisis.serializers import CrisisSerializer, CrisisUpdateSerializer

CrisisCreateInputType = generate_input_type_for_serializer(
    'CrisisCreateInputType',
    CrisisSerializer
)

CrisisUpdateInputType = generate_input_type_for_serializer(
    'CrisisUpdateInputType',
    CrisisUpdateSerializer,
)


class CreateCrisis(graphene.Mutation):
    """
        This class represents a GraphQL mutation for creating a crisis.

        Args:
            graphene.Mutation: The base mutation class from the Graphene library.

        Attributes:
            Arguments: A nested class that defines the input arguments for the mutation.
            - data (CrisisCreateInputType): The data needed to create a crisis.

            errors (List[CustomErrorType]): A list of custom error types.
            ok (bool): A boolean indicating the success of the mutation.
            result (CrisisType): The created crisis object.

        Methods:
            mutate: A static method that defines the logic for executing the mutation.

        Examples:
            # To create a crisis
            mutation {
              createCrisis(data: { name: "Natural Disaster", description: "Hurricane", date: "2022-10-15" }) {
                result {
                  id
                  name
                  description
                  date
                }
                errors {
                  code
                  message
                }
                ok
              }
            }
    """
    class Arguments:
        data = CrisisCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(CrisisType)

    @staticmethod
    @permission_checker(['crisis.add_crisis'])
    def mutate(root, info, data):
        serializer = CrisisSerializer(data=data, context=dict(request=info.context.request))
        if errors := mutation_is_not_valid(serializer):
            return CreateCrisis(errors=errors, ok=False)
        instance = serializer.save()
        return CreateCrisis(result=instance, errors=None, ok=True)


class UpdateCrisis(graphene.Mutation):
    """

    The `UpdateCrisis` class is a subclass of `graphene.Mutation` and is used to update an existing Crisis object. It takes a `data` argument of type `CrisisUpdateInputType`, which is required.

    Attributes:
    - `errors`: A list of `CustomErrorType` objects that represent any errors encountered during the update process. It is a non-null list as specified by `graphene.NonNull`.
    - `ok`: A boolean value indicating the success or failure of the update operation.
    - `result`: A `CrisisType` object representing the updated Crisis instance.

    Methods:
    - `mutate`: A static method decorated with `@staticmethod` and `@permission_checker(['crisis.change_crisis'])`. It performs the update operation by retrieving the Crisis instance based on the provided data's ID, then using the `CrisisSerializer` to update the instance with the provided data. If any validation errors occur, the `mutation_is_not_valid` function is called to handle the errors.

    """
    class Arguments:
        data = CrisisUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(CrisisType)

    @staticmethod
    @permission_checker(['crisis.change_crisis'])
    def mutate(root, info, data):
        try:
            instance = Crisis.objects.get(id=data['id'])
        except Crisis.DoesNotExist:
            return UpdateCrisis(errors=[
                dict(field='nonFieldErrors', messages=gettext('Crisis does not exist.'))
            ])
        serializer = CrisisSerializer(
            instance=instance,
            data=data,
            context=dict(request=info.context),
            partial=True
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateCrisis(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateCrisis(result=instance, errors=None, ok=True)


class DeleteCrisis(graphene.Mutation):
    """
    Mutation to delete a crisis by ID.

    Args:
        id (str): The ID of the crisis to be deleted.

    Returns:
        DeleteCrisis: The mutation response object.

    Raises:
        None.

    Example Usage:
        mutation {
            deleteCrisis(id: "1") {
                result {
                    id
                    name
                    description
                }
                errors {
                    field
                    messages
                }
                ok
            }
        }
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(CrisisType)

    @staticmethod
    @permission_checker(['crisis.delete_crisis'])
    def mutate(root, info, id):
        try:
            instance = Crisis.objects.get(id=id)
        except Crisis.DoesNotExist:
            return DeleteCrisis(errors=[
                dict(field='nonFieldErrors', messages=gettext('Crisis does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteCrisis(result=instance, errors=None, ok=True)


class ExportCrises(ExportBaseMutation):
    """
    ExportCrises class for exporting crisis data in Excel format

    This class extends the ExportBaseMutation class and provides functionality to export crisis data in Excel format.

    Attributes:
        DOWNLOAD_TYPE (str): Constant defining the download type as 'CRISIS'.

    Args:
        filters (CrisisFilterDataInputType): The input data for filtering crisis data.

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = CrisisFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.CRISIS


class Mutation(object):
    """
    Class representing a set of mutation fields for managing crises

    Attributes:
        create_crisis (CreateCrisis.Field): Field for creating a new crisis
        update_crisis (UpdateCrisis.Field): Field for updating an existing crisis
        delete_crisis (DeleteCrisis.Field): Field for deleting a crisis
        export_crises (ExportCrises.Field): Field for exporting a list of crises
    """
    create_crisis = CreateCrisis.Field()
    update_crisis = UpdateCrisis.Field()
    delete_crisis = DeleteCrisis.Field()
    export_crises = ExportCrises.Field()

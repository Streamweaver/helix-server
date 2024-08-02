import graphene
from django.db import transaction
from utils.mutation import generate_input_type_for_serializer
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker, is_authenticated
from django.utils.translation import gettext
from .serializers import StatusLogSerializer, ReleaseMetadataSerializer
from .schema import GiddStatusLogType, GiddReleaseMetadataType
from .tasks import update_gidd_data
from .models import StatusLog


class GiddUpdateData(graphene.Mutation):
    """
    Class: GiddUpdateData

    This class is a mutation class that updates GIDD (Graphene Is Django Database) data through a GraphQL mutation. It
    is used to update the GIDD data in the background.

    Attributes:
        errors (List[CustomErrorType]): A list of CustomErrorType objects representing any errors that occurred during
        the mutation.
        ok (Boolean): A boolean value indicating if the mutation was successful or not.
        result (GiddStatusLogType): A GiddStatusLogType object representing the updated GIDD status log.

    Methods:
        mutate(root, info):
            This static method is the entry point for the GraphQL mutation. It is decorated with the @staticmethod,
            @is_authenticated, and @permission_checker decorators to handle authentication and permission checks. It
            takes the 'root' and 'info' parameters, which are provided by the GraphQL framework.

            Parameters:
                root: The root value of the GraphQL query.
                info: The GraphQL ResolveInfo object containing information about the query and the execution context.

            Returns:
                GiddUpdateData: A GiddUpdateData object representing the result of the mutation.

    Usage:
        # Instantiate the GiddUpdateData class and call the 'mutate' method
        gidd_update_data = GiddUpdateData()
        result = gidd_update_data.mutate(root, info)
    """
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(GiddStatusLogType)

    @staticmethod
    @is_authenticated()
    @permission_checker(['gidd.update_gidd_data_gidd'])
    def mutate(root, info):
        user = info.context.user
        # Check if any pending updates
        status_log = StatusLog.objects.last()
        if status_log and status_log.status == StatusLog.Status.PENDING:
            return GiddUpdateData(
                errors=[dict(
                    field='nonFieldErrors',
                    messages=gettext(
                        'Generating GIDD data in background, you can re-generate once generation will complete'
                    )
                )],
                ok=False
            )

        serializer = StatusLogSerializer(data=dict(triggered_by=user.id))
        if errors := mutation_is_not_valid(serializer):
            return GiddUpdateData(errors=errors, ok=False)
        instance = serializer.save()
        # Update date in background
        transaction.on_commit(lambda: update_gidd_data.delay(log_id=instance.id))
        return GiddUpdateData(result=instance, errors=None, ok=True)


GiddReleaseMetadataInputType = generate_input_type_for_serializer(
    'ReleaseMetadataInputType',
    ReleaseMetadataSerializer,
)


class GiddUpdateReleaseMetaData(graphene.Mutation):
    """
    This class represents a mutation in the GiddUpdateReleaseMetaData module.

    Class Attributes:
    - Arguments: A nested class defining the arguments for the mutation. It has one required argument 'data' of type
    GiddReleaseMetadataInputType.
    - errors: A List of CustomErrorType objects representing any errors that occurred during the mutation.
    - ok: A Boolean indicating whether the mutation was successful or not.
    - result: A field of type GiddReleaseMetadataType representing the result of the mutation.

    Methods:
    - mutate: A static method decorated with the @staticmethod decorator. It takes three parameters: 'root', 'info', and
    'data'.
      - The 'root' parameter is the root object of the schema.
      - The 'info' parameter contains information about the execution state of the query, including the GraphQL schema
      and request context.
      - The 'data' parameter is the input data for the mutation.
      - This method performs the mutation logic, including validation, serialization, and saving the data.
      - If any errors occur during the mutation, they are returned as a List of CustomErrorType objects.
      - The 'ok' attribute is set to False if there are any errors, and True otherwise.
      - The 'result' attribute is set to the saved instance of ReleaseMetadataSerializer.
      - The 'update_gidd_data' task is also scheduled to run in the background after the transaction is committed.

    Example usage:

    mutation {
      GiddUpdateReleaseMetaData(data: { ... }) {
        errors {
          ...
        }
        ok
        result {
          ...
        }
      }
    }
    """
    class Arguments:
        data = GiddReleaseMetadataInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(GiddReleaseMetadataType)

    @staticmethod
    @is_authenticated()
    @permission_checker(['gidd.update_release_meta_data_gidd'])
    def mutate(root, info, data):
        serializer = ReleaseMetadataSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return GiddUpdateReleaseMetaData(errors=errors, ok=False)
        instance = serializer.save()
        # FIXME: We should not call update_gidd_data when setting metadata
        # NOTE: Update date in background
        transaction.on_commit(lambda: update_gidd_data.delay(log_id=instance.id))
        return GiddUpdateReleaseMetaData(result=instance, errors=None, ok=True)


class Mutation(object):
    """
    Mutation class for updating data and release metadata in Gidd.

    Attributes:
        gidd_update_data (Field): Field for updating data in Gidd.
        gidd_update_release_meta_data (Field): Field for updating release metadata in Gidd.
    """
    gidd_update_data = GiddUpdateData.Field()
    gidd_update_release_meta_data = GiddUpdateReleaseMetaData.Field()

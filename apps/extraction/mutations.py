from django.utils.translation import gettext
import graphene

from apps.extraction.models import ExtractionQuery
from apps.extraction.serializers import ExtractionQuerySerializer, ExtractionQueryUpdateSerializer
from apps.extraction.schema import (
    ExtractionQueryObjectType,
)
from utils.mutation import generate_input_type_for_serializer
from utils.error_types import CustomErrorType, mutation_is_not_valid

CreateExtractInputType = generate_input_type_for_serializer(
    'CreateExtractInputType',
    ExtractionQuerySerializer
)

UpdateExtractInputType = generate_input_type_for_serializer(
    'UpdateExtractInputType',
    ExtractionQueryUpdateSerializer
)


class CreateExtraction(graphene.Mutation):
    """
    Class: CreateExtraction

    This class is a Graphene mutation that creates an extraction.

    Usage:
        mutation createExtraction {
            createExtraction(data: CreateExtractInputType!): CreateExtractionPayload
        }

    Attributes:
        - data: Required argument of type CreateExtractInputType. Contains the data for creating the extraction.

        - errors: List of CustomErrorType objects. Contains any errors encountered during the mutation.

        - ok: Boolean value indicating the success or failure of the mutation.

        - result: Object of type ExtractionQueryObjectType. Contains the created extraction object if the mutation was successful.

    Methods:
        - mutate(root, info, data): Static method used to perform the mutation.

    """
    class Arguments:
        data = CreateExtractInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ExtractionQueryObjectType)

    @staticmethod
    def mutate(root, info, data):  # noqa
        serializer = ExtractionQuerySerializer(data=data,
                                               context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):  # noqa
            return CreateExtraction(errors=errors, ok=False)
        instance = serializer.save()
        return CreateExtraction(result=instance, errors=None, ok=True)


class UpdateExtraction(graphene.Mutation):
    """

    The `UpdateExtraction` class is a mutation in the Graphene library for updating an instance of the `ExtractionQuery` model. It takes a `data` argument of type `UpdateExtractInputType` which is required.

    Attributes:
    - `errors`: A list of `CustomErrorType` objects representing any errors that occurred during the mutation.
    - `ok`: A boolean value indicating whether the mutation was successful or not.
    - `result`: A `ExtractionQueryObjectType` object representing the updated instance of the `ExtractionQuery` model.

    Methods:
    - `mutate(root, info, data)`: A static method that performs the mutation. It takes the following arguments:
        - `root`: The root value that was passed to the GraphQL execution engine.
        - `info`: An execution information object containing information about the execution.
        - `data`: The input data for the mutation.

    The `mutate` method first tries to retrieve an instance of the `ExtractionQuery` model using the provided `id` and the currently authenticated user. If the instance does not exist, it returns an error object indicating that the extraction query does not exist.

    Next, it creates a serializer object of type `ExtractionQuerySerializer` with the instance and the input data. The serializer is initialized with a context object containing the request from the execution information.

    If the serializer is not valid, meaning it failed to validate the input data, it returns an error object containing the validation errors.

    If the serializer is valid, it saves the instance using the serializer and returns a response object with the updated instance and no errors.

    """
    class Arguments:
        data = UpdateExtractInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ExtractionQueryObjectType)

    @staticmethod
    def mutate(root, info, data):  # noqa
        try:
            instance = ExtractionQuery.objects.get(id=data['id'],
                                                   created_by=info.context.user)  # TODO: correct?
        except ExtractionQuery.DoesNotExist:
            return UpdateExtraction(errors=[
                dict(field='nonFieldErrors', messages=gettext('Extraction query does not exist.'))
            ])
        serializer = ExtractionQuerySerializer(instance=instance,
                                               data=data,
                                               context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):  # noqa
            return CreateExtraction(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateExtraction(result=instance, errors=None, ok=True)


class DeleteExtraction(graphene.Mutation):
    """
    The DeleteExtraction class is a mutation class in the Graphene library.

    Arguments:
        - id (required): The ID of the extraction query to be deleted.

    Attributes:
        - errors: A list of CustomErrorType objects representing any errors that occurred during the mutation.
        - ok: A boolean value indicating whether the mutation was successful.
        - result: A field representing the deleted ExtractionQuery object.

    Methods:
        - mutate(root, info, id): This static method is called to perform the mutation operation. It receives the root
                                  object, the info object, and the id argument as parameters. It attempts to retrieve the
                                  ExtractionQuery object specified by the id and created by the user making the request.
                                  If the object does not exist, it returns an error with a corresponding message. Otherwise,
                                  it deletes the object and returns a DeleteExtraction instance with the result field set
                                  to the deleted instance and the ok field set to True.

    Note: This class does not rely on any external libraries other than Graphene.
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ExtractionQueryObjectType)

    @staticmethod
    def mutate(root, info, id):
        try:
            instance = ExtractionQuery.objects.get(id=id,
                                                   created_by=info.context.user)  # TODO: correct?
        except ExtractionQuery.DoesNotExist:
            return DeleteExtraction(errors=[
                dict(field='nonFieldErrors', messages=gettext('Extraction query does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteExtraction(result=instance, errors=None, ok=True)


class Mutation:
    """
    This class represents a Mutation in the application.

    Attributes:
    - create_extraction: Field object representing the "create_extraction" mutation.
    - update_extraction: Field object representing the "update_extraction" mutation.
    - delete_extraction: Field object representing the "delete_extraction" mutation.
    """
    create_extraction = CreateExtraction.Field()
    update_extraction = UpdateExtraction.Field()
    delete_extraction = DeleteExtraction.Field()

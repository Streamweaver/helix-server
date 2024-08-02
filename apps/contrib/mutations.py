import graphene
import typing
from graphene_file_upload.scalars import Upload
from django.utils.translation import gettext
from utils.mutation import generate_input_type_for_serializer

from utils.common import convert_date_object_to_string_in_dict
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import is_authenticated, permission_checker
from apps.contrib.filters import ClientFilterDataInputType
from apps.contrib.serializers import ExcelDownloadSerializer
from apps.contrib.models import ExcelDownload
from apps.contrib.schema import AttachmentType, ClientType, BulkApiOperationObjectType
from apps.contrib.bulk_operations.serializers import BulkApiOperationSerializer
from apps.contrib.serializers import (
    AttachmentSerializer,
    ClientSerializer,
    ClientUpdateSerializer,
)
from apps.contrib.models import (
    Client,
)
from .filters import ClientTrackInfoFilterDataInputType


BulkApiOperationInputType = generate_input_type_for_serializer(
    'BulkApiOperationInputType',
    serializer_class=BulkApiOperationSerializer,
)


class AttachmentCreateInputType(graphene.InputObjectType):
    """

    Class: AttachmentCreateInputType

    Description:
    This class represents the input type for creating a new attachment.

    Attributes:
    - attachment (required): The attachment file.
    - attachment_for (required): The identifier for the attachment's target object.

    """
    attachment = Upload(required=True)
    attachment_for = graphene.String(required=True)


class CreateAttachment(graphene.Mutation):
    """CreateAttachment Class

    This class represents a mutation to create an attachment. It is used to create an attachment by
    taking input data, validating it, and saving the instance in the database.

    Attributes:
        errors: A list of custom error types.
        ok: A boolean indicating whether the mutation was successful or not.
        result: The field representing the created attachment.

    Methods:
        mutate: A static method that performs the mutation by validating and saving the input data.

    Usage:
        mutation = CreateAttachment.mutate(root, info, data)
        result = mutation.result
        errors = mutation.errors
        ok = mutation.ok
    """
    class Arguments:
        data = AttachmentCreateInputType(required=True)

    errors = graphene.List(CustomErrorType)
    ok = graphene.Boolean()
    result = graphene.Field(AttachmentType)

    @staticmethod
    @is_authenticated()
    def mutate(root, info, data):
        serializer = AttachmentSerializer(data=data,
                                          context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateAttachment(errors=errors, ok=False)
        instance = serializer.save()
        return CreateAttachment(result=instance, errors=None, ok=True)


ClientCreateInputType = generate_input_type_for_serializer(
    'ClientCreateInputType',
    ClientSerializer,
)

ClientUpdateInputType = generate_input_type_for_serializer(
    'ClientUpdateInputType',
    ClientUpdateSerializer,
)


class CreateClient(graphene.Mutation):
    """
    Class: CreateClient

    A class that represents a GraphQL mutation for creating a client.

    Attributes:
    - errors (graphene.List[CustomErrorType]): A list of custom error types.
    - ok (graphene.Boolean): A boolean indicating if the mutation was successful.
    - result (graphene.Field[ClientType]): A field representing the created client.

    Methods:
    - mutate(root, info, data):
        A static method that performs the mutation to create a client.

        Parameters:
        - root: The root value or object.
        - info: The GraphQL ResolveInfo object.
        - data: The input data for creating the client.

        Returns:
        - If the mutation is valid and successful, it returns an instance of CreateClient with the created client object
        and no errors.
        - If the mutation is not valid, it returns an instance of CreateClient with the errors and ok set to False.
    """
    class Arguments:
        data = ClientCreateInputType(required=True)

    errors = graphene.List(CustomErrorType)
    ok = graphene.Boolean()
    result = graphene.Field(ClientType)

    @staticmethod
    @permission_checker(['contrib.add_client'])
    def mutate(root, info, data):
        serializer = ClientSerializer(
            data=data,
            context={'request': info.context.request}
        )
        if errors := mutation_is_not_valid(serializer):
            return CreateClient(errors=errors, ok=False)
        instance = serializer.save()
        return CreateClient(result=instance, errors=None, ok=True)


class UpdateClient(graphene.Mutation):
    """
    UpdateClient class is a mutation class in a GraphQL schema that is used to update a client object.

    Attributes:
        Arguments: A nested class that defines the arguments required for the mutation.
            - data: An instance of the ClientUpdateInputType class, representing the data to update the client object.

        errors: A list of CustomErrorType objects. Represents any errors that occurred during the mutation.
        ok: A boolean value indicating the success of the mutation.
        result: An instance of the ClientType class representing the updated client object.

    Methods:
        mutate(root, info, data):
            Static method that performs the mutation operation.

            Parameters:
                root: The root object. Not used in this method.
                info: The GraphQL ResolveInfo object containing information about the query.
                data: The data to update the client object.

            Returns:
                If the client object with the specified ID does not exist, it returns an instance of the
                ClientUpdateSerializer class with an error object.
                If the mutation data is not valid, it returns an instance of the UpdateClient class with error objects.
                Otherwise, it updates the client object and returns an instance of the UpdateClient class with the
                updated client.
    """
    class Arguments:
        data = ClientUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ClientType)

    @staticmethod
    @permission_checker(['contrib.change_client'])
    def mutate(root, info, data):
        try:
            instance = Client.objects.get(id=data['id'])
        except Client.DoesNotExist:
            return ClientUpdateSerializer(errors=[
                dict(field='nonFieldErrors', messages=gettext('Client does not exist.'))
            ])
        serializer = ClientUpdateSerializer(
            instance=instance,
            data=data,
            context=dict(request=info.context),
            partial=True
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateClient(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateClient(result=instance, errors=None, ok=True)


class ExportBaseMutation(graphene.Mutation, abstract=True):
    """
    ExportBaseMutation

    This class is a base mutation class for exporting data. It is a subclass of graphene.Mutation and is designed to be
    extended by other mutation classes.

    Attributes:
        errors (List[CustomErrorType]): A list of custom error types.
        ok (bool): A boolean flag indicating the success of the mutation.

    Class Variables:
        DOWNLOAD_TYPE (ExcelDownload.DOWNLOAD_TYPES): A class variable representing the download type for the mutation.

    Methods:
        __init_subclass__(cls, **kwargs): Special method called when a subclass is created. It checks for the presence
        of required attributes and raises an error if any are missing.
        mutate(cls, _, info, filters): Executes the mutation. It creates an instance of ExcelDownloadSerializer and
        saves the data. Returns an instance of the class with the appropriate errors and success flag.

    """
    class Arguments:
        ...

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()

    DOWNLOAD_TYPE: typing.ClassVar[ExcelDownload.DOWNLOAD_TYPES]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        errors = []
        if not hasattr(cls, 'DOWNLOAD_TYPE'):
            errors.append(f"{cls.__name__} must have a 'DOWNLOAD_TYPE' attribute")
        if not hasattr(cls.Arguments, 'filters'):
            errors.append(f"{cls.__name__} must have a 'Arguments.filters' attribute")
        elif isinstance(getattr(cls.Arguments, 'filters'), graphene.InputField):
            errors.append(
                f"{cls.__name__} must have a 'Arguments.filters' attribute as InputField"
            )
        if errors:
            raise TypeError(errors)

    @classmethod
    def mutate(cls, _, info, filters):
        serializer = ExcelDownloadSerializer(
            data=dict(
                download_type=int(cls.DOWNLOAD_TYPE),
                filters=convert_date_object_to_string_in_dict(filters),
            ),
            context=dict(request=info.context.request)
        )
        if errors := mutation_is_not_valid(serializer):
            return cls(errors=errors, ok=False)
        serializer.save()
        return cls(errors=None, ok=True)


class ExportTrackingData(ExportBaseMutation):
    """
    ExportTrackingData is a class that extends ExportBaseMutation and is used for exporting tracking data.

    Attributes:
        DOWNLOAD_TYPE (str): The download type for the exported tracking data.

    Methods:
        Arguments: A class that extends ExportBaseMutation.Arguments and defines the arguments for exporting tracking
        data.

    Args:
        filters (ClientTrackInfoFilterDataInputType): The filters to be applied for exporting tracking data.

    Usage:
        To use the ExportTrackingData class, create an instance of it and provide the required arguments.

    Example:
        filters = ClientTrackInfoFilterDataInputType(...)
        export_data = ExportTrackingData(filters=filters)
    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = ClientTrackInfoFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.TRACKING_DATA


class ExportClients(ExportBaseMutation):
    """

    The ExportClients class is a subclass of the ExportBaseMutation class and is used for exporting client data in Excel
    format. It provides a method to execute the export operation.

    Attributes:
        DOWNLOAD_TYPE (str): The download type for exporting client data. The value is set to 'CLIENT' indicating the
        client download type.

    """
    class Arguments:
        filters = ClientFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.CLIENT


class TriggerBulkOperation(graphene.Mutation):
    """
    The `TriggerBulkOperation` class is a subclass of `graphene.Mutation` and represents a GraphQL mutation for
    triggering bulk operations.

    Attributes:
        Arguments:
            - data: An instance of the `BulkApiOperationInputType` class, which is a required argument for the mutation.

        errors: A list of `CustomErrorType` objects, representing any errors that occurred during the mutation.

        ok: A boolean value indicating the success or failure of the mutation.

        result: An instance of the `BulkApiOperationObjectType` class, representing the result of the mutation.

    Methods:
        mutate(_: Any, info: ResolveInfo, data: BulkApiOperationInputType) -> TriggerBulkOperation:
            This is a static method that handles the mutation logic. It takes three parameters:
                - _: An unused parameter.
                - info: An instance of the `ResolveInfo` class, which contains the GraphQL execution information.
                - data: An instance of the `BulkApiOperationInputType` class, providing the input data for the mutation.

            Returns:
                An instance of the `TriggerBulkOperation` class, with the appropriate attributes set based on the
                mutation logic.
    """
    class Arguments:
        data = BulkApiOperationInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(BulkApiOperationObjectType)

    @staticmethod
    # TODO: Define a proper permission
    # For now, this is handle at client level.
    # We do handle the permission internally as well.
    def mutate(_, info, data):
        serializer = BulkApiOperationSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return TriggerBulkOperation(errors=errors, ok=False)
        instance = serializer.save()
        return TriggerBulkOperation(result=instance, errors=None, ok=True)


class Mutation:
    """
    Class Mutation

    This class represents a collection of mutation fields that can be used to perform operations on the data.

    Attributes:
        create_attachment (Field): The field for creating an attachment.
        create_client (Field): The field for creating a client.
        update_client (Field): The field for updating a client.
        export_tracking_data (Field): The field for exporting tracking data.
        export_clients (Field): The field for exporting clients.
        trigger_bulk_operation (Field): The field for triggering a bulk operation.
    """
    create_attachment = CreateAttachment.Field()
    create_client = CreateClient.Field()
    update_client = UpdateClient.Field()
    export_tracking_data = ExportTrackingData.Field()
    export_clients = ExportClients.Field()
    trigger_bulk_operation = TriggerBulkOperation.Field()

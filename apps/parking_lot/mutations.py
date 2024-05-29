import graphene
from django.utils.translation import gettext

from utils.mutation import generate_input_type_for_serializer
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker
from utils.filters import generate_type_for_filter_set
from apps.contrib.mutations import ExportBaseMutation
from apps.contrib.models import ExcelDownload
from apps.parking_lot.models import ParkedItem
from apps.parking_lot.schema import ParkedItemType
from apps.parking_lot.serializers import ParkedItemSerializer, ParkedItemUpdateSerializer
from apps.parking_lot.filters import ParkingLotFilter


ParkedItemCreateInputType = generate_input_type_for_serializer(
    'ParkedItemCreateInputType',
    ParkedItemSerializer
)

ParkedItemUpdateInputType = generate_input_type_for_serializer(
    'ParkedItemUpdateInputType',
    ParkedItemUpdateSerializer
)

ParkedItemFilterDataType, ParkedItemFilterDataInputType = generate_type_for_filter_set(
    ParkingLotFilter,
    'parking_lot.schema.parking_lot_list',
    'ParkingLotFilterDataType',
    'ParkingLotFilterDataInputType',
)


class CreateParkedItem(graphene.Mutation):
    """
    A mutation class for creating a new ParkedItem.

    ...

    Attributes
    ----------
    Arguments : class
        The Arguments class for the mutation, containing the required 'data' argument.

    errors : list
        A list of CustomErrorType objects. Represents any errors that occurred during the mutation.

    ok : bool
        A boolean value indicating the success or failure of the mutation.

    result : ParkedItemType
        The ParkedItemType object representing the newly created ParkedItem.

    Methods
    -------
    mutate(root, info, data):
        Mutates the data and creates a new ParkedItem. Returns the appropriate CreateParkedItem object.

    """
    class Arguments:
        data = ParkedItemCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ParkedItemType)

    @staticmethod
    @permission_checker(['parking_lot.add_parkeditem'])
    def mutate(root, info, data):
        serializer = ParkedItemSerializer(data=data, context=dict(request=info.context.request))
        if errors := mutation_is_not_valid(serializer):
            return CreateParkedItem(errors=errors, ok=False)
        instance = serializer.save()
        return CreateParkedItem(result=instance, errors=None, ok=True)


class UpdateParkedItem(graphene.Mutation):
    """Class to update a ParkedItem

    Returns an instance of UpdateParkedItem with updated data.

    Args:
        graphene.Mutation: The parent class of UpdateParkedItem.

    Attributes:
        Arguments: The class that defines the arguments for the mutation.
        errors (graphene.List(graphene.NonNull(CustomErrorType))): A list of errors, if any.
        ok (graphene.Boolean): A boolean indicating if the mutation was successful.
        result (graphene.Field(ParkedItemType)): The updated ParkedItem instance.

    Methods:
        mutate(root, info, data): Static method to perform the mutation.

    """
    class Arguments:
        data = ParkedItemUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ParkedItemType)

    @staticmethod
    @permission_checker(['parking_lot.change_parkeditem'])
    def mutate(root, info, data):
        try:
            instance = ParkedItem.objects.get(id=data['id'])
        except ParkedItem.DoesNotExist:
            return UpdateParkedItem(errors=[
                dict(field='nonFieldErrors', messages=gettext('Parked item does not exist.'))
            ])
        serializer = ParkedItemSerializer(instance=instance, data=data, partial=True,
                                          context=dict(request=info.context.request))
        if errors := mutation_is_not_valid(serializer):
            return UpdateParkedItem(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateParkedItem(result=instance, errors=None, ok=True)


class DeleteParkedItem(graphene.Mutation):
    """
    DeleteParkedItem Class

    This class is responsible for deleting a parked item from the database.

    Attributes:
        - Arguments: A nested class that defines the input arguments for deleting the parked item.
          - id (graphene.ID): The ID of the parked item to be deleted.

        - errors (graphene.List[graphene.NonNull[CustomErrorType]]): A list of custom error messages.
        - ok (graphene.Boolean): A flag indicating if the deletion was successful.
        - result (graphene.Field[ParkedItemType]): The deleted parked item.

    Methods:
        - mutate: A static method that performs the deletion of the parked item.

    Example Usage:
        TODO: Add example usage here.

    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ParkedItemType)

    @staticmethod
    @permission_checker(['parking_lot.delete_parkeditem'])
    def mutate(root, info, id):
        try:
            instance = ParkedItem.objects.get(id=id)
        except ParkedItem.DoesNotExist:
            return DeleteParkedItem(errors=[
                dict(
                    field='nonFieldErrors',
                    messages=gettext('Only creator is allowed to delete the parked item.')
                )
            ])
        instance.delete()
        instance.id = id
        return DeleteParkedItem(result=instance, errors=None, ok=True)


class ExportParkedItem(ExportBaseMutation):
    """
    Class representing an export of parked items.

    This class is a subclass of ExportBaseMutation and provides additional functionality specific to exporting parked items.

    Attributes:
        DOWNLOAD_TYPE (str): The type of download, which is set to "PARKING_LOT" for parked items.

    Args:
        filters (ParkedItemFilterDataInputType): The input data type for filtering parked items. Required argument.

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = ParkedItemFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.PARKING_LOT


class Mutation(object):
    """
    The `Mutation` class represents a collection of mutation fields for managing parked items.

    Attributes:
        create_parked_item (Field): Field for creating a new parked item.
        update_parked_item (Field): Field for updating an existing parked item.
        delete_parked_item (Field): Field for deleting a parked item.
        export_parked_item (Field): Field for exporting a parked item.

    """
    create_parked_item = CreateParkedItem.Field()
    update_parked_item = UpdateParkedItem.Field()
    delete_parked_item = DeleteParkedItem.Field()
    export_parked_item = ExportParkedItem.Field()

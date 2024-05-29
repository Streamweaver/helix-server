from django.utils.translation import gettext
import graphene

from utils.mutation import generate_input_type_for_serializer
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker
from apps.contrib.models import ExcelDownload
from apps.contrib.mutations import ExportBaseMutation
from apps.contact.models import Contact, Communication
from apps.contact.filters import ContactFilterDataInputType
from apps.contact.schema import ContactType, CommunicationType
from apps.contact.serializers import (
    ContactSerializer,
    CommunicationSerializer,
    ContactUpdateSerializer,
    CommunicationUpdateSerializer,
)

ContactCreateInputType = generate_input_type_for_serializer(
    'ContactCreateInputType',
    ContactSerializer
)


ContactUpdateInputType = generate_input_type_for_serializer(
    'ContactUpdateInputType',
    ContactUpdateSerializer
)


class CreateContact(graphene.Mutation):
    """
        A class representing a mutation to create a contact.

        Attributes:
            data (dict): The data required to create the contact.
            errors (list[CustomErrorType]): A list of custom error types if the mutation is not valid.
            ok (bool): A boolean indicating if the mutation was successful.
            result (ContactType): The result of the mutation, if successful.
    """
    class Arguments:
        data = ContactCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ContactType)

    @staticmethod
    @permission_checker(['contact.add_contact'])
    def mutate(root, info, data):
        serializer = ContactSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateContact(errors=errors, ok=False)
        instance = serializer.save()
        return CreateContact(result=instance, errors=None, ok=True)


class UpdateContact(graphene.Mutation):
    """

    The UpdateContact class is a mutation class used to update an existing contact record. It is a subclass of the graphene.Mutation class.

    Attributes:
    - errors: A list of CustomErrorType objects representing any validation or error messages.
    - ok: A boolean indicating whether the mutation was successful or not.
    - result: A ContactType object representing the updated contact record.

    Methods:
    - mutate(root, info, data): A static method used to perform the mutation operation. It takes three parameters:
       - root: The root object of the mutation.
       - info: An object containing metadata about the execution.
       - data: The input data for updating the contact record.

    Usage Example:
    mutation {
      updateContact(data: { id: 1, name: "John Doe", email: "john@example.com" }) {
        result {
          name
          email
        }
        ok
        errors {
          field
          messages
        }
      }
    }

    """
    class Arguments:
        data = ContactUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ContactType)

    @staticmethod
    @permission_checker(['contact.change_contact'])
    def mutate(root, info, data):
        try:
            instance = Contact.objects.get(id=data['id'])
        except Contact.DoesNotExist:
            return UpdateContact(errors=[
                dict(field='nonFieldErrors', messages=gettext('Contact does not exist.'))
            ])
        serializer = ContactSerializer(
            instance=instance,
            data=data,
            partial=True,
            context={'request': info.context.request}
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateContact(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateContact(result=instance, errors=None, ok=True)


class DeleteContact(graphene.Mutation):
    """
    The DeleteContact class is a graphene mutation for deleting a contact. It inherits from the Mutation class provided by graphene.

    Attributes:
        Arguments:
            - id (graphene.ID): The ID of the contact to be deleted. This argument is required.

        errors (graphene.List): A list of CustomErrorType objects representing any errors that occurred during the mutation.

        ok (graphene.Boolean): A boolean indicating whether the deletion was successful or not.

        result (graphene.Field): A field representing the deleted contact.

    Methods:
        mutate(root, info, id):
            This is a static method used to perform the deletion of the contact.

            Args:
                - root: The root value passed by the graphene framework.
                - info: The GraphQL execution information.
                - id (graphene.ID): The ID of the contact to be deleted.

            Returns:
                - If the contact with the given ID does not exist, an UpdateContact mutation with appropriate error message is returned.
                - If the contact is successfully deleted, a DeleteContact mutation with the deleted contact and no errors is returned.
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ContactType)

    @staticmethod
    @permission_checker(['contact.delete_contact'])
    def mutate(root, info, id):
        try:
            instance = Contact.objects.get(id=id)
        except Contact.DoesNotExist:
            return UpdateContact(errors=[
                dict(field='nonFieldErrors', messages=gettext('Contact does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteContact(result=instance, errors=None, ok=True)


# Communication #

CommunicationCreateInputType = generate_input_type_for_serializer(
    'CommunicationCreateInputType',
    CommunicationSerializer
)

CommunicationUpdateInputType = generate_input_type_for_serializer(
    'CommunicationUpdateInputType',
    CommunicationUpdateSerializer
)


class CreateCommunication(graphene.Mutation):
    """

    CreateCommunication

    This class represents a GraphQL mutation for creating a communication.

    Attributes:
        Arguments: A nested class specifying the arguments for the mutation.

    Methods:
        mutate(root, info, data)
            Executes the mutation and creates a new communication.


    """
    class Arguments:
        data = CommunicationCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(CommunicationType)

    @staticmethod
    def mutate(root, info, data):
        serializer = CommunicationSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateCommunication(errors=errors, ok=False)
        instance = serializer.save()
        return CreateCommunication(result=instance, errors=None, ok=True)


class UpdateCommunication(graphene.Mutation):
    """
        This class represents a GraphQL mutation for updating a Communication object.

        Args:
            graphene.Mutation: The base class for GraphQL mutations.

        Attributes:
            data (graphene.Argument): The argument for the update data input.
            errors (graphene.List[graphene.NonNull(CustomErrorType)]): A list of custom error types.
            ok (graphene.Boolean): A boolean indicating if the update was successful.
            result (graphene.Field(CommunicationType)): The updated Communication object.
    """
    class Arguments:
        data = CommunicationUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(CommunicationType)

    @staticmethod
    def mutate(root, info, data):
        try:
            instance = Communication.objects.get(id=data['id'])
        except Communication.DoesNotExist:
            return UpdateCommunication(errors=[
                dict(field='nonFieldErrors', messages=gettext('Communication does not exist.'))
            ])
        serializer = CommunicationSerializer(
            instance=instance,
            data=data,
            partial=True,
            context={'request': info.context.request}
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateCommunication(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateCommunication(result=instance, errors=None, ok=True)


class DeleteCommunication(graphene.Mutation):
    """
    The DeleteCommunication class is a mutation class that is used to delete a Communication instance.

    Attributes:
        - id (graphene.ID): The ID of the Communication instance to be deleted.

    Returns:
        - errors (List[CustomErrorType]): A list of custom error messages.
        - ok (Boolean): Flag indicating if the deletion was successful.
        - result (CommunicationType): The deleted Communication instance.

    Methods:
        - mutate(root, info, id): Static method used to perform the deletion of the Communication instance.

    Example Usage:
        mutation {
            deleteCommunication(id: "<communication_id>") {
                errors {
                    field
                    messages
                }
                ok
                result {
                    <communication_fields>
                }
            }
        }
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(CommunicationType)

    @staticmethod
    def mutate(root, info, id):
        try:
            instance = Communication.objects.get(id=id)
        except Communication.DoesNotExist:
            return DeleteCommunication(errors=[
                dict(field='nonFieldErrors', messages=gettext('Communication does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteCommunication(result=instance, errors=None, ok=True)


class ExportContacts(ExportBaseMutation):
    """
    Class: ExportContacts

    This class is used to export contacts to an Excel file.

    Methods:

        __init__(self, context: Context, filters: ContactFilterDataInputType)
            Constructor method for the ExportContacts class.

                Parameters:
                    - context (Context): The context of the GraphQL query.
                    - filters (ContactFilterDataInputType): The filter parameters for exporting contacts.

        export(self) -> bytes
            Exports the contacts to an Excel file and returns the file as bytes.

                Returns:
                    - bytes: The Excel file as bytes.

    Attributes:

        DOWNLOAD_TYPE: ExcelDownload.DOWNLOAD_TYPES
            The download type for exporting contacts.

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = ContactFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.CONTACT


class Mutation(object):
    """

    Class: Mutation

    The Mutation class represents a set of GraphQL fields used for performing mutations on contacts and communications.

    Instance Variables:
        - create_contact: A GraphQL field for creating a contact.
        - update_contact: A GraphQL field for updating a contact.
        - delete_contact: A GraphQL field for deleting a contact.
        - create_communication: A GraphQL field for creating a communication.
        - update_communication: A GraphQL field for updating a communication.
        - delete_communication: A GraphQL field for deleting a communication.
        - export_contacts: A GraphQL field for exporting contacts.

    Usage:

        mutation = Mutation()
        mutation.create_contact  # Use this field to create a new contact.
        mutation.update_contact  # Use this field to update an existing contact.
        mutation.delete_contact  # Use this field to delete a contact.
        mutation.create_communication  # Use this field to create a new communication.
        mutation.update_communication  # Use this field to update an existing communication.
        mutation.delete_communication  # Use this field to delete a communication.
        mutation.export_contacts  # Use this field to export contacts.

    """
    create_contact = CreateContact.Field()
    update_contact = UpdateContact.Field()
    delete_contact = DeleteContact.Field()
    create_communication = CreateCommunication.Field()
    update_communication = UpdateCommunication.Field()
    delete_communication = DeleteCommunication.Field()
    export_contacts = ExportContacts.Field()

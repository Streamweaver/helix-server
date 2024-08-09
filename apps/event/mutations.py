import graphene
from django.utils import timezone
from django.utils.translation import gettext

from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker
from utils.mutation import generate_input_type_for_serializer
from apps.contrib.models import ExcelDownload
from apps.contrib.mutations import ExportBaseMutation
from apps.event.models import Event, Actor, ContextOfViolence
from apps.event.filters import (
    ActorFilterDataInputType,
    EventFilterDataInputType,
    ContextOfViolenceFilterDataInputType,
)
from apps.event.schema import EventType, ActorType, ContextOfViolenceType
from apps.event.serializers import (
    EventSerializer,
    EventUpdateSerializer,
    ActorSerializer,
    ActorUpdateSerializer,
    CloneEventSerializer,
    ContextOfViolenceSerializer,
    ContextOfViolenceUpdateSerializer
)
from apps.notification.models import Notification


ActorCreateInputType = generate_input_type_for_serializer(
    'ActorCreateInputType',
    ActorSerializer
)


ActorUpdateInputType = generate_input_type_for_serializer(
    'ActorUpdateInputType',
    ActorUpdateSerializer
)


class CreateActor(graphene.Mutation):
    """

    The `CreateActor` class is a mutation class in the application. It is responsible for creating new actor instances.

    Attributes:
        data (ActorCreateInputType): The input data for creating an actor instance.
        errors (List[CustomErrorType]): A list of custom errors that might occur during the mutation.
        ok (Boolean): A boolean value indicating the success or failure of the mutation.
        result (ActorType): The created actor instance.

    Methods:
        mutate(root, info, data):
            This method is responsible for executing the mutation. It takes three parameters: `root`, `info`, and
            `data`.
            - `root`: The root value of the GraphQL query, unused in this context.
            - `info`: The GraphQLResolveInfo object that contains information about the execution state.
            - `data`: The input data for creating the actor instance.

            The method performs the following steps:
            1. Checks the permission for creating a new actor.
            2. Serializes the input data using the `ActorSerializer` with the context from the request.
            3. Checks if there are any validation errors in the serialization process.
            4."""
    class Arguments:
        data = ActorCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ActorType)

    @staticmethod
    @permission_checker(['event.add_actor'])
    def mutate(root, info, data):
        serializer = ActorSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateActor(errors=errors, ok=False)
        instance = serializer.save()
        return CreateActor(result=instance, errors=None, ok=True)


class UpdateActor(graphene.Mutation):
    """
    The UpdateActor class is a GraphQL mutation that allows updating an actor object in the system.

    Attributes:
    - data: An argument of type ActorUpdateInputType that is required for the mutation.

    - errors: A list of CustomErrorType objects that represent any errors that occurred during the mutation.

    - ok: A boolean value that indicates the success or failure of the mutation.

    - result: A field of type ActorType that represents the updated actor object.

    Methods:
    - mutate: A static method decorated with the permission_checker decorator that performs the mutation operation. It
    takes three parameters:

      - root: The root object for the query or mutation.

      - info: An object that provides information about the execution context.

      - data: The input data for the mutation.

      The method first attempts to retrieve the actor object with the given ID from the database. If the actor does not
      exist, it returns an UpdateActor object with an error indicating that the actor does not exist.

      It then creates an instance of the ActorSerializer with the retrieved actor object and the input data. The
      serializer is initialized with the context containing the request object from the info context.

      If any validation errors occur during"""
    class Arguments:
        data = ActorUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ActorType)

    @staticmethod
    @permission_checker(['event.change_actor'])
    def mutate(root, info, data):
        try:
            instance = Actor.objects.get(id=data['id'])
        except Actor.DoesNotExist:
            return UpdateActor(errors=[
                dict(field='nonFieldErrors', messages=gettext('Actor does not exist.'))
            ])
        serializer = ActorSerializer(instance=instance, data=data,
                                     context=dict(request=info.context.request), partial=True)
        if errors := mutation_is_not_valid(serializer):
            return UpdateActor(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateActor(result=instance, errors=None, ok=True)


class DeleteActor(graphene.Mutation):
    """
    DeleteActor class is a mutation class in the graphene library. It allows the deletion of an Actor object.

    Arguments:
        - id: Required argument of type ID, represents the unique identifier of the Actor to be deleted.

    Attributes:
        - errors: List of CustomErrorType objects, represents any errors that occurred during the mutation.
        - ok: Boolean value indicating the success of the mutation.
        - result: Field of type ActorType, represents the deleted Actor object.

    Methods:
        - mutate: Static method decorator that performs the deletion of the Actor object. It verifies the permission
        'event.delete_actor', retrieves the Actor instance based on the provided id, and deletes it. If the Actor does
        not exist, it returns a DeleteActor object with an error message. Otherwise, it returns a DeleteActor object
        with the deleted Actor instance, no errors, and ok set to True.

    Usage example:

    mutation {
      deleteActor(id: "12345") {
        ok
        errors {
          field
          messages
        }
        result {
          id
          name
          # Other fields of ActorType
        }
      }
    }
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ActorType)

    @staticmethod
    @permission_checker(['event.delete_actor'])
    def mutate(root, info, id):
        try:
            instance = Actor.objects.get(id=id)
        except Actor.DoesNotExist:
            return DeleteActor(errors=[
                dict(field='nonFieldErrors', messages=gettext('Actor does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteActor(result=instance, errors=None, ok=True)


EventCreateInputType = generate_input_type_for_serializer(
    'EventCreateInputType',
    EventSerializer
)


EventUpdateInputType = generate_input_type_for_serializer(
    'EventUpdateInputType',
    EventUpdateSerializer
)


class CreateEvent(graphene.Mutation):
    """
    CreateEvent Class

    This class represents a mutation to create an event in the system.

    Attributes:
        data (EventCreateInputType): The input data for creating an event.
        errors (List[CustomErrorType]): A list of custom error types.
        ok (bool): Indicates whether the mutation was successful.
        result (EventType): The created event object.

    Methods:
        mutate(root, info, data)
            Executes the mutation to create an event.

    """
    class Arguments:
        data = EventCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EventType)

    @staticmethod
    @permission_checker(['event.add_event'])
    def mutate(root, info, data):
        serializer = EventSerializer(data=data, context=dict(request=info.context.request))
        if errors := mutation_is_not_valid(serializer):
            return CreateEvent(errors=errors, ok=False)
        instance = serializer.save()
        return CreateEvent(result=instance, errors=None, ok=True)


class UpdateEvent(graphene.Mutation):
    """
    The UpdateEvent class is a subclass of graphene.Mutation. It represents a GraphQL mutation that is used to update an
    event.

    Attributes:
        Arguments (class attribute): Defines the arguments required for the mutation. It includes a single argument
        'data',
                                    which is of type EventUpdateInputType and is required.

        errors (class attribute): A List of CustomErrorType objects. It represents any errors that occur during the
        mutation.

        ok (class attribute): A Boolean value indicating the success or failure of the mutation.

        result (class attribute): A Field of type EventType. It represents the updated event.

    Methods:
        mutate(root, info, data): A static method that performs the mutation. It takes three arguments - root, info, and
        data.

            Parameters:
                root: The root value provided by the GraphQL resolver.

                info: The ResolveInfo object provided by the GraphQL resolver.

                data: The input data for the mutation, of type EventUpdateInputType.

            Returns:
                If the event with the specified ID does not exist, it returns an instance of UpdateEvent with errors set
                to a list containing a single error dictionary with the fields 'field' set to"""
    class Arguments:
        data = EventUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EventType)

    @staticmethod
    @permission_checker(['event.change_event'])
    def mutate(root, info, data):
        try:
            instance = Event.objects.get(id=data['id'])
        except Event.DoesNotExist:
            return UpdateEvent(errors=[
                dict(field='nonFieldErrors', messages=gettext('Event does not exist.'))
            ])
        serializer = EventUpdateSerializer(
            instance=instance,
            data=data,
            context=dict(request=info.context.request),
            partial=True,
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateEvent(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateEvent(result=instance, errors=None, ok=True)


class DeleteEvent(graphene.Mutation):
    """

    The DeleteEvent class is a mutation class in Graphene that is used to delete an event. It accepts an ID as a
    required argument, which specifies the ID of the event to be deleted.

    Attributes:
        - errors (List[CustomErrorType]): A list of CustomErrorType objects that represent any errors that occurred
        during the mutation.
        - ok (Boolean): A boolean value indicating whether the mutation was successful.
        - result (EventType): An object of the EventType class representing the deleted event.

    Methods:
        - mutate(root, info, id): This method is a static method that performs the actual deletion of the event. It
        takes three arguments:
            - root: The root object that contains the query or mutation.
            - info: The GraphQL ResolveInfo object containing information about the execution state.
            - id: The ID of the event to be deleted.

            The method performs the following steps:
            1. Tries to retrieve an instance of the Event model with the given ID. If it does not exist, it returns a
            DeleteEvent object with an error indicating that the event does not exist.
            2. Deletes the instance from the database.
            3. Sets the ID of the deleted instance"""
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EventType)

    @staticmethod
    @permission_checker(['event.delete_event'])
    def mutate(root, info, id):
        try:
            instance = Event.objects.get(id=id)
        except Event.DoesNotExist:
            return DeleteEvent(errors=[
                dict(field='nonFieldErrors', messages=gettext('Event does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteEvent(result=instance, errors=None, ok=True)


class ExportEvents(ExportBaseMutation):
    """
    A class for exporting events.

    This class inherits from ExportBaseMutation.

    Args:
        ExportBaseMutation (class): The base mutation class for exporting.

    Attributes:
        DOWNLOAD_TYPE (str): The download type for exporting events.

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = EventFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.EVENT


class ExportActors(ExportBaseMutation):
    """
    Class: ExportActors

    Description:
    This class is a subclass of ExportBaseMutation and is used to export actor data. It provides a method to download
    actor data in Excel format.

    Attributes:
    - DOWNLOAD_TYPE (str): Specifies the type of download as 'ACTOR'.

    Methods:
    None

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = ActorFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.ACTOR


CloneEntryInputType = generate_input_type_for_serializer(
    'CloneEventInputType',
    CloneEventSerializer
)


class CloneEvent(graphene.Mutation):
    """

    Class CloneEvent

    A class representing a GraphQL mutation for cloning an event.

    Attributes:
        - errors (List[CustomErrorType]): A list of custom error types.
        - ok (bool): A boolean indicating if the cloning operation was successful.
        - result (EventType): The cloned event result.

    Methods:
        - mutate(root, info, data): A static method that performs the cloning operation.

    """
    class Arguments:
        data = CloneEntryInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EventType)

    @staticmethod
    @permission_checker(['event.add_event'])
    def mutate(root, info, data):
        serializer = CloneEventSerializer(
            data=data,
            context=dict(request=info.context.request),
        )
        if errors := mutation_is_not_valid(serializer):
            return CloneEvent(errors=errors, ok=False)
        cloned_entries = serializer.save()
        return CloneEvent(result=cloned_entries, errors=None, ok=True)


ContextOfViolenceCreateInputType = generate_input_type_for_serializer(
    'ContextOfViolenceCreateInputType',
    ContextOfViolenceSerializer
)

ContextOfViolenceUpdateInputType = generate_input_type_for_serializer(
    'ContextOfViolenceUpdateInputType',
    ContextOfViolenceUpdateSerializer
)


class CreateContextOfViolence(graphene.Mutation):
    """

    Class: CreateContextOfViolence

    This class is a mutation class that is used to create a context of violence.

    Attributes:
        Arguments:
            - data: (Required) Input data for creating the context of violence.

        errors: A list of custom error types.

        ok: A boolean value indicating the success of the mutation.

        result: A field representing the created context of violence.

    Methods:
        mutate(root, info, data)
            - This is a static method used to mutate and create the context of violence.
            - Parameters:
                - root: The root value.
                - info: The GraphQL ResolveInfo object.
                - data: The input data for creating the context of violence.
            - Returns:
                - If there are any errors in the input data, it returns an instance of CreateContextOfViolence with
                errors and ok set to False.
                - Otherwise, it saves the context of violence using the input data and returns an instance of
                CreateContextOfViolence with the created instance, errors set to None, and ok set to True.

    Note: In order to use this class, the user must have the 'event.add_contextofviolence' permission"""
    class Arguments:
        data = ContextOfViolenceCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ContextOfViolenceType)

    @staticmethod
    @permission_checker(['event.add_contextofviolence'])
    def mutate(root, info, data):
        serializer = ContextOfViolenceSerializer(data=data, context=dict(request=info.context.request))
        if errors := mutation_is_not_valid(serializer):
            return CreateContextOfViolence(errors=errors, ok=False)
        instance = serializer.save()
        return CreateContextOfViolence(result=instance, errors=None, ok=True)


class UpdateContextOfViolence(graphene.Mutation):
    """

    UpdateContextOfViolence class is a mutation class used to update the context of violence. It receives a
    ContextOfViolenceUpdateInputType as an argument and returns a result of type ContextOfViolenceType.

    Attributes:
    - errors: A list of CustomErrorType objects to store any errors that occur during the mutation.
    - ok: A boolean value indicating whether the mutation was successful or not.
    - result: A field of type ContextOfViolenceType to store the updated context of violence.

    Methods:
    - mutate: A static method decorated with @permission_checker that performs the mutation. It takes root, info, and
    data as arguments.
      - root: The root value passed by the GraphQL server.
      - info: An object containing information about the execution of the query/mutation.
      - data: The input data for updating the context of violence.
      It performs the following steps:
      """
    class Arguments:
        data = ContextOfViolenceUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ContextOfViolenceType)

    @staticmethod
    @permission_checker(['event.change_contextofviolence'])
    def mutate(root, info, data):
        try:
            instance = ContextOfViolence.objects.get(id=data['id'])
        except ContextOfViolence.DoesNotExist:
            return UpdateContextOfViolence(errors=[
                dict(field='nonFieldErrors', messages=gettext('Context of violence does not exist.'))
            ])
        serializer = ContextOfViolenceUpdateSerializer(
            instance=instance, data=data,
            context=dict(request=info.context.request), partial=True
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateContextOfViolence(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateContextOfViolence(result=instance, errors=None, ok=True)


class DeleteContextOfViolence(graphene.Mutation):
    """
    The `DeleteContextOfViolence` class is a mutation class that is responsible for deleting a context of violence
    object.

    Args:
        id: The ID of the context of violence object that needs to be deleted. (required)

    Returns:
        - errors: A list of custom error types associated with the mutation, if any.
        - ok: A boolean value indicating whether the deletion was successful or not.
        - result: The deleted context of violence object.

    Example Usage:
        # Create an instance of DeleteContextOfViolence mutation
        mutation = DeleteContextOfViolence()

        # Provide the required arguments
        mutation.id = "1"

        # Execute the mutation and obtain the result
        result = mutation.mutate(root, info, id)

    Note:
        The `id` argument is required. If the provided ID does not exist, a custom error will be returned.
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ContextOfViolenceType)

    @staticmethod
    @permission_checker(['event.delete_contextofviolence'])
    def mutate(root, info, id):
        try:
            instance = ContextOfViolence.objects.get(id=id)
        except ContextOfViolence.DoesNotExist:
            return DeleteContextOfViolence(errors=[
                dict(field='nonFieldErrors', messages=gettext('Context of violence does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteContextOfViolence(result=instance, errors=None, ok=True)


class SetAssigneeToEvent(graphene.Mutation):
    """
    Class: SetAssigneeToEvent

    A class that represents a mutation to set the assignee of an event.

    Attributes:
        - event_id (graphene.ID): The ID of the event to set the assignee for. (required)
        - user_id (graphene.ID): The ID of the user to assign to the event. (required)
        - errors (graphene.List[graphene.NonNull(CustomErrorType)]): A list of custom error types.
        - ok (graphene.Boolean): A boolean indicating if the mutation was successful or not.
        - result (graphene.Field(EventType)): A field containing the updated event object.

    Methods:
        - mutate(root, info, event_id, user_id):
            Performs the mutation by setting the assignee of the event to the specified user.
            Parameters:
                - root: The root value.
                - info: The resolution info.
                - event_id: The ID of the event to set the assignee for.
                - user_id: The ID of the user to assign to the event.
            Returns:
                - If the event does not exist, returns a SetAssigneeToEvent"""
    class Arguments:
        event_id = graphene.ID(required=True)
        user_id = graphene.ID(required=True)
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EventType)

    @staticmethod
    @permission_checker(['event.assign_event'])
    def mutate(root, info, event_id, user_id):
        from apps.users.models import User
        event = Event.objects.filter(id=event_id).first()
        if not event:
            return SetAssigneeToEvent(errors=[
                dict(field='nonFieldErrors', messages=gettext('Event does not exist.'))
            ])

        user = User.objects.filter(id=user_id).first()
        # To prevent users being saved with no permission in event review process. for eg GUEST
        if not user.has_perm('event.self_assign_event'):
            return SetAssigneeToEvent(errors=[
                dict(field='nonFieldErrors', messages=gettext('The user does not exist or has enough permissions.'))
            ])

        prev_assignee_id = event.assignee_id
        prev_assigner_id = event.assigner_id

        event.assignee = user
        event.assigner = info.context.user
        event.assigned_at = timezone.now()
        event.save()

        recipients = []
        if prev_assignee_id:
            recipients.append(prev_assignee_id)
        if prev_assigner_id:
            recipients.append(prev_assigner_id)
        if recipients:
            Notification.send_safe_multiple_notifications(
                event=event,
                recipients=recipients,
                actor=info.context.user,
                type=Notification.Type.EVENT_ASSIGNEE_CLEARED,
            )

        recipients = [user.id]
        if prev_assigner_id:
            recipients.append(prev_assigner_id)
        Notification.send_safe_multiple_notifications(
            event=event,
            recipients=recipients,
            actor=info.context.user,
            type=Notification.Type.EVENT_ASSIGNED,
        )

        return SetAssigneeToEvent(result=event, errors=None, ok=True)


class SetSelfAssigneeToEvent(graphene.Mutation):
    """
    The `SetSelfAssigneeToEvent` class is a mutation that allows the current user to assign themselves as the assignee
    of a specified event.

    Parameters:
    - `event_id` (required): The ID of the event to be assigned.

    Attributes:
    - `errors`: A list of error messages, if any errors occur during the mutation.
    - `ok`: A boolean indicating whether the mutation was successful or not.
    - `result`: The updated event object after the self-assignment.

    Usage:
    1. Instantiate the `SetSelfAssigneeToEvent` class with the `event_id` parameter.
    2. Call the `mutate` method on the instance, passing in the necessary arguments.
    3. The method will assign the current user as the assignee of the specified event.
    4. The method will also send notifications to the previous assignee and assigner, notifying them of the change.
    5. Finally, the method will return the updated event object.

    Example:

    set_self_assignee = SetSelfAssigneeToEvent(event_id='12345')
    result = set_self_assignee.mutate()

    result.ok
    >>> True

    """
    class Arguments:
        event_id = graphene.ID(required=True)
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EventType)

    @staticmethod
    @permission_checker(['event.self_assign_event'])
    def mutate(root, info, event_id):
        event = Event.objects.filter(id=event_id).first()
        if not event:
            return SetSelfAssigneeToEvent(errors=[
                dict(field='nonFieldErrors', messages=gettext('Event does not exist.'))
            ])

        prev_assignee_id = event.assignee_id
        prev_assigner_id = event.assigner_id

        event.assignee = info.context.user
        event.assigner = info.context.user
        event.assigned_at = timezone.now()
        event.save()

        recipients = []
        if prev_assignee_id:
            recipients.append(prev_assignee_id)
        if prev_assigner_id:
            recipients.append(prev_assigner_id)
        if recipients:
            Notification.send_safe_multiple_notifications(
                event=event,
                recipients=recipients,
                actor=info.context.user,
                type=Notification.Type.EVENT_ASSIGNEE_CLEARED,
            )

        recipients = [user['id'] for user in Event.regional_coordinators(
            event,
            actor=info.context.user,
        )]
        if prev_assigner_id:
            recipients.append(prev_assigner_id)
        Notification.send_safe_multiple_notifications(
            recipients=recipients,
            type=Notification.Type.EVENT_SELF_ASSIGNED,
            actor=info.context.user,
            event=event,
        )

        return SetSelfAssigneeToEvent(result=event, errors=None, ok=True)


class ClearAssigneFromEvent(graphene.Mutation):
    """
    ClearAssigneFromEvent

    This class represents a GraphQL mutation for clearing the assignee from an event.

    Attributes:
        Arguments:
            event_id (graphene.ID): The ID of the event to clear the assignee from.

        errors (graphene.List[graphene.NonNull(CustomErrorType)]): A list of errors that occurred during the mutation.

        ok (graphene.Boolean): A flag indicating if the mutation was successful.

        result (graphene.Field(EventType)): The updated event object after clearing the assignee.

    Methods:
        mutate(root, info, event_id)
            This method is a static method that handles the mutation logic for clearing the assignee from an event.

            Args:
                root: The root value of the mutation.
                info: The GraphQL ResolveInfo object containing information about the execution state.
                event_id (graphene.ID): The ID of the event to clear the assignee from.

            Returns:
                ClearAssigneFromEvent: The updated ClearAssigneFromEvent object after clearing the assignee.

    """
    class Arguments:
        event_id = graphene.ID(required=True)
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EventType)

    @staticmethod
    @permission_checker(['event.clear_assignee_event'])
    def mutate(root, info, event_id):
        # Admin, assigner and assignee(self) can only clear assignee
        event = Event.objects.filter(id=event_id).first()
        if not event:
            return ClearAssigneFromEvent(errors=[
                dict(field='nonFieldErrors', messages=gettext('Event does not exist.'))
            ])

        prev_assignee_id = event.assignee_id
        prev_assigner_id = event.assigner_id
        if not prev_assignee_id:
            return ClearAssigneFromEvent(errors=[
                dict(
                    field='nonFieldErrors',
                    messages=gettext('Cannot clear assignee because event does not have an assignee'),
                )
            ])

        event.assignee = None
        event.assigner = None
        event.assigned_at = None
        event.save()

        recipients = []
        if prev_assignee_id:
            recipients.append(prev_assignee_id)
        if prev_assigner_id:
            recipients.append(prev_assigner_id)
        if recipients:
            Notification.send_safe_multiple_notifications(
                event=event,
                recipients=recipients,
                actor=info.context.user,
                type=Notification.Type.EVENT_ASSIGNEE_CLEARED,
            )

        return ClearAssigneFromEvent(result=event, errors=None, ok=True)


class ClearSelfAssigneFromEvent(graphene.Mutation):
    """

    A class that represents a GraphQL mutation to clear self assignee from an event.

    Examples:
        This class does not provide any example code. Please refer to the usage documentation.

    Attributes:
        Arguments:
            event_id (graphene.ID): The ID of the event to clear self assignee from.

        errors (graphene.List[graphene.NonNull(CustomErrorType)]): A list of custom error messages returned by the
        mutation.

        ok (graphene.Boolean): A boolean indicating if the mutation was successful.

        result (graphene.Field(EventType)): The updated event object after clearing self assignee.

    Methods:
        mutate(root, info, event_id):
            A static method that executes the mutation logic to clear self assignee from the event.

    Parameters:
        root (Any): The root value of the mutation.

        info (ResolveInfo): Information about the execution state of the mutation.

        event_id (str): The ID of the event to clear self assignee from.

    Returns:
        ClearSelfAssigneFromEvent: An instance of the ClearSelfAssigneFromEvent class.

    """
    class Arguments:
        event_id = graphene.ID(required=True)
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EventType)

    @staticmethod
    @permission_checker(['event.clear_self_assignee_event'])
    def mutate(root, info, event_id):
        event = Event.objects.filter(id=event_id).first()
        if not event:
            return ClearSelfAssigneFromEvent(errors=[
                dict(field='nonFieldErrors', messages=gettext('Event does not exist.'))
            ])

        # Admin and RE can clear all other users from assignee except ME
        # FIXME: this logic does not seem right after `or`
        if event.assignee_id != info.context.user.id or info.context.user.has_perm('clear_assignee_from_event'):
            return ClearAssigneFromEvent(errors=[
                dict(field='nonFieldErrors', messages=gettext('You are not allowed to clear others from assignee.'))
            ])

        prev_assigner_id = event.assigner_id

        event.assignee = None
        event.assigner = None
        event.assigned_at = None
        event.save()

        recipients = []
        if event.regional_coordinators:
            recipients.extend([user['id'] for user in Event.regional_coordinators(
                event,
                actor=info.context.user,
            )])
        if prev_assigner_id:
            recipients.append(prev_assigner_id)

        if recipients:
            Notification.send_safe_multiple_notifications(
                recipients=recipients,
                type=Notification.Type.EVENT_ASSIGNEE_CLEARED,
                actor=info.context.user,
                event=event,
            )

        return ClearSelfAssigneFromEvent(result=event, errors=None, ok=True)


class SignOffEvent(graphene.Mutation):
    """

    """
    class Arguments:
        event_id = graphene.ID(required=True)
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EventType)

    @staticmethod
    @permission_checker(['event.sign_off_event'])
    def mutate(root, info, event_id):
        event = Event.objects.filter(id=event_id).first()
        if not event:
            return SignOffEvent(errors=[
                dict(field='nonFieldErrors', messages=gettext('Event does not exist.'))
            ])
        if not event.review_status == Event.EVENT_REVIEW_STATUS.APPROVED:
            return SignOffEvent(errors=[
                dict(field='nonFieldErrors', messages=gettext('Event is not approved yet.'))
            ])

        event.review_status = Event.EVENT_REVIEW_STATUS.SIGNED_OFF
        event.save()

        recipients = [
            user['id'] for user in Event.regional_coordinators(
                event,
                actor=info.context.user,
            )
        ]
        if event.created_by_id:
            recipients.append(event.created_by_id)
        if event.assignee_id:
            recipients.append(event.assignee_id)

        Notification.send_safe_multiple_notifications(
            recipients=recipients,
            type=Notification.Type.EVENT_SIGNED_OFF,
            actor=info.context.user,
            event=event,
        )

        return SignOffEvent(result=event, errors=None, ok=True)


class ExportContextOfViolences(ExportBaseMutation):
    """
    ExportContextOfViolences class is a subclass of ExportBaseMutation class. It represents a mutation for exporting the
    context of violences data.

    Attributes:
        DOWNLOAD_TYPE (str): The download type for context of violences export.

    Arguments:
        filters (ContextOfViolenceFilterDataInputType): Required input data for filtering the context of violences.

    Example usage:
        mutation {
            exportContextOfViolences(filters: { ... }) {
                success
                errors
                file
            }
        }
    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = ContextOfViolenceFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.CONTEXT_OF_VIOLENCE


class Mutation(object):
    """

    Class: Mutation

    This class represents a collection of fields that define the mutations available in a system. Each mutation
    corresponds to a specific action that can be performed on the system's data.

    Attributes:
    - create_event: A field representing the mutation to create an event.
    - update_event: A field representing the mutation to update an event.
    - delete_event: A field representing the mutation to delete an event.
    - create_actor: A field representing the mutation to create an actor.
    - update_actor: A field representing the mutation to update an actor.
    - delete_actor: A field representing the mutation to delete an actor.
    - create_context_of_violence: A field representing the mutation to create a context of violence.
    - update_context_of_violence: A field representing the mutation to update a context of violence.
    - delete_context_of_violence: A field representing the mutation to delete a context of violence.
    - export_events: A field representing the mutation to export events.
    - export_actors: A field representing the mutation to export actors.
    - export_context_of_violences: A field representing the mutation to export contexts of violence.
    - clone_event: A field representing the"""
    create_event = CreateEvent.Field()
    update_event = UpdateEvent.Field()
    delete_event = DeleteEvent.Field()
    create_actor = CreateActor.Field()
    update_actor = UpdateActor.Field()
    delete_actor = DeleteActor.Field()
    create_context_of_violence = CreateContextOfViolence.Field()
    update_context_of_violence = UpdateContextOfViolence.Field()
    delete_context_of_violence = DeleteContextOfViolence.Field()

    # exports
    export_events = ExportEvents.Field()
    export_actors = ExportActors.Field()
    export_context_of_violences = ExportContextOfViolences.Field()
    clone_event = CloneEvent.Field()

    # review related
    set_assignee_to_event = SetAssigneeToEvent.Field()
    set_self_assignee_to_event = SetSelfAssigneeToEvent.Field()
    clear_assignee_from_event = ClearAssigneFromEvent.Field()
    clear_self_assignee_from_event = ClearSelfAssigneFromEvent.Field()
    sign_off_event = SignOffEvent.Field()

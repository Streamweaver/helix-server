from django.utils.translation import gettext
import graphene
from django.utils import timezone
from django.db import transaction

from apps.entry.models import Entry, FigureTag, Figure
from apps.entry.schema import (
    EntryType,
    FigureType,
    SourcePreviewType,
    FigureTagType,)
from apps.entry.serializers import (
    EntryCreateSerializer,
    EntryUpdateSerializer,
    FigureTagCreateSerializer,
    FigureTagUpdateSerializer,
    FigureSerializer,
)
from apps.extraction.filters import FigureExtractionFilterDataInputType, EntryExtractionFilterDataInputType
from apps.contrib.models import SourcePreview, ExcelDownload
from apps.contrib.mutations import ExportBaseMutation
from apps.contrib.serializers import SourcePreviewSerializer
from apps.extraction.filters import FigureTagFilterDataInputType
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker, is_authenticated
from utils.mutation import generate_input_type_for_serializer, BulkUpdateMutation

from apps.notification.models import Notification
from .utils import BulkUpdateFigureManager, send_figure_notifications, get_figure_notification_type

# entry

EntryCreateInputType = generate_input_type_for_serializer(
    'EntryCreateInputType',
    serializer_class=EntryCreateSerializer
)

EntryUpdateInputType = generate_input_type_for_serializer(
    'EntryUpdateInputType',
    serializer_class=EntryUpdateSerializer,
)

FigureUpdateInputType = generate_input_type_for_serializer(
    'FigureUpdateInputType',
    serializer_class=FigureSerializer,
    partial=True,
)


class CreateEntry(graphene.Mutation):
    """

    Class: CreateEntry

    Description:
    This class is a mutation class that allows the creation of new entries. It takes in data of type 'EntryCreateInputType' as an argument and returns a response containing information about the success of the mutation and any errors that occurred.

    Attributes:
    - Arguments:
        - data: Required. Type: EntryCreateInputType. The input data for creating a new entry.
    - errors: A list of CustomErrorType objects. Contains any errors that occurred during the mutation.
    - ok: Boolean value representing the success status of the mutation.
    - result: Field of type EntryType. Contains the newly created entry if the mutation was successful.

    Methods:
    - mutate(root, info, data):
        - Description: A static method that handles the mutation logic.
        - Parameters:
            - root: The root object.
            - info: Information about the request.
            - data: The input data for creating a new entry.
        - Returns: An instance of the CreateEntry class.

    """
    class Arguments:
        data = EntryCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EntryType)

    @staticmethod
    @permission_checker(['entry.add_entry'])
    def mutate(root, info, data):
        serializer = EntryCreateSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateEntry(errors=errors, ok=False)
        instance = serializer.save()
        return CreateEntry(result=instance, errors=None, ok=True)


class UpdateEntry(graphene.Mutation):
    """
    Class UpdateEntry

    A class representing a mutation for updating an Entry object.

    Properties:
    - data: Required argument of type EntryUpdateInputType. Represents the data to update the Entry object.
    - errors: A list of CustomErrorType objects. Represents any errors that occurred during the mutation.
    - ok: A boolean value indicating the success of the mutation.
    - result: An EntryType object representing the updated Entry object.

    Methods:
    - mutate(root, info, data): Static method that performs the mutation operation. It takes the following parameters:
      - root: The root object.
      - info: The GraphQL resolver info object.
      - data: The data to update the Entry object.

    Returns:
    An instance of the UpdateEntry class.

    Example Usage:
    mutation {
      updateEntry(data: {id: 1, ...}) {
        errors {
          field
          messages
        }
        ok
        result {
          id
          ...
        }
      }
    }
    """
    class Arguments:
        data = EntryUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EntryType)

    @staticmethod
    @permission_checker(['entry.change_entry'])
    def mutate(root, info, data):
        try:
            instance = Entry.objects.get(id=data['id'])
        except Entry.DoesNotExist:
            return UpdateEntry(errors=[
                dict(field='nonFieldErrors', messages=gettext('Entry does not exist.'))
            ])
        serializer = EntryUpdateSerializer(instance=instance, data=data,
                                           context={'request': info.context.request}, partial=True)
        if errors := mutation_is_not_valid(serializer):
            return UpdateEntry(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateEntry(result=instance, errors=None, ok=True)


class DeleteEntry(graphene.Mutation):
    """
    Class to delete an entry.

    .. note::
        This class is a mutation class that is responsible for deleting an entry.

    .. attribute:: Arguments

        - **id** (*graphene.ID(required=True)*) - The ID of the entry to be deleted.

    .. attribute:: errors

        - **errors** (*graphene.List(graphene.NonNull(CustomErrorType))*) - A list of custom error types.

    .. attribute:: ok

        - **ok** (*graphene.Boolean*) - A boolean value indicating if the entry was successfully deleted.

    .. attribute:: result

        - **result** (*graphene.Field(EntryType)*) - The deleted entry.

    .. method:: mutate(root, info, id)

        This method is responsible for the actual deletion of the entry. It takes the following parameters:

        - **root** - The root value.
        - **info** - The GraphQL resolve info.
        - **id** - The ID of the entry to be deleted.

        :returns: A `DeleteEntry` instance containing the deleted entry, errors (if any), and the success status.
        :rtype: DeleteEntry
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(EntryType)

    @staticmethod
    @permission_checker(['entry.delete_entry'])
    def mutate(root, info, id):
        from apps.event.models import Event

        try:
            instance = Entry.objects.get(id=id)
        except Entry.DoesNotExist:
            return DeleteEntry(errors=[
                dict(field='nonFieldErrors', messages=gettext('Entry does not exist.'))
            ])

        affected_event_ids = []

        # Send notification to regional co-ordinators
        # TODO: Can we re-use the function defined on DeleteFigure._get_notification_type?
        for review_status in [
            Event.EVENT_REVIEW_STATUS.APPROVED_BUT_CHANGED,
            Event.EVENT_REVIEW_STATUS.SIGNED_OFF_BUT_CHANGED,
            Event.EVENT_REVIEW_STATUS.APPROVED,
            Event.EVENT_REVIEW_STATUS.SIGNED_OFF,
        ]:
            figures = instance.figures.filter(
                entry__id=instance.id,
                event__review_status=review_status
            )

            for figure in figures:
                recipients = [
                    user['id'] for user in Event.regional_coordinators(
                        event=figure.event,
                        actor=info.context.user,
                    )
                ]
                if figure.event.created_by_id:
                    recipients.append(figure.event.created_by_id)
                if figure.event.assignee_id:
                    recipients.append(figure.event.assignee_id)

                notification_type = Notification.Type.FIGURE_DELETED_IN_APPROVED_EVENT
                if (
                    review_status == Event.EVENT_REVIEW_STATUS.SIGNED_OFF or
                    review_status == Event.EVENT_REVIEW_STATUS.SIGNED_OFF_BUT_CHANGED
                ):
                    notification_type = Notification.Type.FIGURE_DELETED_IN_SIGNED_EVENT

                Notification.send_safe_multiple_notifications(
                    recipients=recipients,
                    actor=info.context.user,
                    type=notification_type,
                    event=figure.event,
                    text=gettext('Entry and figures were deleted'),
                )

                affected_event_ids.append(figure.event_id)

        for event_id in list(set(affected_event_ids)):
            Figure.update_event_status_and_send_notifications(event_id)

        instance.delete()

        instance.id = id
        return DeleteEntry(result=instance, errors=None, ok=True)


SourcePreviewInputType = generate_input_type_for_serializer(
    'SourcePreviewInputType',
    SourcePreviewSerializer
)


class CreateSourcePreview(graphene.Mutation):
    """
    CreateSourcePreview class

    This class is a mutation for creating a source preview.

    Attributes:
        ok (graphene.Boolean): Indicates if the mutation was successful.
        errors (graphene.List[CustomErrorType]): List of errors occurred during the mutation.
        result (graphene.Field[SourcePreviewType]): The created source preview.

    Methods:
        mutate(root, info, data)
            Executes the mutation logic to create a source preview.

    """

    class Arguments:
        data = SourcePreviewInputType(required=True)

    ok = graphene.Boolean()
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    result = graphene.Field(SourcePreviewType)

    @staticmethod
    @permission_checker(['entry.add_entry'])
    def mutate(root, info, data):
        if data.get('id'):
            try:
                instance = SourcePreview.objects.get(id=data['id'])
                serializer = SourcePreviewSerializer(data=data, instance=instance,
                                                     context={'request': info.context.request})
            except SourcePreview.DoesNotExist:
                return CreateSourcePreview(errors=[
                    dict(field='nonFieldErrors', messages=gettext('Preview does not exist.'))
                ])
        else:
            serializer = SourcePreviewSerializer(data=data,
                                                 context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateSourcePreview(errors=errors, ok=False)
        instance = serializer.save()
        return CreateSourcePreview(result=instance, errors=None, ok=True)


FigureTagCreateInputType = generate_input_type_for_serializer(
    'FigureTagCreateInputType',
    FigureTagCreateSerializer
)

FigureTagUpdateInputType = generate_input_type_for_serializer(
    'FigureTagUpdateInputType',
    FigureTagUpdateSerializer
)


class CreateFigureTag(graphene.Mutation):
    """
    CreateFigureTag

    This class represents a GraphQL mutation to create a FigureTag instance.

    Attributes:
        - Arguments:
            - data: An instance of FigureTagCreateInputType that contains the data for creating a FigureTag.
        - errors: A list of CustomErrorType objects representing any error that occurred during the mutation.
        - ok: A boolean indicating the success of the mutation.
        - result: An instance of FigureTagType representing the created FigureTag.

    Methods:
        - mutate: A static method decorated with various decorators that performs the mutation.

    """
    class Arguments:
        data = FigureTagCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(FigureTagType)

    @staticmethod
    @is_authenticated()
    @permission_checker(['entry.add_figuretag'])
    def mutate(root, info, data):
        serializer = FigureTagCreateSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateFigureTag(errors=errors, ok=False)
        instance = serializer.save()
        return CreateFigureTag(result=instance, errors=None, ok=True)


class UpdateFigureTag(graphene.Mutation):
    """

    The UpdateFigureTag class represents a GraphQL mutation for updating a FigureTag object.

    Attributes:
    - errors: A list of CustomErrorType objects representing any errors that occurred during the mutation.
    - ok: A boolean indicating whether the mutation was successful.
    - result: A FigureTagType object representing the updated FigureTag.

    Methods:
    - mutate(root, info, data): A static method that performs the mutation based on the provided arguments.

    Parameters:
    - root: The root value.
    - info: The GraphQL resolve info.
    - data: An instance of FigureTagUpdateInputType representing the data to update the FigureTag with.

    The mutate() method first tries to retrieve the FigureTag object with the provided ID from the database. If the object does not exist, it returns an UpdateFigureTag object with an error indicating that the tag does not exist.

    Next, it creates a FigureTagCreateSerializer instance with the retrieved FigureTag object, the provided data, and the request context. The partial argument is set to True, indicating that only the provided fields should be updated.

    If the serializer's validation fails, it returns an UpdateFigureTag object with the validation errors and a value of False for the ok attribute.

    If the validation succeeds, it saves the serializer and assigns the updated FigureTag object to the instance variable.

    Finally, it returns an UpdateFigureTag object with the updated FigureTag, a value of True for the ok attribute, and no errors.

    """
    class Arguments:
        data = FigureTagUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(FigureTagType)

    @staticmethod
    @is_authenticated()
    @permission_checker(['entry.change_figuretag'])
    def mutate(root, info, data):
        try:
            instance = FigureTag.objects.get(id=data['id'])
        except FigureTag.DoesNotExist:
            return UpdateFigureTag(errors=[
                dict(field='nonFieldErrors', messages=gettext('Tag does not exist.'))
            ])
        serializer = FigureTagCreateSerializer(instance=instance, data=data,
                                               context={'request': info.context.request}, partial=True)
        if errors := mutation_is_not_valid(serializer):
            return UpdateFigureTag(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateFigureTag(result=instance, errors=None, ok=True)


class DeleteFigureTag(graphene.Mutation):
    """

    `DeleteFigureTag` is a mutation class that is used to delete a specific `FigureTag` object from the database. This class is a part of a GraphQL schema.

    ## Arguments
    - `id`: Required argument of type `graphene.ID`. It represents the unique identifier of the `FigureTag` object that needs to be deleted.

    ## Output
    - `errors`: A list of `CustomErrorType` objects. It represents any errors that may have occurred during the deletion process.
    - `ok`: A boolean value indicating the success of the deletion operation.
    - `result`: A `FigureTagType` object representing the deleted `FigureTag` instance.

    ## Usage

    1. Import the necessary modules and dependencies:

    ```python
    import graphene
    from your_module import is_authenticated, permission_checker
    from your_module.models import FigureTag
    from your_module.types import CustomErrorType, FigureTagType
    ```

    2. Define the `DeleteFigureTag` mutation class:

    ```python
    class DeleteFigureTag(graphene.Mutation):
        class Arguments:
            id = graphene.ID(required=True)

        errors = graphene.List(graphene.NonNull(CustomErrorType))
        ok = graphene.Boolean()
        result = graphene.Field(FigureTagType)
    ```

    3. Implement the `mutate` method to perform the deletion operation:

    ```python
        @staticmethod
        @is_authenticated()
        @permission_checker(['entry.delete_figuretag'])
        def mutate(root, info, id):
            try:
                instance = FigureTag.objects.get(id=id)
            except FigureTag.DoesNotExist:
                return DeleteFigureTag(errors=[
                    dict(field='nonFieldErrors', messages=gettext('Tag does not exist.'))
                ])
            instance.delete()
            instance.id = id

            return DeleteFigureTag(result=instance, errors=None, ok=True)
    ```

    Note: The above code assumes that you have defined the `is_authenticated` and `permission_checker` decorators, as well as the `FigureTagType` and `CustomErrorType` types, in your module.

    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(FigureTagType)

    @staticmethod
    @is_authenticated()
    @permission_checker(['entry.delete_figuretag'])
    def mutate(root, info, id):
        try:
            instance = FigureTag.objects.get(id=id)
        except FigureTag.DoesNotExist:
            return DeleteFigureTag(errors=[
                dict(field='nonFieldErrors', messages=gettext('Tag does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteFigureTag(result=instance, errors=None, ok=True)


class ExportEntries(ExportBaseMutation):
    """A class for exporting entries to Excel format.

    ExportEntries is a subclass of ExportBaseMutation and is used to export entries to Excel format. It takes the required `filters` argument of type EntryExtractionFilterDataInputType.

    Example usage:
        export = ExportEntries(filters={'type': 'book'})

    Attributes:
        DOWNLOAD_TYPE (str): The download type for exporting as Excel.

    Args:
        ExportBaseMutation (class): The base mutation class for exporting.
        Arguments (class): The argument class for exporting.
        filters (EntryExtractionFilterDataInputType): The required filters for exporting.

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = EntryExtractionFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.ENTRY


class ExportFigures(ExportBaseMutation):
    """
    Class: ExportFigures

    Describes a class that is used to export figures in Excel format.

    Inherits From: ExportBaseMutation

    Attributes:
        DOWNLOAD_TYPE (str): The download type for figures, set to 'FIGURE'.

    Arguments:
        filters (FigureExtractionFilterDataInputType): Required argument that specifies the filters for figure extraction.

    """
    class Arguments(ExportBaseMutation.Arguments):
        # TODO: use Can we use ReportFigureExtractionFilterSet?
        filters = FigureExtractionFilterDataInputType(required=True)

    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.FIGURE


class ExportFigureTags(ExportBaseMutation):
    """

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = FigureTagFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.FIGURE_TAG


class DeleteFigure(graphene.Mutation):
    """
    The DeleteFigure class is a mutation class used to delete a figure object. It inherits from the graphene.Mutation class.

    Attributes:
        - Arguments (class): A nested class that defines the arguments required for the mutation.
            - id (graphene.ID): The ID of the figure to be deleted.

        - errors (graphene.List[graphene.NonNull(CustomErrorType)]): A list of custom error types, if any.
        - ok (graphene.Boolean): A boolean indicating the success of the mutation.
        - result (graphene.Field[FigureType]): The deleted figure object.

    Methods:
        - mutate(root, info, id): A static method used to perform the mutation. It takes the following parameters:
            - root: The root value.
            - info: The GraphQL ResolveInfo object.
            - id (graphene.ID): The ID of the figure to be deleted.

            Returns:
                - If the figure with the provided ID does not exist, a DeleteFigure object with a list of errors is returned.
                - If the figure is successfully deleted, a DeleteFigure object with ok set to True and errors set to None is returned.

                Deletes the figure with the provided ID, and sends appropriate notifications based on the event's review status.
                Updates the event's status and sends notifications.
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(FigureType)

    @staticmethod
    @permission_checker(['entry.delete_figure'])
    def mutate(root, info, id):
        from apps.event.models import Event

        try:
            instance = Figure.objects.get(id=id)
        except Entry.DoesNotExist:
            return DeleteFigure(errors=[
                dict(field='nonFieldErrors', messages=gettext('Figure does not exist.'))
            ])

        instance.delete()

        def _get_notification_type(event):
            if event.review_status in [
                Event.EVENT_REVIEW_STATUS.APPROVED,
                Event.EVENT_REVIEW_STATUS.APPROVED_BUT_CHANGED,
            ]:
                return Notification.Type.FIGURE_DELETED_IN_APPROVED_EVENT
            if event.review_status in [
                Event.EVENT_REVIEW_STATUS.SIGNED_OFF,
                Event.EVENT_REVIEW_STATUS.SIGNED_OFF_BUT_CHANGED,
            ]:
                return Notification.Type.FIGURE_DELETED_IN_SIGNED_EVENT
            return None

        _type = _get_notification_type(instance.event)

        if _type:
            recipients = [user['id'] for user in Event.regional_coordinators(
                instance.event,
                actor=info.context.user,
            )]
            if instance.event.created_by_id:
                recipients.append(instance.event.created_by_id)
            if instance.event.assignee_id:
                recipients.append(instance.event.assignee_id)

            Notification.send_safe_multiple_notifications(
                recipients=recipients,
                actor=info.context.user,
                type=_type,
                entry=instance.entry,
                event=instance.event,
            )

        Figure.update_event_status_and_send_notifications(instance.event_id)
        instance.event.refresh_from_db()

        return DeleteFigure(errors=None, ok=True)


class ApproveFigure(graphene.Mutation):
    """
    This class represents a mutation to approve a figure. It is a sub-class of the `graphene.Mutation` class.

    Attributes:
        Arguments (nested class): Represents the arguments that can be passed to the mutation.
        - id (graphene.ID): The ID of the figure to be approved.

        errors (graphene.List): A list of error messages. Each error message is an instance of `CustomErrorType`.
        ok (graphene.Boolean): Indicates whether the mutation was successful or not.
        result (graphene.Field): Represents the approved figure. It is an instance of `FigureType`.

    Methods:
        mutate(root, info, id): Static method that performs the mutation logic. Called when the mutation is executed.

    Note:
        - The `mutate` method has the `@staticmethod` decorator and the `@permission_checker(['entry.approve_figure'])`
          decorator, indicating that it can be called without creating an instance of the class and that the user must have
          the 'entry.approve_figure' permission.
        - The `mutate` method returns an instance of `ApproveFigure` with either the approved figure and no errors,
          or a list of error messages and no result.
        - The `mutate` method updates the review status of the figure to 'approved', sets the approved by and approved on
          fields, and saves the changes to the database.
        - The `mutate` method calls the static method `update_event_status_and_send_notifications` of the `Figure` class to
          update the event status and send notifications for the event associated with the approved figure.
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(FigureType)

    @staticmethod
    @permission_checker(['entry.approve_figure'])
    def mutate(root, info, id):
        figure = Figure.objects.filter(id=id).first()
        if not figure:
            return ApproveFigure(errors=[
                dict(field='nonFieldErrors', messages=gettext('Figure does not exist.'))
            ])
        if figure.review_status == Figure.FIGURE_REVIEW_STATUS.APPROVED:
            return ApproveFigure(errors=[
                dict(field='nonFieldErrors', messages=gettext('Approved figures cannot be approved'))
            ])

        figure.review_status = Figure.FIGURE_REVIEW_STATUS.APPROVED
        figure.approved_by = info.context.user
        figure.approved_on = timezone.now()
        figure.save()

        # NOTE: not sending notification when figure is approved as it is not actionable

        Figure.update_event_status_and_send_notifications(figure.event_id)
        figure.event.refresh_from_db()

        return ApproveFigure(result=figure, errors=None, ok=True)


class UnapproveFigure(graphene.Mutation):
    """
    UnapproveFigure
    -----------

    A class that represents a mutation for un-approving a figure.

    Attributes:
    -----------
    - id (graphene.ID): The ID of the figure to be un-approved.

    Returns:
    -----------
    - errors (List[CustomErrorType]): A list of errors, if any occurred during the mutation.
    - ok (Boolean): Indicates whether the mutation was successful or not.
    - result (FigureType): The updated figure object, if the mutation was successful.

    Methods:
    -----------
    - staticmethod mutate(root, info, id):
        Executes the mutation to un-approve a figure.

        Parameters:
            - root: The root value/handler
            - info: The GraphQL resolution info
            - id (str): The ID of the figure to be un-approved.

        Returns:
            - An instance of the UnapproveFigure class.
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(FigureType)

    @staticmethod
    @permission_checker(['entry.approve_figure'])
    @is_authenticated()
    def mutate(root, info, id):
        from apps.event.models import Event
        figure = Figure.objects.filter(id=id).first()
        if not figure:
            return UnapproveFigure(errors=[
                dict(field='nonFieldErrors', messages=gettext('Figure does not exist.'))
            ])
        if figure.review_status != Figure.FIGURE_REVIEW_STATUS.APPROVED:
            return UnapproveFigure(errors=[
                dict(field='nonFieldErrors', messages=gettext('Only approved figures can be un-approved'))
            ])

        figure.review_status = (
            Figure.FIGURE_REVIEW_STATUS.REVIEW_IN_PROGRESS
            if figure.figure_review_comments.all().count() > 0
            else Figure.FIGURE_REVIEW_STATUS.REVIEW_NOT_STARTED
        )
        figure.approved_by = None
        figure.approved_on = None
        figure.save()

        def _get_notification_type(event):
            if event.review_status in [
                Event.EVENT_REVIEW_STATUS.APPROVED,
                Event.EVENT_REVIEW_STATUS.APPROVED_BUT_CHANGED,
            ]:
                return Notification.Type.FIGURE_UNAPPROVED_IN_APPROVED_EVENT
            if event.review_status in [
                Event.EVENT_REVIEW_STATUS.SIGNED_OFF,
                Event.EVENT_REVIEW_STATUS.SIGNED_OFF_BUT_CHANGED,
            ]:
                return Notification.Type.FIGURE_UNAPPROVED_IN_SIGNED_EVENT
            return None

        _type = _get_notification_type(figure.event)
        if _type:
            recipients = [user['id'] for user in Event.regional_coordinators(
                figure.event,
                actor=info.context.user,
            )]
            if figure.event.created_by_id:
                recipients.append(figure.event.created_by_id)

            Notification.send_safe_multiple_notifications(
                recipients=recipients,
                type=_type,
                actor=info.context.user,
                event=figure.event,
                entry=figure.entry,
                figure=figure,
            )

        # Update event status
        Figure.update_event_status_and_send_notifications(figure.event_id)
        figure.event.refresh_from_db()

        return UnapproveFigure(result=figure, errors=None, ok=True)


class ReRequestReviewFigure(graphene.Mutation):
    """
    Class: ReRequestReviewFigure

    A GraphQL mutation class to re-request review for a figure.

    Attributes:
        - id: Required argument of type ID representing the ID of the figure.

    Methods:
        - mutate(root, info, id):
            Static method to perform the mutation operation.
            Args:
                - root: The root object of the mutation.
                - info: Information about the execution.
                - id: The ID of the figure to re-request review for.
            Returns:
                An instance of the ReRequestReviewFigure class with the following attributes:
                    - errors: A list of CustomErrorType objects representing any errors that occurred during the mutation.
                    - ok: A boolean indicating if the mutation was successful.
                    - result: A Field object of type FigureType representing the updated figure after re-requesting review.

            Raises:
                None
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(FigureType)

    @staticmethod
    @permission_checker(['entry.change_figure'])
    @is_authenticated()
    def mutate(root, info, id):
        figure = Figure.objects.filter(id=id).first()
        if not figure:
            return ReRequestReviewFigure(errors=[
                dict(field='nonFieldErrors', messages=gettext('Figure does not exist.'))
            ])

        # NOTE: State machine with states defined in FIGURE_REVIEW_STATUS
        if figure.review_status != Figure.FIGURE_REVIEW_STATUS.REVIEW_IN_PROGRESS:
            return ReRequestReviewFigure(errors=[
                dict(field='nonFieldErrors', messages=gettext('Only in-progress figures can be re-requested review'))
            ])

        figure.review_status = Figure.FIGURE_REVIEW_STATUS.REVIEW_RE_REQUESTED
        figure.approved_by = None
        figure.approved_on = None
        figure.save()

        if figure.event.assignee_id:
            Notification.send_safe_multiple_notifications(
                event=figure.event,
                figure=figure,
                entry=figure.entry,
                recipients=[figure.event.assignee_id],
                actor=info.context.user,
                type=Notification.Type.FIGURE_RE_REQUESTED_REVIEW,
            )

        Figure.update_event_status_and_send_notifications(figure.event_id)
        figure.event.refresh_from_db()

        return ReRequestReviewFigure(result=figure, errors=None, ok=True)


class BulkUpdateFigures(BulkUpdateMutation):
    """

    Class: BulkUpdateFigures

    This class is responsible for bulk updating the figures in the database.

    Attributes:
    - model (Figure): Specifies the model class to be updated.
    - serializer_class (FigureSerializer): Specifies the serializer class to be used for serialization.
    - result (List[FigureType]): Provides a list of figures after the bulk update operation.
    - deleted_result (List[FigureType]): Provides a list of figures that were deleted during the bulk update operation.
    - permissions (List[str]): Specifies the list of permissions required for performing the bulk update operation.

    Methods:
    - get_queryset(): Returns a QuerySet containing all the figures.
    - delete_item(figure, context): Deletes the given figure and performs additional operations like sending notifications and adding an event to the bulk manager.
    - mutate(*args, **kwargs): Executes the bulk update mutation operation using the BulkUpdateFigureManager.

    """
    class Arguments(BulkUpdateMutation.Arguments):
        items = graphene.List(graphene.NonNull(FigureUpdateInputType))

    model = Figure
    serializer_class = FigureSerializer
    result = graphene.List(FigureType)
    deleted_result = graphene.List(graphene.NonNull(FigureType))
    permissions = ['entry.add_figure', 'entry.change_figure', 'entry.delete_figure']

    @staticmethod
    def get_queryset():
        return Figure.objects.all()

    @classmethod
    @transaction.atomic
    def delete_item(cls, figure, context):
        bulk_manager: BulkUpdateFigureManager = context['bulk_manager']
        figure = super().delete_item(figure, context)

        if notification_type := get_figure_notification_type(figure.event, is_deleted=True):
            send_figure_notifications(
                figure,
                context['request'].user,
                notification_type,
                is_deleted=True,
            )
        bulk_manager.add_event(figure.event_id)
        return figure

    @classmethod
    def mutate(cls, *args, **kwargs):
        with BulkUpdateFigureManager() as bulk_manager:
            return super().mutate(*args, **kwargs, context={'bulk_manager': bulk_manager})


class Mutation(object):
    """

    """
    create_entry = CreateEntry.Field()
    update_entry = UpdateEntry.Field()
    delete_entry = DeleteEntry.Field()
    # source preview
    create_source_preview = CreateSourcePreview.Field()
    # figure tags
    create_figure_tag = CreateFigureTag.Field()
    update_figure_tag = UpdateFigureTag.Field()
    delete_figure_tag = DeleteFigureTag.Field()
    # exports
    export_entries = ExportEntries.Field()
    export_figures = ExportFigures.Field()
    export_figure_tags = ExportFigureTags.Field()
    bulk_update_figures = BulkUpdateFigures.Field()
    # figure
    delete_figure = DeleteFigure.Field()
    approve_figure = ApproveFigure.Field()
    unapprove_figure = UnapproveFigure.Field()
    re_request_review_figure = ReRequestReviewFigure.Field()

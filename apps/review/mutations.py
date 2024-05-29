import graphene
from django.utils.translation import gettext

from apps.review.models import UnifiedReviewComment
from apps.review.schema import UnifiedReviewCommentType
from apps.review.serializers import UnifiedReviewCommentSerializer
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker
from utils.mutation import generate_input_type_for_serializer
from apps.notification.models import Notification


UnifiedReviewCommentCreateInputType = generate_input_type_for_serializer(
    'UnifiedReviewCommentCreateInputType',
    UnifiedReviewCommentSerializer
)


class UnifiedReviewCommentUpdateInputType(graphene.InputObjectType):
    """

    Class: UnifiedReviewCommentUpdateInputType

    Represents an input object type for updating a review comment.

    Attributes:
    - id: The unique ID of the comment. (Required)
    - comment: The updated comment text. (Required)

    """
    id = graphene.ID(required=True)
    comment = graphene.String(required=True)


class CreateUnifiedReviewComment(graphene.Mutation):
    """
    Mutation class for creating a unified review comment.

    Args:
        data (UnifiedReviewCommentCreateInputType): The input data for creating a unified review comment.

    Returns:
        CreateUnifiedReviewComment: An instance of the CreateUnifiedReviewComment class.

    Attributes:
        ok (bool): Indicates whether the mutation was successful or not.
        errors (List[CustomErrorType]): A list of error messages, if any.
        result (UnifiedReviewCommentType): The created unified review comment.

    Methods:
        mutate(root, info, data): Method for executing the mutation and creating the unified review comment.
    """
    class Arguments:
        data = UnifiedReviewCommentCreateInputType(required=True)

    ok = graphene.Boolean()
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    result = graphene.Field(UnifiedReviewCommentType)

    @staticmethod
    @permission_checker(['review.add_reviewcomment'])
    def mutate(root, info, data):
        from apps.entry.models import Figure

        serializer = UnifiedReviewCommentSerializer(
            data=data,
            context={'request': info.context.request}, partial=True
        )
        if serializer.is_valid():
            serialized_data = serializer.validated_data
            comment_type = serialized_data.get('comment_type')
            event = serialized_data.get('event')
            figure = serialized_data.get('figure')

            if (
                event and
                comment_type != UnifiedReviewComment.REVIEW_COMMENT_TYPE.GREY and
                (not event.assignee or event.assignee != info.context.user)
            ):
                return CreateUnifiedReviewComment(
                    errors=[
                        dict(field='nonFieldErrors',
                             messages=gettext('Assignee not set or you are not the assignee.'))
                    ],
                    ok=False
                )

            # NOTE: State machine with states defined in FIGURE_REVIEW_STATUS
            if figure and figure.review_status == Figure.FIGURE_REVIEW_STATUS.REVIEW_NOT_STARTED:
                figure.review_status = Figure.FIGURE_REVIEW_STATUS.REVIEW_IN_PROGRESS
                figure.save()
            elif (
                figure and
                figure.review_status == Figure.FIGURE_REVIEW_STATUS.REVIEW_RE_REQUESTED and
                figure.event.assignee_id and
                info.context.user.id == figure.event.assignee_id
            ):
                figure.review_status = Figure.FIGURE_REVIEW_STATUS.REVIEW_IN_PROGRESS
                figure.save()

            if event:
                Figure.update_event_status_and_send_notifications(event.id)
                event.refresh_from_db()

        if errors := mutation_is_not_valid(serializer):
            return CreateUnifiedReviewComment(errors=errors, ok=False)
        instance = serializer.save()

        if instance.figure and instance.event and instance.event.assignee_id:
            Notification.send_safe_multiple_notifications(
                recipients=[instance.event.assignee_id],
                event=instance.event,
                entry=instance.figure.entry,
                figure=instance.figure,
                actor=info.context.user,
                type=Notification.Type.REVIEW_COMMENT_CREATED,
                review_comment=instance,
            )

        if instance.figure and instance.event and instance.figure.created_by_id:
            Notification.send_safe_multiple_notifications(
                recipients=[instance.figure.created_by_id],
                event=instance.event,
                entry=instance.figure.entry,
                figure=instance.figure,
                actor=info.context.user,
                type=Notification.Type.REVIEW_COMMENT_CREATED,
                review_comment=instance,
            )
        return CreateUnifiedReviewComment(result=instance, errors=None, ok=True)


class UpdateUnifiedReviewComment(graphene.Mutation):
    """

    This class represents a GraphQL mutation for updating a UnifiedReviewComment object.

    Attributes:
        Arguments:
            - data (UnifiedReviewCommentUpdateInputType): The input data for updating the UnifiedReviewComment object.
        ok (Boolean): Indicates whether the mutation was successful or not.
        errors (List[CustomErrorType]): A list of custom error types that occurred during the mutation process.
        result (UnifiedReviewCommentType): The updated UnifiedReviewComment object.

    Methods:
        mutate (staticmethod): Updates the UnifiedReviewComment object based on the provided input data.

    """
    class Arguments:
        data = UnifiedReviewCommentUpdateInputType(required=True)

    ok = graphene.Boolean()
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    result = graphene.Field(UnifiedReviewCommentType)

    @staticmethod
    @permission_checker(['review.change_reviewcomment'])
    def mutate(root, info, data):
        try:
            instance = UnifiedReviewComment.objects.get(created_by=info.context.user, id=data['id'])
        except UnifiedReviewComment.DoesNotExist:
            return UpdateUnifiedReviewComment(
                errors=[
                    dict(field='nonFieldErrors',
                         messages=gettext('Comment does not exist.'))
                ],
                ok=False
            )
        serializer = UnifiedReviewCommentSerializer(
            instance=instance,
            data=data,
            context={'request': info.context.request}, partial=True
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateUnifiedReviewComment(errors=errors, ok=False)
        instance = serializer.save()
        instance.is_edited = True
        instance.save()
        return UpdateUnifiedReviewComment(result=instance, errors=None, ok=True)


class DeleteUnifiedReviewComment(graphene.Mutation):
    """
    The DeleteUnifiedReviewComment class is a mutation class that allows a user to delete a unified review comment. It is a specific implementation of the graphene.Mutation class.

    Attributes:
        - Arguments: A nested class that defines the input arguments for the mutation. It contains a single argument, id, which is a required graphene.ID field.
        - ok: A graphene.Boolean field indicating whether the deletion was successful.
        - errors: A list of CustomErrorType objects representing any errors that occurred during the deletion.
        - result: A graphene.Field object representing the deleted UnifiedReviewComment object.

    Methods:
        - mutate: A static method that executes the mutation logic. It takes in the root, info, and id arguments. It performs the following steps:
            1. Retrieves the UnifiedReviewComment object with the specified id, created by the authenticated user.
            2. If no such UnifiedReviewComment exists, returns an instance of DeleteUnifiedReviewComment with appropriate errors and ok=False.
            3. Sets the is_deleted field of the UnifiedReviewComment object to True and clears the comment field.
            4. Saves the changes to the UnifiedReviewComment object.
            5. Returns an instance of DeleteUnifiedReviewComment with the deleted UnifiedReviewComment object as the result, no errors, and ok=True.
    """
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    result = graphene.Field(UnifiedReviewCommentType)

    @staticmethod
    @permission_checker(['review.delete_reviewcomment'])
    def mutate(root, info, id):
        try:
            instance = UnifiedReviewComment.objects.get(
                created_by=info.context.user,
                id=id
            )
        except UnifiedReviewComment.DoesNotExist:
            return DeleteUnifiedReviewComment(
                errors=[
                    dict(field='nonFieldErrors',
                         messages=gettext('Comment does not exist.'))
                ],
                ok=False
            )
        instance.is_deleted = True
        instance.comment = None
        instance.save()
        # FIXME: Don't we need to update the status here?
        return DeleteUnifiedReviewComment(result=instance, errors=None, ok=True)


class Mutation(object):
    """
    This class defines the mutation operations for review comments.

    Methods:
        create_review_comment: Creates a new review comment.
        update_review_comment: Updates an existing review comment.
        delete_review_comment: Deletes a review comment.
    """
    create_review_comment = CreateUnifiedReviewComment.Field()
    update_review_comment = UpdateUnifiedReviewComment.Field()
    delete_review_comment = DeleteUnifiedReviewComment.Field()

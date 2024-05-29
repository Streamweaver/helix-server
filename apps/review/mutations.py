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
    A class representing the input data for updating a unified review comment.

    Attributes:
        id (str): The ID of the review comment that needs to be updated.
        comment (str): The new comment for the review.
    """
    id = graphene.ID(required=True)
    comment = graphene.String(required=True)


class CreateUnifiedReviewComment(graphene.Mutation):
    """
    Class: CreateUnifiedReviewComment

    This class represents a graphene Mutation for creating a unified review comment. It is used to create a new review comment in the system.

    Properties:
    - ok (Boolean): Indicates if the mutation was successful or not.
    - errors (List[CustomErrorType]): List of errors that occurred during the mutation process.
    - result (UnifiedReviewCommentType): The created unified review comment instance.

    Methods:
    - mutate(root, info, data): Static method that handles the mutation process. It takes the root, info, and data arguments. The root argument is the root value for the query. The info argument provides information about the execution state of the query. The data argument is an instance of the UnifiedReviewCommentCreateInputType class, which contains the data for creating the review comment.

    Dependencies:
    - graphene.Mutation: The base class for creating mutations in graphene.

    Example Usage:
    data = UnifiedReviewCommentCreateInputType(required=True)
    mutation = CreateUnifiedReviewComment.mutate(None, None, data)
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
    Class: UpdateUnifiedReviewComment

    Description:
        This class is responsible for updating a unified review comment. It is a graphene mutation class that takes in a UnifiedReviewCommentUpdateInputType object as an argument.

    Attributes:
        - ok (graphene.Boolean): A boolean indicating whether the update operation was successful or not.
        - errors (graphene.List[CustomErrorType]): A list of custom error types that occurred during the update operation.
        - result (graphene.Field[UnifiedReviewCommentType]): A field containing the updated unified review comment.

    Methods:
        mutate(root, info, data):
            This method is a static method and is decorated with a permission checker. It is responsible for performing the update operation on the unified review comment.

            Parameters:
                - root: The root value, corresponding to the top-level value passed to the schema's executor.
                - info: The GraphQL ResolveInfo object containing information about the execution state.
                - data: The input data of type UnifiedReviewCommentUpdateInputType.

            Returns:
                An instance of UpdateUnifiedReviewComment with the updated unified review comment, any errors that occurred, and a boolean indicating the success of the operation.
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

    DeleteUnifiedReviewComment

    mutation class used to delete a unified review comment.

    Args:
        id (str): The ID of the unified review comment to be deleted. (required)

    Returns:
        ok (bool): Indicates whether the deletion was successful.
        errors (list): A list of custom error messages, if any.
        result (UnifiedReviewCommentType): The deleted unified review comment instance.

    Raises:
        N/A

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

    Mutation class

    This class represents a collection of GraphQL mutation operations.

    Attributes:
        create_review_comment (Field): A field for creating a review comment.
        update_review_comment (Field): A field for updating a review comment.
        delete_review_comment (Field): A field for deleting a review comment.

    """
    create_review_comment = CreateUnifiedReviewComment.Field()
    update_review_comment = UpdateUnifiedReviewComment.Field()
    delete_review_comment = DeleteUnifiedReviewComment.Field()

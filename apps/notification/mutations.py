import graphene
from django.utils.translation import gettext
from apps.notification.models import Notification
from utils.error_types import CustomErrorType
from apps.notification.schema import GenericNotificationType


class ToggleNotificationRead(graphene.Mutation):
    """
    ToggleNotificationRead class is a mutation class that is responsible for toggling the read status of a notification. It takes the notification ID as an argument and returns the updated notification object along with an 'ok' flag and any errors that may occur.

    Args:
        id (graphene.ID): The ID of the notification that needs to be toggled.

    Returns:
        - ok (graphene.Boolean): A boolean flag indicating whether the mutation was successful or not.
        - errors (List[graphene.NonNull(CustomErrorType)]): A list of custom error objects (CustomErrorType) that may occur during the mutation process.
        - result (graphene.Field(GenericNotificationType)): The updated notification object.

    """
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    result = graphene.Field(GenericNotificationType)

    @staticmethod
    def mutate(root, info, id):
        instance = Notification.objects.filter(
            recipient=info.context.user,
            id=id
        ).first()
        if not instance:
            return ToggleNotificationRead(
                errors=[
                    dict(field='nonFieldErrors',
                         messages=gettext('Notification does not exist or you are not recipient.'))
                ],
                ok=False
            )
        if not instance.is_read:
            instance.is_read = True
        else:
            instance.is_read = False
        instance.save()
        return ToggleNotificationRead(result=instance, errors=None, ok=True)


class Mutation(object):
    """
    This class represents a mutation for toggling the read status of a notification.

    Attributes:
        toggle_notification_read (ToggleNotificationRead.Field): A field representing the toggle_notification_read mutation.

    """
    toggle_notification_read = ToggleNotificationRead.Field()

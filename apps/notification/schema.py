import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField

from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount
from utils.graphene.enums import EnumDescription

from apps.notification.models import Notification
from apps.notification.enums import NotificationTypeEnum
from apps.notification.filters import NotificationFilter


def notificaiton_qs(info):
    """
    Queries the database for notifications related to the current user.

    :param info: GraphQL context object containing information about the current execution
    :return: QuerySet of notification objects filtered by recipient as the current user
    """
    return Notification.objects.filter(recipient=info.context.user)


class GenericNotificationType(DjangoObjectType):
    """
    GenericNotificationType

    A class representing the GraphQL ObjectType for the Notification model.

    Attributes:
        type: A graphene.Field representing the NotificationTypeEnum of the notification.
        type_display: A EnumDescription field representing the display value of the notification type.

    Methods:
        get_custom_queryset(queryset, info): A static method that returns a modified queryset based on the provided info.

    """
    class Meta:
        model = Notification
        fields = (
            'id',
            'type',
            'recipient',
            'actor',
            'event',
            'figure',
            'entry',
            'review_comment',
            'is_read',
            'text',
            'created_at',
        )

    type = graphene.Field(NotificationTypeEnum)
    type_display = EnumDescription(source='get_type_display')

    @staticmethod
    def get_custom_queryset(queryset, info):
        # FIXME: Improve utils
        return notificaiton_qs(info)


class GenericNotificationListType(CustomDjangoListObjectType):
    """

    GenericNotificationListType is a class that inherits from CustomDjangoListObjectType.

    Attributes:
        Meta (class): A class that contains meta information about the GenericNotificationListType class.

        - model (model class): The Django model class for the Notification model.

        - filterset_class (class): The Django filterset class for filtering the notifications.

    """
    class Meta:
        model = Notification
        filterset_class = NotificationFilter


class Query(object):
    """
    Class: Query

    This class represents the query resolver for GraphQL queries related to notifications.

    Attributes:
    - notification: A DjangoObjectField representing a single notification.
    - notifications: A DjangoPaginatedListObjectField representing a paginated list of notifications.

    Methods:
    - resolve_notification(root, info, **kwargs): This method is used to resolve the 'notification' field in the query.
        - Parameters:
            - root: The root object.
            - info: The GraphQLResolveInfo object.
            - **kwargs: Additional keyword arguments.
        - Returns:
            - If the user is authenticated, it returns the result of the `notification_qs(info)` function, which represents the query to fetch the notification.
            - Otherwise, it returns an empty list.
    """
    notification = DjangoObjectField(GenericNotificationType)
    notifications = DjangoPaginatedListObjectField(
        GenericNotificationListType,
        pagination=PageGraphqlPaginationWithoutCount(
            page_size_query_param='pageSize'
        ),
    )

    def resolve_notification(root, info, **kwargs):
        # FIXME: This resolver does not work, improve utils to fix this
        if info.context.user.is_authenticated:
            return notificaiton_qs(info)
        return []

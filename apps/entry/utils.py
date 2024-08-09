import typing

from apps.entry.models import Figure
from apps.event.models import Event
from apps.notification.models import Notification
from apps.users.models import User


def get_figure_notification_type(event, is_deleted=False, is_new=False):
    """
    Determines the notification type based on the event review status and delete/new flags.

    :param event: The event object containing the review status.
    :param is_deleted: Flag indicating whether the figure has been deleted.
    :param is_new: Flag indicating whether the figure is new.
    :return: The notification type based on the event review status and flags.
    """
    if event.review_status in [
        Event.EVENT_REVIEW_STATUS.SIGNED_OFF,
        Event.EVENT_REVIEW_STATUS.SIGNED_OFF_BUT_CHANGED,
    ]:
        if is_deleted:
            return Notification.Type.FIGURE_DELETED_IN_SIGNED_EVENT
        if is_new:
            return Notification.Type.FIGURE_CREATED_IN_SIGNED_EVENT
        # For update
        return Notification.Type.FIGURE_UPDATED_IN_SIGNED_EVENT

    elif event.review_status in [
        Event.EVENT_REVIEW_STATUS.APPROVED,
        Event.EVENT_REVIEW_STATUS.APPROVED_BUT_CHANGED,
    ]:
        if is_deleted:
            return Notification.Type.FIGURE_DELETED_IN_APPROVED_EVENT
        if is_new:
            return Notification.Type.FIGURE_CREATED_IN_APPROVED_EVENT
        # For update
        return Notification.Type.FIGURE_UPDATED_IN_APPROVED_EVENT


def get_event_notification_type(event, is_figure_deleted=False, is_figure_new=False):
    """Get the event notification type based on the event type and figure status.

    Args:
        event (str): The event type.
        is_figure_deleted (bool): Optional. Whether the figure is deleted. Default is False.
        is_figure_new (bool): Optional. Whether the figure is new. Default is False.

    Returns:
        str: The event notification type.

    """
    return get_figure_notification_type(event, is_deleted=is_figure_deleted, is_new=is_figure_new)


def send_figure_notifications(
    figure: Figure,
    actor: User,
    notification_type: Notification.Type,
    is_deleted: bool = False,
    event: typing.Optional[Event] = None,
):
    """
    Sends figure notifications to the relevant recipients.

    Parameters:
    - figure (Figure): The figure object for which the notifications need to be sent.
    - actor (User): The user who initiated the action that triggered the notifications.
    - notification_type (Notification.Type): The type of notifications to be sent.
    - is_deleted (bool): Optional. Indicates whether the figure has been deleted. Defaults to False.
    - event (Optional[Event]): Optional. The event to which the figure belongs. Defaults to None.

    Returns:
    None
    """
    _event = event or figure.event

    recipients = [
        user['id']
        for user in Event.regional_coordinators(
            _event,
            actor=actor,
        )
    ]
    if _event.created_by_id:
        recipients.append(_event.created_by_id)
    if _event.assignee_id:
        recipients.append(_event.assignee_id)

    Notification.send_safe_multiple_notifications(
        recipients=recipients,
        actor=actor,
        event=_event,
        entry=figure.entry,
        type=notification_type,
        **(
            dict(figure=figure)
            if not is_deleted else dict()
        ),
    )


class BulkUpdateFigureManager():
    """
    Class to manage bulk updates of figure events.

    Attributes:
    - event_ids (typing.Set[int]): Set to store event ids that need to be updated.
    - figure_moved_from_event (typing.Set[Event]): Set to store events from which the figure was moved.
    - figure_moved_to_event (typing.Set[Event]): Set to store events to which the figure was moved.

    Methods:
    - __enter__(): Enter method for context management.
    - add_event(event_id: int): Add an event id to the set of events to be updated.
    - __exit__(exc_type, exc_value, exc_traceback): Exit method for context management.

    Usage:
    with BulkUpdateFigureManager() as manager:
        manager.add_event(1)
        manager.add_event(2)
        ...
    """
    event_ids: typing.Set[int]
    figure_moved_from_event: typing.Set[Event]
    figure_moved_to_event: typing.Set[Event]

    def __enter__(self):
        self.event_ids = set()
        self.figure_moved_from_event = set()
        self.figure_moved_to_event = set()
        return self

    def add_event(self, event_id: int):
        self.event_ids.add(event_id)

    # Note: Using *_ will make typing make this as non context manager
    def __exit__(self, exc_type, exc_value, exc_traceback):
        # Update status
        for event_id in self.event_ids:
            Figure.update_event_status_and_send_notifications(event_id)

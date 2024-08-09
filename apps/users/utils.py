from typing import Union
from contextlib import contextmanager

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import DjangoUnicodeDecodeError
from django.conf import settings
from djoser.compat import get_user_email
from djoser.email import ActivationEmail
from djoser.utils import decode_uid

from apps.users.models import User, Portfolio


def send_activation_email(user, request) -> None:
    """

    Sends an activation email to the user.

    Parameters:
    - user: The user object for whom the activation email needs to be sent.
    - request: The request object associated with the current activation request.

    Return type: None

    """
    to = [get_user_email(user)]
    ActivationEmail(request, {'user': user}).send(to)


def get_user_from_activation_token(uid, token) -> Union[User, None]:
    """

    Method to retrieve a user object based on an activation token.

    Parameters:
    - uid (str): The encoded user ID.
    - token (str): The activation token.

    Returns:
    - User or None: If the user is found and the token is valid, the corresponding User object is returned. If not found
    or the token is not valid, None is returned.

    """
    try:
        uid = decode_uid(uid)
    except DjangoUnicodeDecodeError:
        return None
    try:
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError):
        return None
    if not default_token_generator.check_token(user, token):
        return None
    return user


class HelixInternalBot:
    """

    A class representing the HelixInternalBot.

    Attributes:
    - user (User): The user associated with the internal bot.

    Methods:
    - __init__(): Initializes the internal bot and sets the user attribute.
    - temporary_role(): A context manager that temporarily assigns a role to the internal bot's user.

    """
    user: User

    def __init__(self):
        # TODO: We need to flag bounce email if we send email in future
        self.user, _ = User.objects.get_or_create(email=settings.INTERNAL_BOT_EMAIL)

    @contextmanager
    def temporary_role(self, role):
        temp_role, _ = Portfolio.objects.get_or_create(
            user=self.user,
            role=role,
        )
        try:
            yield temp_role
        finally:
            temp_role.delete()

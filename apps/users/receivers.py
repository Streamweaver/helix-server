from django.db.models.signals import (
    post_save,
    post_delete,
)
from django.dispatch import receiver

from .enums import USER_ROLE
from .models import User, Portfolio


def set_user_role(user: User) -> None:
    """
    Set User Role

    Sets the highest role for the specified User.

    Parameters:
    - user (User): The User object for which to set the role.

    Returns:
    None
    """
    user.set_highest_role()


def remove_guest_portfolio(user: User):
    """
    Removes the guest portfolio for the specified user.

    Parameters:
    - user (User): The user for whom the guest portfolio should be removed.

    Returns:
    None
    """
    if user.portfolios.count() > 1:
        Portfolio.objects.filter(
            user=user,
            role=USER_ROLE.GUEST
        ).delete()


def add_guest_portfolio(user: User):
    """

    Add Guest Portfolio

    This method adds a guest portfolio for a given user.

    Parameters:
    - user (User): The user for whom the guest portfolio will be added.

    Returns:
    None

    """
    if user.portfolios.count() == 0:
        Portfolio.objects.create(
            user=user,
            role=USER_ROLE.GUEST
        )


@receiver(post_save, sender=User)
def add_default_guest_portfolio(sender, instance, **kwargs):
    """
    This method is a receiver function that is triggered after a User model instance is saved.
    It adds a default guest portfolio to the user and sets the user's role.

    Parameters:
    - sender (Model): The model class responsible for sending the signal.
    - instance (User): The User model instance that is being saved.

    Returns:
    None
    """
    add_guest_portfolio(instance)
    set_user_role(instance)


@receiver(post_delete, sender=Portfolio)
def update_user_group_post_delete(sender, instance, **kwargs):
    """
    Update user group after deleting a portfolio.

    This method is a receiver for the `post_delete` signal of the `Portfolio` model.
    It updates the user group by adding the user to the 'guest' group and setting their role.

    Args:
        sender (Type[Portfolio]): The model class that sent the signal.
        instance (Portfolio): The instance being deleted.
        kwargs (dict): Additional keyword arguments.

    Returns:
        None

    """
    add_guest_portfolio(instance.user)
    set_user_role(instance.user)


@receiver(post_save, sender=Portfolio)
def update_user_group_post_save(sender, instance, **kwargs):
    """
    Update the user group after saving a portfolio.

    This method is triggered by the post_save signal when a Portfolio object is saved. It updates the user group of the
    user associated with the portfolio by removing their guest portfolio status and setting their role.

    Args:
        sender (class): The class sending the signal.
        instance (Portfolio): The saved Portfolio instance.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    remove_guest_portfolio(instance.user)
    set_user_role(instance.user)

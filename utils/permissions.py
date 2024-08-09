import hashlib
from typing import List, Callable
import logging

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext

PERMISSION_DENIED_MESSAGE = 'You do not have permission to perform this action.'

logger = logging.getLogger(__name__)


def permission_checker(perms: List[str]) -> Callable[..., Callable]:
    """

    :param perms: List of permissions required for the wrapped function
    :type perms: List[str]
    :return: Callable function
    :rtype: Callable[..., Callable]

    This method is a decorator that checks if the current user has the required permissions before executing the wrapped
    function. It takes a list of permissions as input and returns a function decorator.

    The decorator function takes the wrapped function as input and returns a new function that checks if the user has
    the required permissions. If the user does not have the required permissions, a `PermissionDenied` exception is
    raised. Otherwise, the wrapped function is executed with the provided arguments and keyword arguments.

    Example usage:

    ```python
    @permission_checker(["permission1", "permission2"])
    def my_function(root, info, arg1, arg2):
        # Function code here
        pass
    ```

    In this example, the `my_function` is decorated with the `permission_checker` decorator, which requires the user to
    have both "permission1" and "permission2" permissions. If the user has the required permissions, the function will
    be executed as usual. If not, a `PermissionDenied` exception will be raised.

    Note: The `PermissionDenied` exception is assumed to be imported from the appropriate module, and the
    `PERMISSION_DENIED_MESSAGE` constant is assumed to be defined elsewhere in the code.

    """
    def wrapped(func):
        def wrapped_func(root, info, *args, **kwargs):
            if not info.context.user.has_perms(perms):
                raise PermissionDenied(gettext(PERMISSION_DENIED_MESSAGE))
            return func(root, info, *args, **kwargs)
        return wrapped_func
    return wrapped


def is_authenticated() -> Callable[..., Callable]:
    """
    Check if the user is authenticated before executing the wrapped function.

    Returns:
        A callable function that wraps the provided function.

    Raises:
        PermissionDenied: If the user is not authenticated.

    Example usage:
        @is_authenticated()
        def my_func(root, info, *args, **kwargs):
            # Function code goes here
            pass
    """
    def wrapped(func):
        def wrapped_func(root, info, *args, **kwargs):
            if not info.context.user.is_authenticated:
                raise PermissionDenied(gettext(PERMISSION_DENIED_MESSAGE))
            return func(root, info, *args, **kwargs)
        return wrapped_func
    return wrapped


def cache_key_function(*args, **kwargs):
    """
        Generates a cache key based on the provided arguments.

        Args:
            *args: The positional arguments to include in the cache key.
            **kwargs: The keyword arguments to include in the cache key.

        Returns:
            The cache key as a hexadecimal string.

        Raises:
            None.

        Example:
            cache_key_function('arg1', arg2='value2')
            => 'c3bfc6483193a2789a1c920eeb719448924c62c2d5f491c25f184b2134c663ce'
    """
    logger.error('cache key')
    return hashlib.sha256((str(args) + str(kwargs)).encode()).hexdigest()


def cache_me(timeout=None):
    """
    Cache the function's return value for a specified amount of time.

    Parameters:
    - timeout (float, optional): The time in seconds for which the value should be cached. If not specified, the value
    will be cached indefinitely.

    Returns:
    - function: A wrapper function that caches the return value of the decorated function.
    """
    def wrapped(func):
        def wrapped_func(*args, **kwargs):
            cache_key = cache_key_function(func.__name__, *args, **kwargs)
            cached_value = cache.get(cache_key)
            if cached_value:
                return cached_value
            value = func(*args, **kwargs)
            cache.set(cache_key, value, timeout)
            return value
        return wrapped_func
    return wrapped

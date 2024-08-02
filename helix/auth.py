from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext

PERMISSION_DENIED_MESSAGE = 'You do not have permission to perform this action.'


class WhiteListMiddleware:
    """
    Class: WhiteListMiddleware

    This class provides middleware functionality to check if a user is authenticated and has access to whitelisted nodes
    in a GraphQL API.

    Attributes:
        None

    Methods:
        - resolve(next, root, info, **args): This method is a custom resolver that gets called by the GraphQL execution
        engine for each resolver in the execution process. It checks if the user is authenticated and has access to the
        requested node. If not, it raises a PermissionDenied exception. This check is only performed at the root node
        and not in deeper nodes.

    Args:
        - next: The next resolver function to be called in the execution process.
        - root: The resolved value of the parent field. None for the root field.
        - info: A GraphQL ResolveInfo object that provides information about the execution state.
        - **args: Keyword arguments that represent the field arguments passed by the client.

    Returns:
        The result of calling the next resolver function with the provided arguments.

    Raises:
        - PermissionDenied: If the user is not authenticated and the requested node is not in the whitelist.

    Example Usage:
        # Create an instance of the WhiteListMiddleware class
        whitelist_middleware = WhiteListMiddleware()

        # Invoke the resolve method passing the required arguments
        result = whitelist_middleware.resolve(next_resolver, root_value, resolve_info, **arguments)
    """
    def resolve(self, next, root, info, **args):
        # if user is not authenticated and user is not accessing
        # whitelisted nodes, then raise permission denied error

        # furthermore, this check must only happen in the root node, and not in deeper nodes
        if root is None:
            if not info.context.user.is_authenticated and info.field_name not in settings.GRAPHENE_NODES_WHITELIST:
                raise PermissionDenied(gettext(PERMISSION_DENIED_MESSAGE))
        return next(root, info, **args)

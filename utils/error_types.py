from typing import List

import graphene
from graphene import ObjectType
from graphene.types.generic import GenericScalar
from graphene.utils.str_converters import to_snake_case
from graphene_django.utils.utils import _camelize_django_str

ARRAY_NON_MEMBER_ERRORS = 'nonMemberErrors'
# generalize all the CustomErrorType
CustomErrorType = GenericScalar


class ArrayNestedErrorType(ObjectType):
    """
    A class representing an array nested error with key, messages, and object_errors.

    Attributes:
        key (str): The key of the array nested error.
        messages (str): The messages associated with the array nested error.
        object_errors (List[CustomErrorType]): The list of custom error types associated with the array nested error.
    """
    key = graphene.String(required=True)
    messages = graphene.String(required=False)
    object_errors = graphene.List(graphene.NonNull("utils.error_types.CustomErrorType"))

    def keys(self):
        return ['key', 'messages', 'objectErrors']

    def __getitem__(self, key):
        key = to_snake_case(key)
        if key in ('object_errors',) and getattr(self, key):
            return [dict(each) for each in getattr(self, key)]
        return getattr(self, key)


class _CustomErrorType(ObjectType):
    """
    Class: _CustomErrorType

    This class represents a custom error type. It is a subclass of ObjectType.

    Attributes:
    - field (str): The field related to the error.
    - messages (str, optional): Additional error messages.
    - object_errors (list[_CustomErrorType]): A list of nested _CustomErrorType objects.
    - array_errors (list[ArrayNestedErrorType]): A list of nested ArrayNestedErrorType objects.

    Methods:
    - keys(): Returns a list of valid keys for this object.
    - __getitem__(key): Returns the value of the specified key.

    Example usage:
        error = _CustomErrorType()
        error.field = "email"
        error.messages = "Invalid email format"
        nested_error = _CustomErrorType()
        nested_error.field = "name"
        nested_error.messages = "Name is required"
        error.object_errors = [nested_error]
        keys = error.keys()
        value = error['field']

    Note: Please ensure that the related import statements are included when using this class.
    """
    field = graphene.String(required=True)
    messages = graphene.String(required=False)
    object_errors = graphene.List(graphene.NonNull("utils.error_types.CustomErrorType"))
    array_errors = graphene.List(graphene.NonNull(ArrayNestedErrorType))

    def keys(self):
        return ['field', 'messages', 'objectErrors', 'arrayErrors']

    def __getitem__(self, key):
        key = to_snake_case(key)
        if key in ('object_errors', 'array_errors') and getattr(self, key):
            return [dict(each) for each in getattr(self, key)]
        return getattr(self, key)


def serializer_error_to_error_types(errors: dict, initial_data: dict = None) -> List:
    """
    Convert serializer errors to custom error types.

    Args:
        errors (dict): The serializer errors.
        initial_data (dict, optional): The initial data. Defaults to None.

    Returns:
        List: The list of custom error types.
    """
    initial_data = initial_data or dict()
    error_types = list()
    for field, value in errors.items():
        if isinstance(value, dict):
            error_types.append(_CustomErrorType(
                field=_camelize_django_str(field),
                object_errors=serializer_error_to_error_types(value)
            ))
        elif isinstance(value, list):
            if isinstance(value[0], str):
                if isinstance(initial_data.get(field), list):
                    # we have found an array input with top level error
                    error_types.append(_CustomErrorType(
                        field=_camelize_django_str(field),
                        array_errors=[ArrayNestedErrorType(
                            key=ARRAY_NON_MEMBER_ERRORS,
                            messages=''.join(str(msg) for msg in value)
                        )]
                    ))
                else:
                    error_types.append(_CustomErrorType(
                        field=_camelize_django_str(field),
                        messages=''.join(str(msg) for msg in value)
                    ))
            elif isinstance(value[0], dict):
                array_errors = []
                for pos, array_item in enumerate(value):
                    if not array_item:
                        # array item might not have error
                        continue
                    # fetch array.item.uuid from the initial data
                    key = initial_data[field][pos].get('uuid', f'NOT_FOUND_{pos}')
                    array_errors.append(ArrayNestedErrorType(
                        key=key,
                        object_errors=serializer_error_to_error_types(array_item, initial_data[field][pos])
                    ))
                error_types.append(_CustomErrorType(
                    field=_camelize_django_str(field),
                    array_errors=array_errors
                ))
        else:
            # fallback
            error_types.append(_CustomErrorType(
                field=_camelize_django_str(field),
                messages=' '.join(str(msg) for msg in value)
            ))
    return error_types


def mutation_is_not_valid(serializer) -> List[dict]:
    """
    Checks if the given serializer is valid.

    If the serializer is not valid, it converts the serializer errors to a list of dictionaries
    representing the error types and returns it. Otherwise, it returns an empty list.

    :param serializer: The serializer to be checked.
    :type serializer: object

    :return: A list of dictionaries representing the error types if the serializer is not valid,
             otherwise, an empty list.
    :rtype: list[dict]
    """
    if not serializer.is_valid():
        errors = serializer_error_to_error_types(serializer.errors, serializer.initial_data)
        return [dict(each) for each in errors]
    return []

from typing import Union

import graphene
from django_enumfield import enum
from rest_framework import serializers
from django.db import models
from django.contrib.postgres.fields import ArrayField


def to_camelcase(snake_str):
    """
    Converts a snake case string to camel case.

    Args:
        snake_str (str): The snake case string to be converted.

    Returns:
        str: The converted camel case string.

    Example:
        >>> to_camelcase('hello_world')
        'helloWorld'
        >>> to_camelcase('my_variable_name')
        'myVariableName'
    """
    components = snake_str.split('_')
    return components[0] + "".join(x.title() for x in components[1:])


def enum_description(v: enum.Enum) -> Union[str, None]:
    """
    Get the description for a given enum value.

    Parameters:
        v (enum.Enum): The enum value to get the description for.

    Returns:
        Union[str, None]: The description of the given enum value, or None if there is no description.

    """
    try:
        return v.label
    except AttributeError:
        return None


def convert_enum_to_graphene_enum(enum, name=None, description=enum_description, deprecation_reason=None):
    """
    Converts a Python enum to a Graphene enum.

    Parameters:
        enum (Enum): The Python enum to be converted.
        name (str, optional): The name of the Graphene enum. If not provided, the name of the Python enum will be used.
        description (str, optional): The description of the Graphene enum. If not provided, the docstring of the Python enum will be used.
        deprecation_reason (str, optional): The deprecation reason for the Graphene enum.

    Returns:
        type: The converted Graphene enum.

    Example usage:
        # Define a Python enum
        class MyEnum(Enum):
            VALUE1 = 1
            VALUE2 = 2

        # Convert the Python enum to a Graphene enum
        MyGrapheneEnum = convert_enum_to_graphene_enum(MyEnum)

        # Use the converted Graphene enum in a GraphQL schema
        class MyQuery(graphene.ObjectType):
            my_field = graphene.Field(MyGrapheneEnum)

    Note: This method creates a new type dynamically based on the provided Python enum. It uses the enum's name and docstring as the name and description of the Graphene enum. The Graphene enum will have the same values and attributes as the Python enum.
    """
    description = description or enum.__doc__
    name = name or enum.__name__
    meta_dict = {
        "enum": enum,
        "description": description,
        "deprecation_reason": deprecation_reason,
    }
    meta_class = type("Meta", (object,), meta_dict)
    return type(name, (graphene.Enum,), {"Meta": meta_class})


def get_enum_name_from_django_field(
    field: Union[
        None,
        serializers.ChoiceField,
        models.CharField,
        models.IntegerField,
        ArrayField,
        models.query_utils.DeferredAttribute,
    ],
    field_name=None,
    model_name=None,
):
    """
    Get the enum name from a Django field.

    Args:
        field (Union[None, serializers.ChoiceField, models.CharField, models.IntegerField, ArrayField, models.query_utils.DeferredAttribute]): The Django field.
        field_name (str, optional): The name of the field. Defaults to None.
        model_name (str, optional): The name of the model. Defaults to None.

    Returns:
        str: The enum name.

    Raises:
        Exception: If either the `model_name` or `field_name` is None.

    Notes:
        - The `field` parameter should be one of the valid field types: `serializers.ChoiceField`, `models.CharField`, `models.IntegerField`, `ArrayField`, `models.query_utils.DeferredAttribute`.
        - If `field_name` and `model_name` are not provided, they will be inferred from the `field` parameter.

    Examples:
        # Example usage 1:
        field = serializers.ChoiceField(choices=['A', 'B', 'C'])
        field_name = 'my_field'
        model_name = 'MyModel'
        enum_name = get_enum_name_from_django_field(field, field_name, model_name)
        # enum_name should be 'MyModelMyField'

        # Example usage 2:
        field = models.CharField(max_length=50)
        enum_name = get_enum_name_from_django_field(field)
        # Assume this field is from a model named 'MyModel' and is named 'my_field',
        # enum_name should be 'MyModelMyField'
    """
    if field_name is None and model_name is None:
        if isinstance(field, serializers.ChoiceField):
            if isinstance(field.parent, serializers.ListField):
                model_name = field.parent.parent.Meta.model.__name__
                field_name = field.parent.field_name
            else:
                model_name = field.parent.Meta.model.__name__
                field_name = field.field_name
        elif isinstance(field, ArrayField):
            model_name = field.model.__name__
            field_name = field.base_field.name
        elif type(field) in [models.CharField, models.IntegerField]:
            model_name = field.model.__name__
            field_name = field.name
        elif isinstance(field, models.query_utils.DeferredAttribute):
            model_name = field.field.model.__name__
            field_name = field.field.name
    if model_name is None or field_name is None:
        raise Exception(f'{field=} | {type(field)=}: Both {model_name=} and {field_name=} should have a value')
    return f'{model_name}{to_camelcase(field_name.title())}'


class EnumDescription(graphene.Scalar):
    # NOTE: This is for Field only. Not usable as InputField or Argument.
    # XXX: Maybe there is a better way then this.
    """

    EnumDescription is a class that represents a custom scalar for Graphene.

    NOTE: This class is designed to be used only for fields and is not usable as an input field or argument.

    Methods:
    - coerce_string(value): Coerces the given value to a string. The value should always be a callable representing the function get_FOO_display, where FOO is a field name.
        - Parameters:
            - value: The value to be coerced.
        - Returns: The coerced value as a string.

    Attributes:
    - serialize: A reference to the coerce_string method. This attribute is used for serialization.
    - parse_value: A reference to the coerce_string method. This attribute is used for parsing a value.
    - parse_literal: A reference to the graphene.String.parse_literal method. This attribute is used for parsing a literal.

    """

    @staticmethod
    def coerce_string(value):
        """
        Here value should always be callable get_FOO_display
        """
        if callable(value):
            return value()
        return value

    serialize = coerce_string
    parse_value = coerce_string
    parse_literal = graphene.String.parse_literal

import json
from collections import defaultdict

import graphene
from graphene import ObjectType


class NestedErrorType(ObjectType):
    field = graphene.String(required=True)
    messages = graphene.String(required=True)


class ArrayNestedErrorType(ObjectType):
    key = graphene.String(required=True)
    object_errors = graphene.List(NestedErrorType)


class CustomErrorType(ObjectType):
    field = graphene.String(required=True)
    messages = graphene.String(required=False)
    object_errors = graphene.List(NestedErrorType)
    array_errors = graphene.List(ArrayNestedErrorType)


def mutation_is_not_valid(serializer) -> List:
    """
    Checks if serializer is valid, if not returns list of errorTypes
    """
    if not serializer.is_valid():
        errors = []
        for key, value in serializer.errors.items():
            if isinstance(value, dict):
                object_errors = []
                for k, v in value.items():
                    object_errors.append(
                        NestedErrorType(field=k, messages=''.join(str(msg) for msg in v))
                    )
                errors.append(CustomErrorType(field=key, object_errors=object_errors))
            elif isinstance(value, list) and isinstance(value[0], dict):
                array_errors = []
                position = 0
                for nested_instance in value:
                    position += 1
                    if not nested_instance:
                        # nested instance might not have error
                        continue
                    nested_object_errors = []
                    for k, v in nested_instance.items():
                        nested_object_errors.append(NestedErrorType(
                            field=k,
                            messages=''.join(str(msg) for msg in v)
                        ))
                    array_errors.append(ArrayNestedErrorType(
                        key=position,
                        object_errors=nested_object_errors
                    ))
                errors.append(CustomErrorType(field=key, array_errors=array_errors))
            else:
                messages = ''.join(str(msg) for msg in value)
                errors.append(CustomErrorType(field=key, messages=messages))
        return errors
    return []

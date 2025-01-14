import logging
import inspect
import typing
from functools import partial
from collections import OrderedDict

import graphene
from django.db.models import QuerySet
from django.core.exceptions import FieldError as DjFieldError
from graphene import NonNull
from graphene.types.structures import Structure
from graphene.utils.str_converters import to_snake_case
from graphene_django.utils import maybe_queryset, is_valid_django_model
from graphene_django_extras import DjangoFilterPaginateListField
from graphene_django_extras.base_types import DjangoListObjectBase
from graphene_django_extras.fields import DjangoListField
from graphene_django_extras.filters.filter import get_filterset_class
from graphene_django_extras.paginations.pagination import BaseDjangoGraphqlPagination
from graphene_django_extras.settings import graphql_api_settings
from graphene_django_extras.utils import get_extra_filters
from graphene_django.rest_framework.serializer_converter import get_graphene_type_from_serializer_field
from graphene_django.registry import get_global_registry
from rest_framework import serializers

from utils.graphene.pagination import OrderingOnlyArgumentPagination
from utils.filters import generate_type_for_filter_set
from utils.common import track_gidd
from apps.gidd.filters import GIDD_API_TYPE_MAP


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def path_has_list(info):
    """
    Check if the path contains any numeric values.

    Args:
        info (object): An object containing path information.

    Returns:
        bool: True if the path contains at least one numeric value, False otherwise.
    """
    return bool([each for each in info.path if str(each).isdigit()])


class CustomDjangoListObjectBase(DjangoListObjectBase):
    """
    Constructor for CustomDjangoListObjectBase.

    Args:
        results (list): The list of results.
        count (int): The total count of results.
        page (int): The current page number.
        pageSize (int): The number of results per page.
        results_field_name (str, optional): The name of the results field in the dictionary representation. Defaults to
        "results".
    """
    def __init__(self, results, count, page, pageSize, results_field_name="results"):
        self.results = results
        self.count = count
        self.results_field_name = results_field_name
        self.page = page
        self.pageSize = pageSize

    def to_dict(self):
        return {
            self.results_field_name: [e.to_dict() for e in self.results],
            "count": self.count,
            "page": self.page,
            "pageSize": self.pageSize
        }


class CustomDjangoListField(DjangoListField):
    """

    CustomDjangoListField

    This class extends the DjangoListField and provides additional functionality for resolving lists in
    DjangoObjectType.

    Methods:
    - list_resolver: A static method that resolves the list for a DjangoObjectType. It takes the following parameters:
        - django_object_type: The DjangoObjectType for the list.
        - resolver: The resolver function for the parent field.
        - root: The root object.
        - info: The GraphQLResolveInfo object.
        - args: Additional arguments passed to the resolver.

    - get_resolver: Overrides the get_resolver method of DjangoListField. It returns a partial function that calls the
    list_resolver method with the appropriate arguments.

    """
    @staticmethod
    def list_resolver(
            django_object_type, resolver, root, info, **args
    ):
        queryset = maybe_queryset(resolver(root, info, **args))
        if queryset is None:
            queryset = QuerySet.none()

        if isinstance(queryset, QuerySet):
            if hasattr(django_object_type, 'get_queryset'):
                # Pass queryset to the DjangoObjectType get_queryset method
                queryset = maybe_queryset(django_object_type.get_queryset(queryset, info))
        return queryset

    def get_resolver(self, parent_resolver):
        _type = self.type
        if isinstance(_type, NonNull):
            _type = _type.of_type
        object_type = _type.of_type.of_type
        return partial(
            self.list_resolver,
            object_type,
            parent_resolver,
        )


class CustomPaginatedListObjectField(DjangoFilterPaginateListField):
    """
    CustomPaginatedListObjectField

    A class that extends DjangoFilterPaginateListField and provides additional functionality for paginated lists of
    objects.

    Parameters:
        _type: The GraphQLObjectType to use for the list items.
        pagination: (optional) The pagination type to use for the list. If not provided, OrderingOnlyArgumentPagination
        will be used.
        extra_filter_meta: (optional) Additional meta data for the filterset class.
        filterset_class: (optional) The filterset class to use for filtering the queryset.
        *args: Additional positional arguments to pass to the parent class.
        **kwargs: Additional keyword arguments to pass to the parent class.

    Methods:
        list_resolver: Resolves the list of objects based on the provided filterset class, filtering args, root, info
        and kwargs.
            Parameters:
                filterset_class: The filterset class to use for filtering the queryset.
                filtering_args: The filtering arguments for the filterset class.
                root: The root of the GraphQL query.
                info: The GraphQL ResolveInfo object.
                **kwargs: Additional keyword arguments passed to the resolver.
            Returns:
                A CustomDjangoListObjectBase instance containing the filtered and paginated results.

        get_resolver: Overrides the parent method to return a partial function of the list_resolver with the filterset
        class and filtering args as arguments.

    Note: This class assumes the use of DjangoFilterPaginateListField and its dependencies.
    """
    def __init__(
        self,
        _type,
        pagination=None,
        extra_filter_meta=None,
        filterset_class=None,
        *args,
        **kwargs,
    ):

        kwargs.setdefault("args", {})

        # -- NOTE: This doesn't uses nested filters args
        # Currently arguments aren't used for this
        filterset_class = filterset_class or _type._meta.filterset_class
        self.filterset_class = get_filterset_class(filterset_class)
        self.filtering_args = get_filtering_args_from_non_model_filterset(
            self.filterset_class
        )
        # -- NOTE: This doesn't uses nested filters args
        kwargs["args"].update(self.filtering_args)

        pagination = pagination or OrderingOnlyArgumentPagination()

        if pagination is not None:
            assert isinstance(pagination, BaseDjangoGraphqlPagination), (
                'You need to pass a valid DjangoGraphqlPagination in DjangoFilterPaginateListField, received "{}".'
            ).format(pagination)

            pagination_kwargs = pagination.to_graphql_fields()

            self.pagination = pagination
            kwargs.update(**pagination_kwargs)

        self.accessor = kwargs.pop('accessor', None)
        super(DjangoFilterPaginateListField, self).__init__(
            _type, *args, **kwargs
        )

    def list_resolver(
        self, filterset_class, filtering_args, root, info, **kwargs
    ):

        filter_kwargs = {k: v for k, v in kwargs.items() if k in filtering_args}
        qs = getattr(root, self.accessor)
        if hasattr(qs, 'all'):
            qs = qs.all()
        qs = filterset_class(data=filter_kwargs, queryset=qs, request=info.context.request).qs
        count = qs.count()

        if getattr(self, "pagination", None):
            ordering = kwargs.pop(self.pagination.ordering_param, None) or self.pagination.ordering
            ordering = ','.join([to_snake_case(each) for each in ordering.strip(',').replace(' ', '').split(',')])
            kwargs[self.pagination.ordering_param] = ordering
            qs = self.pagination.paginate_queryset(qs, **kwargs)

        return CustomDjangoListObjectBase(
            count=count,
            results=maybe_queryset(qs),
            results_field_name=self.type._meta.results_field_name,
            page=kwargs.get('page', 1) if hasattr(self.pagination, 'page') else None,
            pageSize=kwargs.get(
                'pageSize',
                graphql_api_settings.DEFAULT_PAGE_SIZE
            ) if hasattr(self.pagination, 'page') else None
        )

    def get_resolver(self, parent_resolver):
        current_type = self.type
        while isinstance(current_type, Structure):
            current_type = current_type.of_type
        return partial(
            self.list_resolver,
            self.filterset_class,
            self.filtering_args,
        )


class DjangoPaginatedListObjectField(DjangoFilterPaginateListField):
    """
    DjangoPaginatedListObjectField class is a subclass of DjangoFilterPaginateListField. It is used to create a
    paginated list of objects with filtering capabilities.

    Parameters:
    - _type: The GraphQL object type of the objects in the list.
    - pagination: An optional pagination configuration for the list. If None, only ordering fields will be allowed.
    - fields: An optional list of fields to include in the object type.
    - extra_filter_meta: An optional dictionary for extra filter metadata.
    - filterset_class: An optional filterset class for filtering the queryset.

    Attributes:
    - filtering_args: A dictionary containing the filtering arguments for the GraphQL field.
    - pagination: The pagination configuration for the list.
    - accessor: An optional accessor for custom querysets.
    - related_name: An optional related name for relationships spanning multiple fields.
    - reverse_related_name: An optional reverse related name for relationships spanning multiple fields.

    Methods:
    - list_resolver: The resolver function for the list field. It fetches the objects from the queryset and applies
    filtering and pagination.
    """
    def __init__(
        self,
        _type,
        pagination=None,
        fields=None,
        extra_filter_meta=None,
        filterset_class=None,
        *args,
        **kwargs,
    ):
        '''
        If pagination is None, then we will only allow Ordering fields.
            - The page size will respect the settings.
            - Client will not be able to add pagination params
        '''
        _fields = _type._meta.filter_fields
        if _fields:
            raise Exception(f'filter_fields are ignored: Provided: {_fields} <> {_type}')

        kwargs.setdefault("args", {})

        self.filterset_class = filterset_class or _type._meta.filterset_class
        if self.filterset_class:
            _, filterset_type = generate_type_for_filter_set(
                self.filterset_class,
                _type,
                f"{self.filterset_class.__name__.replace('Filter', '')}FilterDataType",
                f"{self.filterset_class.__name__.replace('Filter', '')}FilterDataInputType",
            )
            self.filtering_args = {
                "filters": filterset_type(required=False),
            }
        else:
            self.filtering_args = {}
        kwargs["args"].update(self.filtering_args)

        pagination = pagination or OrderingOnlyArgumentPagination()

        if pagination is not None:
            assert isinstance(pagination, BaseDjangoGraphqlPagination), (
                'You need to pass a valid DjangoGraphqlPagination in DjangoFilterPaginateListField, received "{}".'
            ).format(pagination)

            pagination_kwargs = pagination.to_graphql_fields()

            self.pagination = pagination
            kwargs.update(**pagination_kwargs)

        if not kwargs.get("description", None):
            kwargs["description"] = "{} list".format(_type._meta.model.__name__)

        # accessor will be used with custom querysets
        self.accessor = kwargs.pop('accessor', None)
        # related_names will be used especially for fkeys and m2ms with
        # relationships spanning across more than one fields
        self.related_name = kwargs.pop('related_name', None)
        self.reverse_related_name = kwargs.pop('reverse_related_name', None)

        super(DjangoFilterPaginateListField, self).__init__(
            _type, *args, **kwargs
        )

    def list_resolver(
        self, manager, filterset_class, filtering_args, root, info, **kwargs
    ):
        filter_kwargs = kwargs.get('filters', {})

        client_id = kwargs.get('client_id')
        if client_id:
            api_type = GIDD_API_TYPE_MAP.get(filterset_class.__name__)
            if api_type is None:
                logger.error(f'Client tracking key was not found for filter {filterset_class.__name__}')
            track_gidd(client_id, api_type)

        # setup pagination
        if getattr(self, "pagination", None):
            ordering = kwargs.pop(self.pagination.ordering_param, None) or self.pagination.ordering
            ordering = ','.join([to_snake_case(each) for each in ordering.strip(',').replace(' ', '').split(',')])
            kwargs[self.pagination.ordering_param] = ordering

        if root and path_has_list(info):
            if not getattr(self, 'related_name', None):
                raise NotImplementedError(f'Dataloader error: fetching without dataloader. {info.path}')
            parent_class = root._meta.model
            child_class = manager.model
            # TODO: qs should be executed only when we access the results node in the future
            qs = info.context.get_dataloader(
                parent_class.__name__,
                self.related_name,
            ).load(
                root.id,
                parent=parent_class,
                child=child_class,
                accessor=self.accessor,
                related_name=self.related_name,
                reverse_related_name=self.reverse_related_name,
                pagination=self.pagination,
                filterset_class=filterset_class,
                filter_kwargs=filter_kwargs,
                request=info.context.request,
                **kwargs,
            )
            count = info.context.get_count_loader(
                parent_class.__name__,
                child_class.__name__,
            ).load(
                root.id,
                parent=parent_class,
                child=child_class,
                accessor=self.accessor,
                related_name=self.related_name,
                reverse_related_name=self.reverse_related_name,
                pagination=self.pagination,
                filterset_class=filterset_class,
                filter_kwargs=filter_kwargs,
                request=info.context.request,
                **kwargs,
            )
        else:
            accessor = self.accessor or self.related_name
            if accessor:
                qs = getattr(root, accessor, None)
                if hasattr(qs, 'all'):
                    qs = qs.all()
            else:
                qs = self.get_queryset(manager, info, **kwargs)
            qs = filterset_class(data=filter_kwargs, queryset=qs, request=info.context.request).qs
            if root and not accessor and is_valid_django_model(root._meta.model):
                extra_filters = get_extra_filters(root, manager.model)
                if len(list(extra_filters.keys())) == 1:
                    # NOTE: multiple field filters are returned when
                    # root and child are related in multiple ways
                    qs = qs.filter(**extra_filters)
            try:
                # XXX: Experimental: Try to use 'id' to minimize joins in SQL Query
                count = qs.values('id').count()
            except DjFieldError:
                # Fallback to normal count
                count = qs.count()

            qs = self.pagination.paginate_queryset(
                qs,
                **kwargs
            )

        return CustomDjangoListObjectBase(
            results=qs,
            count=count,
            results_field_name=self.type._meta.results_field_name,
            page=kwargs.get('page', 1) if hasattr(self.pagination, 'page_query_param') else None,
            pageSize=kwargs.get(
                'pageSize',
                graphql_api_settings.DEFAULT_PAGE_SIZE
            ) if hasattr(self.pagination, 'page_size_query_param') else None
        )


def get_filtering_args_from_non_model_filterset(filterset_class):
    """

    Get filtering arguments from a non-model filterset class.

    Parameters:
    - filterset_class (class): The non-model filterset class from which to extract filtering arguments.

    Returns:
    - args (dict): A dictionary of filtering arguments, where the key is the name of the argument and the value is the
    corresponding graphene argument type.

    """
    from graphene_django.forms.converter import convert_form_field

    args = {}
    for name, filter_field in filterset_class.declared_filters.items():
        form_field = filter_field.field
        field_type = convert_form_field(form_field).Argument()
        field_type.description = filter_field.label
        args[name] = field_type
    return args


def generate_serializer_field_class(inner_type, serializer_field, non_null=False):
    """

    Args:
        inner_type (type): The inner type of the serializer field class.
        serializer_field (type): The base class of the serializer field.
        non_null (bool, optional): Whether the field should be non-null or not. Defaults to False.

    Returns:
        type: The newly generated serializer field class.

    """
    new_serializer_field = type(
        "{}SerializerField".format(inner_type.__name__),
        (serializer_field,),
        {},
    )
    get_graphene_type_from_serializer_field.register(new_serializer_field)(
        lambda _: graphene.NonNull(inner_type) if non_null else inner_type
    )
    return new_serializer_field


# Only use this for single object type with direct scaler access.
def generate_object_field_from_input_type(input_type, skip_fields=[]):
    """
    Generates a new map of fields for an input type object.

    Args:
        input_type (InputObjectType): The input type object.
        skip_fields (list, optional): List of fields to skip. Defaults to [].

    Returns:
        dict: A new map of fields for the input type object.

    """
    new_fields_map = {}
    for field_key, field in input_type._meta.fields.items():
        if field_key in skip_fields:
            continue
        _type = field.type
        if inspect.isclass(_type) and (
            issubclass(_type, graphene.Scalar) or
            issubclass(_type, graphene.Enum)
        ):
            new_fields_map[field_key] = graphene.Field(_type)
        else:
            new_fields_map[field_key] = _type
    return new_fields_map


# use this for input type with direct scaler fields only.
def generate_simple_object_type_from_input_type(input_type):
    """Generate a simple object type from an input type.

    Parameters:
    - input_type: The input type to generate the object type from.

    Returns:
    - The newly generated object type.

    """
    new_fields_map = generate_object_field_from_input_type(input_type)
    return type(input_type._meta.name.replace('Input', ''), (graphene.ObjectType,), new_fields_map)


def compare_input_output_type_fields(input_type, output_type):
    """
    Compares the fields between the input type and the output type.

    Args:
        input_type (Type): The input type to compare.
        output_type (Type): The output type to compare against.

    Raises:
        Exception: If the number of fields in output_type differs from the number of fields in input_type.

    Returns:
        None

    """
    if len(output_type._meta.fields) != len(input_type._meta.fields):
        for field in input_type._meta.fields.keys():
            if field not in output_type._meta.fields.keys():
                print('---> [Entry] Missing: ', field)
        raise Exception('Conversion failed')


def convert_serializer_field(field, convert_choices_to_enum=True, force_optional=False):
    """
    Convert a Django REST Framework serializer field into a corresponding GraphQL field.

    Parameters:
    - field (Field): The Django REST Framework serializer field to convert.
    - convert_choices_to_enum (bool): Whether to convert ChoiceField to Enum type (default: True).
    - force_optional (bool): Whether to force the field to be optional (default: False).

    Returns:
    - The corresponding GraphQL field.

    """

    if isinstance(field, serializers.ChoiceField) and not convert_choices_to_enum:
        graphql_type = graphene.String
    # elif isinstance(field, serializers.FileField):
    #     graphql_type = Upload
    else:
        graphql_type = get_graphene_type_from_serializer_field(field)

    args = []
    kwargs = {
        "description": field.help_text,
        "required": field.required and not force_optional
    }

    # if it is a tuple or a list it means that we are returning
    # the graphql type and the child type
    if isinstance(graphql_type, (list, tuple)):
        kwargs["of_type"] = graphql_type[1]
        graphql_type = graphql_type[0]

    if isinstance(field, serializers.ModelSerializer):
        global_registry = get_global_registry()
        field_model = field.Meta.model
        args = [global_registry.get_type_for_model(field_model)]
    elif isinstance(field, serializers.Serializer):
        args = [convert_serializer_to_type(field.__class__)]
    elif isinstance(field, serializers.ListSerializer):
        field = field.child
        if isinstance(field, serializers.ModelSerializer):
            del kwargs["of_type"]
            global_registry = get_global_registry()
            field_model = field.Meta.model
            args = [global_registry.get_type_for_model(field_model)]
        elif isinstance(field, serializers.Serializer):
            kwargs["of_type"] = graphene.NonNull(convert_serializer_to_type(field.__class__))
    return graphql_type(*args, **kwargs)


def convert_serializer_to_type(serializer_class):
    """
    Converts a Django REST Framework serializer class to a GraphQL type class.

    :param serializer_class: The serializer class to convert.
    :type serializer_class: class

    :return: The converted GraphQL type class.
    :rtype: class

    """
    cached_type = convert_serializer_to_type.cache.get(
        serializer_class.__name__, None
    )
    if cached_type:
        return cached_type
    serializer = serializer_class()

    items = {
        name: convert_serializer_field(field)
        for name, field in serializer.fields.items()
    }
    # Alter naming
    serializer_name = serializer.__class__.__name__
    serializer_name = ''.join(''.join(serializer_name.split('ModelSerializer')).split('Serializer'))
    ref_name = f'{serializer_name}Type'

    base_classes = (graphene.ObjectType,)

    ret_type = type(
        ref_name,
        base_classes,
        items,
    )
    convert_serializer_to_type.cache[serializer_class.__name__] = ret_type
    return ret_type


convert_serializer_to_type.cache = {}


def fields_for_serializer(
    serializer,
    only_fields,
    exclude_fields,
    convert_choices_to_enum=True,
    partial=False,
):
    """
    Generate a dictionary of fields to be used in a serializer.

    Parameters:
    - serializer: The serializer object to generate fields from.
    - only_fields (list): A list of field names to include in the generated fields. If provided, only these fields will
    be included. Default is an empty list.
    - exclude_fields (list): A list of field names to exclude from the generated fields. If provided, these fields will
    be skipped. Default is an empty list.
    - convert_choices_to_enum (bool): Indicates whether serializer field choices should be converted to enums. Set to
    True to convert choices to enum values. Default is True.
    - partial (bool): Indicates whether the serializer is used for partial updates. Set to True if the serializer is
    used for partial updates. Default is False.

    Returns:
    - fields (OrderedDict): A dictionary of fields generated from the provided serializer. The keys are field names, and
    the values are the converted serializer fields.

    Example usage:
        serializer_class = MySerializer
        only_fields = ["field1", "field2"]
        exclude_fields = ["field3"]
        fields = fields_for_serializer(serializer_class, only_fields, exclude_fields)
    """
    fields = OrderedDict()
    for name, field in serializer.fields.items():
        is_not_in_only = only_fields and name not in only_fields
        is_excluded = name in exclude_fields
        if is_not_in_only or is_excluded:
            continue
        fields[name] = convert_serializer_field(
            field,
            convert_choices_to_enum=convert_choices_to_enum,
            force_optional=partial,
        )
    return fields


def generate_type_for_serializer(
    name: str,
    serializer_class,
    partial=False,
    update_cache=False,
) -> typing.Type[graphene.ObjectType]:
    """
    Generate a type for a serializer.

    Parameters:
    - name (str): The name of the type.
    - serializer_class: The serializer class.
    - partial (bool, optional): Whether to generate a partial type or not. Defaults to False.
    - update_cache (bool, optional): Whether to update the type cache or not. Defaults to False.

    Returns:
    typing.Type[graphene.ObjectType]: The generated type.

    Raises:
    Exception: If a type with the same name already exists in the cache.

    Note:
    Custom converters are defined in a mutation, which need to be set first.
    """
    # NOTE: Custom converter are defined in mutation which needs to be set first.
    import utils.mutation  # noqa:F401

    data_members = fields_for_serializer(
        serializer_class(),
        only_fields=[],
        exclude_fields=[],
        partial=partial,
    )
    _type = type(name, (graphene.ObjectType,), data_members)
    if update_cache:
        if name in convert_serializer_to_type.cache:
            raise Exception(f'<{name}> : <{serializer_class.__name__}> Alreay exists')
        convert_serializer_to_type.cache[serializer_class.__name__] = _type
    return _type

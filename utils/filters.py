import typing
import graphene
import django_filters
from functools import partial
from django import forms
from django.db.models.functions import Lower, StrIndex
from django.db.models import Value
from django.db.models.query import QuerySet
from graphene.types.generic import GenericScalar
from graphene_django.forms.converter import convert_form_field
from graphene_django.filter.utils import get_filtering_args_from_filterset

from utils.mutation import generate_object_field_from_input_type, compare_input_output_type_fields


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    """
    Class NumberInFilter

    A custom Django filter that allows filtering based on a list of number values.

    Inherits:
        - django_filters.BaseInFilter
        - django_filters.NumberFilter

    Attributes:
        - field_class (forms.IntegerField): The field class to be used for the filter.

    """
    field_class = forms.IntegerField


class DjangoFilterCSVWidget(django_filters.widgets.CSVWidget):
    """

    DjangoFilterCSVWidget

    A class that inherits from the 'CSVWidget' class of the 'django_filters.widgets' module in Django.

    Methods:
    - value_from_datadict(data, files, name)
        Returns a processed value from the given data dictionary, files dictionary, and name.

    """
    def value_from_datadict(self, data, files, name):
        value = forms.Widget.value_from_datadict(self, data, files, name)

        if value is not None:
            if value == '':  # parse empty value as an empty list
                return []
            # if value is already list(by POST)
            elif isinstance(value, list) or isinstance(value, QuerySet):
                return value
            elif isinstance(value, str):
                return [x.strip() for x in value.strip().split(',') if x.strip()]
            raise Exception(f'Unknown value type {type(value)}')
        return None


def _generate_filter_class(inner_type, filter_type=None, non_null=False):
    """

    Generate a filter class for a given inner type and optional filter type.

    Parameters:
    - inner_type: The inner type of the filter class.
    - filter_type: The filter type to be used. If not specified, default to django_filters.Filter.
    - non_null: Whether the filter class should be non-null. Default is False.

    Returns:
    - The generated filter class.

    The _generate_filter_class method creates a filter class for the specified inner type. It uses the filter_type
    parameter to determine the type of filter to be used. If filter_type is not provided, it defaults to
    django_filters.Filter.

    The method creates a form_field for the filter class, which is a type derived from the field_class of the filter
    type. The form_field is used to define the field class for the filter class. The field class is generated as
    "{}FormField" where "{}" is the name of the inner_type.

    The filter class itself is created using the inner_type, filter_type, and form_field. It extends the filter_type and
    sets the field_class to the defined form_field. The __doc__ attribute of the filter class is set to a formatted
    string that describes the purpose of the filter class.

    Finally, the form_field is registered in convert_form_field, which is a registration mechanism for converting form
    fields to graphene types. If non_null is True, the inner_type is wrapped in graphene.NonNull. Otherwise, the
    inner_type is used as is.

    Note that the generated filter class is not returned as a string, but as a Python class object.

    """
    _filter_type = filter_type or django_filters.Filter
    form_field = type(
        "{}FormField".format(inner_type.__name__),
        (_filter_type.field_class,),
        {},
    )
    filter_class = type(
        "{}Filter".format(inner_type.__name__),
        (_filter_type,),
        {
            "field_class": form_field,
            "__doc__": (
                "{0}Filter is a small extension of a raw {1} "
                "that allows us to express graphql ({0}) arguments using FilterSets."
                "Note that the given values are passed directly into queryset filters."
            ).format(inner_type.__name__, _filter_type),
        },
    )
    convert_form_field.register(form_field)(
        lambda _: graphene.NonNull(inner_type) if non_null else inner_type()
    )

    return filter_class


def _generate_list_filter_class(inner_type, filter_type=None, field_class=None):
    """
    Generates a list filter class for filtering List({inner_type}) arguments using FilterSets.

    :param inner_type: The type used in the list filter.
    :param filter_type: (optional) The type of filter to use. Defaults to django_filters.Filter.
    :param field_class: (optional) The field class to use. Defaults to the field class of the filter type.

    :return: The generated list filter class.

    The generated list filter class is a small extension of the raw filter_type that allows expressing graphql
    List({inner_type}) arguments using FilterSets. The given values are passed directly into queryset filters.
    """

    _filter_type = filter_type or django_filters.Filter
    _field_class = field_class or _filter_type.field_class
    form_field = type(
        "List{}FormField".format(inner_type.__name__),
        (_field_class,),
        {},
    )
    filter_class = type(
        "{}ListFilter".format(inner_type.__name__),
        (_filter_type,),
        {
            "field_class": form_field,
            "__doc__": (
                "{0}ListFilter is a small extension of a raw {1} "
                "that allows us to express graphql List({0}) arguments using FilterSets."
                "Note that the given values are passed directly into queryset filters."
            ).format(inner_type.__name__, _filter_type),
        },
    )
    convert_form_field.register(form_field)(
        lambda _: graphene.List(graphene.NonNull(inner_type))
    )

    return filter_class


def _get_simple_input_filter(_type, **kwargs):
    """
    Return an instance of a filter class based on the given type.

    :param _type: The type of the filter.
    :type _type: str
    :param kwargs: Additional keyword arguments to initialize the filter.
    :type kwargs: dict
    :return: An instance of the filter class based on the given type.
    :rtype: object
    """
    return _generate_filter_class(_type)(**kwargs)


def _get_multiple_input_filter(_type, **kwargs):
    """

    Method: _get_multiple_input_filter

    Description:
    This method generates a filter class object for multiple choice filter type. It is a helper method used within the
    codebase.

    Parameters:
    - _type: The type of filter.
    - **kwargs: Additional keyword arguments for the filter class.

    Returns:
    A filter class object for the given multiple choice filter type.

    Example Usage:
    _filter = _get_multiple_input_filter(_type='my_filter', name='my_filter', lookup_expr='exact')

    """
    return _generate_list_filter_class(
        _type,
        filter_type=django_filters.MultipleChoiceFilter,
        # TODO: Hack, not sure why django_filters.MultipleChoiceFilter.field_class doesn't work
        field_class=django_filters.Filter.field_class,
    )(**kwargs)


def generate_type_for_filter_set(
    filter_set,
    used_node,
    type_name,
    input_type_name,
    custom_new_fields_map=None,
) -> typing.Tuple[graphene.ObjectType, graphene.InputObjectType]:
    """

    generate_type_for_filter_set(filter_set, used_node, type_name, input_type_name, custom_new_fields_map=None) ->
    typing.Tuple[graphene.ObjectType, graphene.InputObjectType]

    Generates a GraphQL type for a given filter set.

    Parameters:
    - filter_set (FilterSet): The filter set for which the GraphQL type is being generated.
    - used_node (Node): The node used to fetch the filter set.
    - type_name (str): The name of the generated GraphQL type.
    - input_type_name (str): The name of the generated GraphQL input type.
    - custom_new_fields_map (dict, optional): A custom dictionary mapping new fields to be added to the generated
    GraphQL type. Default is None.

    Returns:
    - typing.Tuple[graphene.ObjectType, graphene.InputObjectType]: A tuple containing the generated GraphQL type and
    input type.

    Note:
    - If the given filter set already exists in the cache, the cached types are returned.

     """
    if filter_set in generate_type_for_filter_set.cache:
        return generate_type_for_filter_set.cache[filter_set]

    def generate_type_from_input_type(input_type):
        new_fields_map = generate_object_field_from_input_type(input_type)
        if custom_new_fields_map:
            new_fields_map.update(custom_new_fields_map)
        new_type = type(type_name, (graphene.ObjectType,), new_fields_map)
        compare_input_output_type_fields(input_type, new_type)
        return new_type

    input_type = type(
        input_type_name,
        (graphene.InputObjectType,),
        get_filtering_args_from_filterset(filter_set, used_node)
    )
    _type = generate_type_from_input_type(input_type)
    generate_type_for_filter_set.cache[filter_set] = (_type, input_type)
    return _type, input_type


generate_type_for_filter_set.cache = {}

SimpleInputFilter = _get_simple_input_filter
MultipleInputFilter = _get_multiple_input_filter

IDFilter = _generate_filter_class(
    graphene.ID,
    filter_type=django_filters.NumberFilter,
)

# Generic Filters
IDListFilter = _generate_list_filter_class(graphene.ID)

StringListFilter: MultipleInputFilter = _generate_list_filter_class(graphene.String)
GenericFilter = _generate_filter_class(GenericScalar)

DateTimeFilter = partial(
    django_filters.DateTimeFilter,
    input_formats=[django_filters.fields.IsoDateTimeField.ISO_8601],
)
DateTimeGteFilter = partial(
    django_filters.DateTimeFilter,
    lookup_expr='gte',
    input_formats=[django_filters.fields.IsoDateTimeField.ISO_8601],
)
DateTimeLteFilter = partial(
    django_filters.DateTimeFilter,
    lookup_expr='lte',
    input_formats=[django_filters.fields.IsoDateTimeField.ISO_8601],
)

DateGteFilter = partial(django_filters.DateFilter, lookup_expr='gte')
DateLteFilter = partial(django_filters.DateFilter, lookup_expr='lte')


class NameFilterMixin:
    """

    Class NameFilterMixin

    Mixin class that provides a name filter for Django filters.

    Attributes:
    - None

    Methods:
    - _filter_name: Filters the queryset based on the given name value.

    """
    # NOTE: add a `name` django_filter as follows in the child filters
    # name = django_filters.CharFilter(method='_filter_name')

    def _filter_name(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.annotate(
            lname=Lower('name')
        ).annotate(
            idx=StrIndex('lname', Value(value.lower()))
        ).filter(idx__gt=0).order_by('idx', 'name')

from django_filters import rest_framework as df
from apps.entry.models import (
    OSMName,
    DisaggregatedAge,
    Figure,
    FigureTag,
)


class OSMNameFilter(df.FilterSet):
    """
    Class: OSMNameFilter

    Inherits From: df.FilterSet

    Description:
    This class is used to create a filter set for the OSMName model.

    Attributes:
    - model: The model class being filtered (OSMName).
    - fields: The fields used for filtering (['country']).

    Usage Example:
    filter = OSMNameFilter(data=query_params, queryset=queryset)
    filtered_queryset = filter.qs
    """
    class Meta:
        model = OSMName
        fields = ['country']


class DisaggregatedAgeFilter(df.FilterSet):
    """
    Class: DisaggregatedAgeFilter

    This class is a subclass of FilterSet. It provides a custom filter for the DisaggregatedAge model.

    Fields:
    - sex (list): Filter options for the 'sex' field of the DisaggregatedAge model. The filter uses the 'in' operator.

    Usage Example:
        filter_params = {'sex': ['male', 'female']}
        filter = DisaggregatedAgeFilter(filter_params)
        queryset = filter.qs

    """
    class Meta:
        model = DisaggregatedAge
        fields = {
            'sex': ['in'],
        }


class FigureFilter(df.FilterSet):
    """

    Class: FigureFilter

    Subclass of: df.FilterSet

    Description:
    This class is a filter set used for filtering Figure objects based on certain criteria.

    Attributes:
    - model (class): The model class that this filter set is associated with (Figure).
    - fields (dict): A dictionary representing the filtering fields and their corresponding lookup types.

    """
    class Meta:
        model = Figure
        fields = {
            'unit': ('exact',),
            'start_date': ('lte', 'gte'),
        }


class FigureTagFilter(df.FilterSet):
    """

    FigureTagFilter is a subclass of df.FilterSet and is used for filtering FigureTag model objects.

    Attributes:
        model (class): The model class that this filter is based on.
        fields (dict): A dictionary that specifies the filter fields for this filter.

    """
    class Meta:
        model = FigureTag
        fields = {
            'name': ('unaccent__icontains',),
        }

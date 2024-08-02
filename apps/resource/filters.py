import django_filters as df

from apps.resource.models import Resource, ResourceGroup
from utils.filters import StringListFilter


class ResourceFilter(df.FilterSet):
    """

    Module: resource_filter.py

    This module contains the class `ResourceFilter`, which is a subclass of `df.FilterSet` and is used for filtering
    resources.

    """
    countries = StringListFilter(method='filter_countries')

    class Meta:
        model = Resource
        fields = {
            'name': ['unaccent__icontains']
        }

    @property
    def qs(self):
        if self.request.user.is_authenticated:
            return super().qs.filter(created_by=self.request.user)
        return Resource.objects.none()

    def filter_countries(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(countries__in=value).distinct()


class ResourceGroupFilter(df.FilterSet):
    """

    This class represents a filter for ResourceGroup objects. It is a subclass of df.FilterSet and includes a Meta class
    that specifies the model and fields to filter on.

    Usage:
        To use this filter, create an instance of the ResourceGroupFilter class and pass the request object as an
        argument. Then access the 'qs' property to retrieve the filtered queryset.

    Attributes:
        - model: The model class that this filter is applied to (ResourceGroup).
        - fields: A dictionary that specifies the fields to filter on and the lookup methods to use for each field.

    Methods:
        - qs: This property returns the filtered queryset. If the user is authenticated, it applies an additional filter
        to only include ResourceGroup objects created by the logged-in user. If the user is not authenticated, it
        returns an empty queryset.

    Example:

        filter = ResourceGroupFilter(request)
        queryset = filter.qs

    """
    class Meta:
        model = ResourceGroup
        fields = {
            'name': ['unaccent__icontains']
        }

    @property
    def qs(self):
        if self.request.user.is_authenticated:
            return super().qs.filter(created_by=self.request.user)
        return ResourceGroup.objects.none()

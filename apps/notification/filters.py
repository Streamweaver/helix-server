from django_filters import rest_framework as df
from utils.filters import IDListFilter, StringListFilter
from apps.notification.models import Notification


class NotificationFilter(df.FilterSet):
    """

    Class: NotificationFilter

    This class is a subclass of df.FilterSet and it provides custom filtering capabilities for the Notification model.

    Attributes:
    - events: An instance of IDListFilter class with method set to 'filter_events'. This filter is used to filter the notifications based on the events they are associated with.
    - figures: An instance of IDListFilter class with method set to 'filter_figures'. This filter is used to filter the notifications based on the figures they are associated with.
    - types: An instance of StringListFilter class with method set to 'filter_types'. This filter is used to filter the notifications based on their types.
    - created_at_after: An instance of DateFilter class with method set to 'filter_created_at_after'. This filter is used to filter the notifications created after a specific date.
    - created_at_before: An instance of DateFilter class with method set to 'filter_created_at_before'. This filter is used to filter the notifications created before a specific date.

    Methods:
    - filter_events(qs, name, value): This method filters the queryset based on the events associated with the notifications. If the value is empty, the queryset is returned as is. Otherwise, the queryset is filtered to include only the notifications with events in the given list of values.
    - filter_figures(qs, name, value): This method filters the queryset based on the figures associated with the notifications. If the value is empty, the queryset is returned as is. Otherwise, the queryset is filtered to include only the notifications with figures in the given list of values.
    - filter_types(qs, name, value): This method filters the queryset based on the types of the notifications. If the value is empty, the queryset is returned as is. If the first element of the value list is an integer, the queryset is filtered to include only the notifications with types in the given list of values. Otherwise, the queryset is filtered to include only the notifications with types corresponding to the string values in the given list.
    - filter_created_at_after(qs, name, value): This method filters the queryset based on the creation date of the notifications. If the value is not empty, the queryset is filtered to include only the notifications created on or after the given date. Otherwise, the queryset is returned as is.
    - filter_created_at_before(qs, name, value): This method filters the queryset based on the creation date of the notifications. If the value is not empty, the queryset is filtered to include only the notifications created on or before the given date. Otherwise, the queryset is returned as is.

    Nested Class:
    - Meta: This nested class specifies the model and fields to be used for the filtering. The model is set to Notification and the fields are set to 'recipient' and 'is_read'.

    """
    events = IDListFilter(method='filter_events')
    figures = IDListFilter(method='filter_figures')
    types = StringListFilter(method='filter_types')
    created_at_after = df.DateFilter(method='filter_created_at_after')
    created_at_before = df.DateFilter(method='filter_created_at_before')

    def filter_events(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(event__in=value)

    def filter_figures(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(figure__in=value)

    def filter_types(self, qs, name, value):
        if not value:
            return qs
        if isinstance(value[0], int):
            return qs.filter(type_in=value).distinct()
        return qs.filter(
            type__in=[
                Notification.Type.get(item).value for item in value
            ]
        )

    def filter_created_at_after(self, qs, name, value):
        if value:
            return qs.filter(created_at__gte=value)
        return qs

    def filter_created_at_before(self, qs, name, value):
        if value:
            return qs.filter(created_at__lte=value)
        return qs

    class Meta:
        model = Notification
        fields = {
            'recipient': ['exact', ],
            'is_read': ['exact', ],
        }

from django_filters import rest_framework as df

from apps.parking_lot.models import ParkedItem
from utils.filters import StringListFilter


class ParkingLotFilter(df.FilterSet):
    """
    ParkingLotFilter

    Subclass of df.FilterSet used to filter parking lot items.

    Attributes:
        status_in (StringListFilter): Filter for selecting items with specific statuses.
        assigned_to_in (StringListFilter): Filter for selecting items assigned to specific users.

    Methods:
        filter_status_in: Method for filtering items based on status.
        filter_assigned_to: Method for filtering items based on assigned user.
        qs: Property that returns the filtered queryset.

    Example Usage:
        filter = ParkingLotFilter(data=request.GET, queryset=items)
        queryset = filter.qs
    """
    status_in = StringListFilter(method='filter_status_in')
    # assigned_to_in = StringListFilter(field_name='assigned_to', lookup_expr='in')
    assigned_to_in = StringListFilter(method='filter_assigned_to')

    class Meta:
        model = ParkedItem
        fields = {
            'title': ['unaccent__icontains'],
            'created_by': ['exact'],
        }

    def filter_status_in(self, queryset, name, value):
        if value:
            # map enum names to values
            return queryset.filter(status__in=[ParkedItem.PARKING_LOT_STATUS.get(each)
                                               for each in value])
        return queryset

    def filter_assigned_to(self, queryset, name, value):
        if value:
            return queryset.filter(assigned_to__in=value)
        return queryset

    @property
    def qs(self):
        return super().qs.distinct()

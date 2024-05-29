import django_filters
from django.db.models import Q

from utils.filters import StringListFilter, MultipleInputFilter, generate_type_for_filter_set
from apps.contrib.models import ExcelDownload, ClientTrackInfo, Client, BulkApiOperation
from apps.entry.models import ExternalApiDump
from apps.users.roles import USER_ROLE

from .enums import BulkApiOperationActionEnum, BulkApiOperationStatusEnum


class ExcelExportFilter(django_filters.FilterSet):
    """
    FilterSet for exporting data to Excel.

    This class extends the `django_filters.FilterSet` class and provides additional filtering options for exporting data to Excel.

    Attributes:
        status_list (StringListFilter): Filter for status list.

    Meta:
        model (ExcelDownload): The model to filter on.
        fields (dict): A dictionary of fields and their lookup types.

    Methods:
        filter_status(qs, name, value): Filters the queryset based on the status values provided.
        qs: Get the filtered queryset based on the current filter set and user.

    """
    status_list = StringListFilter(method='filter_status')

    class Meta:
        model = ExcelDownload
        fields = {
            'started_at': ['lt', 'gt', 'gte', 'lte']
        }

    def filter_status(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                # internal filtering
                return qs.filter(status__in=value).distinct()
            # client side filtering
            return qs.filter(status__in=[
                ExcelDownload.EXCEL_GENERATION_STATUS.get(item).value for item in value
            ]).distinct()
        return qs

    @property
    def qs(self):
        return super().qs.filter(
            created_by=self.request.user
        )


class ClientFilter(django_filters.FilterSet):
    """ClientFilter class

    This class is used to filter the Client model based on various fields.

    Attributes:
        name (django_filters.CharFilter): A filter for the 'name' field of the Client model.
        is_active (django_filters.BooleanFilter): A filter for the 'is_active' field of the Client model.
        use_cases (StringListFilter): A filter for the 'use_cases' field of the Client model.

    Methods:
        filter_name(queryset, name, value): Filter the queryset based on the 'name' field.
        filter_use_cases(qs, name, value): Filter the queryset based on the 'use_cases' field.
        qs: Get the filtered queryset based on the user's role.

    """
    name = django_filters.CharFilter(method='filter_name')
    is_active = django_filters.BooleanFilter()
    use_cases = StringListFilter(method='filter_use_cases')

    class Meta:
        model = Client
        fields = ()

    def filter_name(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__unaccent__icontains=value) |
            Q(acronym__icontains=value) |
            Q(contact_name__icontains=value) |
            Q(contact_email__icontains=value)
        ).distinct()

    def filter_use_cases(self, qs, name, value):
        enum_values = [Client.USE_CASE_TYPES[use_case].value for use_case in value]
        return qs.filter(use_cases__overlap=enum_values)

    @property
    def qs(self):
        user = self.request.user
        if user.highest_role == USER_ROLE.ADMIN:
            return super().qs
        return super().qs.none()


class ClientTrackInfoFilter(django_filters.FilterSet):
    """

    ClientTrackInfoFilter is a class that extends django_filters.FilterSet. It provides filtering options for the fields api_type, client_codes, start_track_date, and end_track_date.

    Attributes:
      - api_type: A filter for the api_type field.
      - client_codes: A filter for the client_codes field.
      - start_track_date: A filter for the start_track_date field.
      - end_track_date: A filter for the end_track_date field.

    Methods:
      - filter_api_type(qs, name, value): A method that filters the queryset based on the api_type field.
      - filter_client_codes(qs, name, value): A method that filters the queryset based on the client_codes field.
      - filter_start_track_date(qs, name, value): A method that filters the queryset based on the start_track_date field.
      - filter_end_track_date(qs, name, value): A method that filters the queryset based on the end_track_date field.
      - qs: A property that returns the filtered queryset based on the user role.

    Usage:
      - Create an instance of ClientTrackInfoFilter and pass it to a FilterSet or a Django view for filtering the queryset.

    Example:
      filter = ClientTrackInfoFilter(data=request.GET, queryset=ClientTrackInfo.objects.all())

    """
    api_type = StringListFilter(method='filter_api_type')
    client_codes = StringListFilter(method='filter_client_codes')
    start_track_date = django_filters.DateFilter(method='filter_start_track_date')
    end_track_date = django_filters.DateFilter(method='filter_end_track_date')

    class Meta:
        model = ClientTrackInfo
        fields = ()

    def filter_api_type(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                return qs.filter(api_type__in=value).distinct()
            return qs.filter(api_type__in=[
                ExternalApiDump.ExternalApiType[item].value for item in value
            ]).distinct()
        return qs

    def filter_client_codes(self, qs, name, value):
        return qs.filter(client__code__in=value)

    def filter_start_track_date(self, qs, name, value):
        return qs.filter(tracked_date__gte=value)

    def filter_end_track_date(self, qs, name, value):
        return qs.filter(tracked_date__lte=value)

    @property
    def qs(self):
        user = self.request.user
        if user.highest_role == USER_ROLE.ADMIN:
            return super().qs.exclude(api_type='None').annotate(
                **ClientTrackInfo.annotate_api_name()
            ).select_related('client')
        return super().qs.none()


class BulkApiOperationFilter(django_filters.FilterSet):
    """
    Class: BulkApiOperationFilter

    This class is a subclass of django_filters.FilterSet and is used to filter instances of the BulkApiOperation model.

    Attributes:
        action_list: A MultipleInputFilter instance that filters the BulkApiOperation instances based on the action field.
        status_list: A MultipleInputFilter instance that filters the BulkApiOperation instances based on the status field.

    Methods:
        qs:
            This method is a property decorator that returns the filtered queryset of BulkApiOperation instances based on the provided filters.
            It filters the queryset based on the created_by field, considering only the bulk operations created by the current user.
            It also defers the loading of the success_list and failure_list fields to improve performance.

    """
    action_list = MultipleInputFilter(BulkApiOperationActionEnum, field_name='action')
    status_list = MultipleInputFilter(BulkApiOperationStatusEnum, field_name='status')

    class Meta:
        model = BulkApiOperation
        fields = []

    @property
    def qs(self):
        # TODO: SuperUser may also need to look at other's bulk operations
        return super().qs.filter(
            created_by=self.request.user,
        ).defer('success_list', 'failure_list')


ClientTrackInfoFilterDataType, ClientTrackInfoFilterDataInputType = generate_type_for_filter_set(
    ClientTrackInfoFilter,
    'contrib.schema.client_track_information_list',
    'ClientTrackInfoFilterDataType',
    'ClientTrackInfoFilterDataInputType',
)


ClientFilterDataType, ClientFilterDataInputType = generate_type_for_filter_set(
    ClientFilter,
    'contrib.schema.client_list',
    'ClientFilterDataType',
    'ClientFilterDataInputType',
)

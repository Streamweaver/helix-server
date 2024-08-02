from django.db.models import Q
import django_filters

from apps.users.roles import USER_ROLE
from apps.contact.models import Contact, Communication, CommunicationMedium
from utils.filters import StringListFilter, generate_type_for_filter_set, IDListFilter


class ContactFilter(django_filters.FilterSet):
    """
    ContactFilter is a class used for filtering queries on the Contact model.

    Attributes:
        id: A filter for the 'id' field which performs a case-insensitive exact match.
        first_name_contains: A filter for the 'first_name' field which performs a case-insensitive
            substring match.
        last_name_contains: A filter for the 'last_name' field which performs a case-insensitive
            substring match.
        name_contains: A custom filter method that filters based on 'first_name' or 'last_name'
            case-insensitive substring match.
        countries_of_operation: A custom filter method that filters based on 'countries_of_operation'
            attribute of the Contact model.

    Methods:
        filter_name_contains(qs, name, value): A custom filter method that performs a case-insensitive substring
            match on 'first_name' and 'last_name' fields of the Contact model.
        filter_countries(qs, name, value): A custom filter method that filters based on 'countries_of_operation'
            attribute of the Contact model.
        qs: A property that returns the filtered queryset based on the user's highest role.

    Usage:
        # Create an instance of ContactFilter
        contact_filter = ContactFilter(data=request.GET, queryset=Contact.objects.all())

        # Apply filters
        queryset = contact_filter.qs

        # Iterate over the filtered queryset
        for contact in queryset:
            print(contact.first_name)

    Note:
        This class is designed to be used with Django and relies on the django-filters library.
        Make sure to import the required dependencies and configure the necessary settings.
        """
    id = django_filters.CharFilter(field_name='id', lookup_expr='iexact')
    first_name_contains = django_filters.CharFilter(field_name='first_name', lookup_expr='unaccent__icontains')
    last_name_contains = django_filters.CharFilter(field_name='last_name', lookup_expr='unaccent__icontains')
    name_contains = django_filters.CharFilter(method='filter_name_contains')
    countries_of_operation = StringListFilter(method='filter_countries')

    class Meta:
        model = Contact
        fields = ['country']

    def filter_name_contains(self, qs, name, value):
        return qs.filter(Q(first_name__unaccent__icontains=value) | Q(last_name__unaccent__icontains=value))

    def filter_countries(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(countries_of_operation__in=value).distinct()

    @property
    def qs(self):
        if self.request.user.highest_role == USER_ROLE.GUEST.value:
            return super().qs.none()
        return super().qs.distinct()


class CommunicationFilter(django_filters.FilterSet):
    """

    The CommunicationFilter class is a subclass of the django_filters.FilterSet class and is used to filter instances of
    the Communication model.

    Attributes:
        - id: A CharFilter that filters the 'id' field of the Communication model based on an exact case-insensitive
        match.
        - subject_contains: A CharFilter that filters the 'subject' field of the Communication model based on a
        case-insensitive substring match, using the 'unaccent__icontains' lookup expression.

    Meta:
        - model: The model to filter, which is set to the Communication model.
        - fields: The fields to include in the filter, which are 'contact' and 'country'.

    Methods:
        - qs: A property method that overrides the default queryset method of the FilterSet class. It filters the
        queryset based on the user's highest role. If the user's highest role is set to 'GUEST', it returns an empty
        queryset. Otherwise, it returns the distinct queryset obtained from the superclass method.

    Example usage:

    filter = CommunicationFilter(request.GET, queryset=Communication.objects.all())
    filtered_queryset = filter.qs

    Note: This code/documentation assumes the existence of a Communication model and a USER_ROLE enum with the 'GUEST'
    value.
    """
    id = django_filters.CharFilter(field_name='id', lookup_expr='iexact')
    subject_contains = django_filters.CharFilter(field_name='subject', lookup_expr='unaccent__icontains')

    class Meta:
        model = Communication
        fields = ['contact', 'country']

    @property
    def qs(self):
        if self.request.user.highest_role == USER_ROLE.GUEST.value:
            return super().qs.none()
        return super().qs.distinct()


class CommunicationMediumFilter(django_filters.FilterSet):
    """
    Class CommunicationMediumFilter

    A class used to filter communication mediums based on certain criteria.

    Attributes:
        ids (IDListFilter): A custom filter that filters communication mediums based on a list of IDs.

    Meta:
        model (CommunicationMedium): The model that the filter is applied to.
        fields (list): The fields of the model that can be filtered.

    """
    ids = IDListFilter(field_name='id')

    class Meta:
        model = CommunicationMedium
        fields = []


ContactFilterDataType, ContactFilterDataInputType = generate_type_for_filter_set(
    ContactFilter,
    'contact.schema.contact_list',
    'ContactFilterDataType',
    'ContactFilterDataInputType',
)

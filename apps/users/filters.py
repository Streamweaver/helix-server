from django.contrib.auth.models import Permission
from django.db import models
from django.db.models.functions import Lower, StrIndex, Concat, Coalesce
import django_filters
from django.db.models import Min

from apps.users.models import User, Portfolio
from apps.users.enums import USER_ROLE
from utils.filters import (
    StringListFilter,
    IDListFilter,
    generate_type_for_filter_set,
)


class UserFilter(django_filters.FilterSet):
    """
    UserFilter

    FilterSet class for filtering User objects.

    Filters:
    - role_in: Filter users by role. Accepts a list of roles.
    - role_not_in: Filter users by excluding roles. Accepts a list of roles.
    - monitoring_sub_region_in: Filter users by monitoring sub region. Accepts a list of monitoring sub region ids.
    - monitoring_sub_region_not_in: Filter users by excluding monitoring sub region. Accepts a list of monitoring sub region ids.
    - full_name: Filter users by full name. Accepts a string value.
    - include_inactive: Filter users by including or excluding inactive users. Accepts a boolean value.
    - id: Filter users by id. Accepts an exact id value.
    - permissions: Filter users by permissions. Accepts a list of permissions.

    Methods:
    - filter_role_not_in(queryset, name, value): Filter users by excluding roles.
    - filter_monitoring_sub_region_in(queryset, name, value): Filter users by monitoring sub region.
    - filter_monitoring_sub_region_not_in(queryset, name, value): Filter users by excluding monitoring sub region.
    - filter_role_in(queryset, name, value): Filter users by role.
    - filter_full_name(queryset, name, value): Filter users by full name.
    - filter_include_inactive(queryset, name, value): Filter users by including or excluding inactive users.
    - filter_permissions(queryset, name, value): Filter users by permissions.

    Attributes:
    - qs: Property to get the filtered queryset with prefetch related portfolios and distinct roles.
    """
    role_in = StringListFilter(method='filter_role_in')
    role_not_in = StringListFilter(method='filter_role_not_in')
    monitoring_sub_region_in = IDListFilter(method='filter_monitoring_sub_region_in')
    monitoring_sub_region_not_in = IDListFilter(method='filter_monitoring_sub_region_not_in')
    full_name = django_filters.CharFilter(method='filter_full_name')
    include_inactive = django_filters.BooleanFilter(method='filter_include_inactive')
    id = django_filters.CharFilter(field_name='id', lookup_expr='iexact')
    permissions = StringListFilter(method='filter_permissions')

    class Meta:
        model = User
        fields = ['email', 'is_active']

    def filter_role_not_in(self, queryset, name, value):
        roles = [USER_ROLE[role].value for role in value]
        return queryset.filter(
            ~models.Q(portfolios__role__in=roles)
        )

    def filter_monitoring_sub_region_in(self, queryset, name, value):
        return queryset.filter(
            portfolios__monitoring_sub_region__in=value
        )

    def filter_monitoring_sub_region_not_in(self, queryset, name, value):
        return queryset.filter(
            ~models.Q(portfolios__monitoring_sub_region__in=value)
        )

    def filter_role_in(self, queryset, name, value):
        roles = [USER_ROLE[role].value for role in value]
        return queryset.annotate(
            highest_user_role=Min('portfolios__role')
        ).filter(highest_user_role__in=roles)

    def filter_full_name(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.annotate(
            full=Coalesce(
                Lower('full_name'),
                Concat(Lower('first_name'), models.Value(' '), Lower('last_name')),
            )
        ).annotate(
            idx=StrIndex('full', models.Value(value.lower()))
        ).filter(full__unaccent__icontains=value).order_by('idx')

    def filter_include_inactive(self, queryset, name, value):
        if value is False:
            return queryset.filter(is_active=True)
        return queryset

    def filter_permissions(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(groups__permissions__codename__in=value)

    @property
    def qs(self):
        # to get the highest role
        return super().qs.prefetch_related('portfolios').distinct()


class PortfolioFilter(django_filters.FilterSet):
    """
    The PortfolioFilter class is a subclass of django_filters.FilterSet and is used to filter instances of the Portfolio model. It provides the role_in filter, which allows filtering by the role field using a list of values.

    Attributes:
        - role_in (StringListFilter): A filter for the role field using a list of values.

    Methods:
        - filter_role_in(queryset, name, value): This method is used to filter the queryset based on the role field. It takes three parameters:
            - queryset (QuerySet): The initial queryset to be filtered.
            - name (str): The name of the field being filtered.
            - value (list): The list of role values to filter on.

        It returns a filtered queryset based on the role field.

    Example usage:
        filter = PortfolioFilter(data=request.GET, queryset=Portfolio.objects.all())
        filtered_queryset = filter.qs

        Note that to use the filter_role_in method, you need to specify it in the method attribute of the role_in filter when defining the PortfolioFilter class.
    """
    role_in = StringListFilter(method='filter_role_in')

    class Meta:
        model = Portfolio
        fields = {
            'monitoring_sub_region': ['in'],
            'country': ['in'],
        }

    def filter_role_in(self, queryset, name, value):
        roles = [USER_ROLE[role].value for role in value]
        return queryset.filter(
            role__in=roles
        )


class ReviewerUserFilter(UserFilter):
    """
    A class representing a reviewer user filter.

    This class extends the UserFilter class and provides a filtered queryset of users who have the 'add_review' permission.

    Attributes:
        qs (django.db.models.query.QuerySet): The filtered queryset of users.

    Methods:
        qs: Returns the filtered queryset of users.

    """
    @property
    def qs(self):
        return super().qs.filter(
            groups__permissions__id=Permission.objects.get(codename='add_review').id
        )


UserFilterDataType, UserFilterDataInputType = generate_type_for_filter_set(
    UserFilter,
    'users.schema.users',
    'UserFilterDataType',
    'UserFilterDataInputType',
)

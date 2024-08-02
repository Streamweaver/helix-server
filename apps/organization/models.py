from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates.general import StringAgg
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_enumfield import enum

from apps.contrib.models import MetaInformationArchiveAbstractModel, SoftDeleteModel
from apps.common.utils import EXTERNAL_ARRAY_SEPARATOR

User = get_user_model()


class OrganizationKind(MetaInformationArchiveAbstractModel, models.Model):
    """
    Class: OrganizationKind

    This class represents the model for an organization kind. It inherits from `MetaInformationArchiveAbstractModel` and
    `models.Model`.

    Attributes:
    - name: A `CharField` representing the title of the organization kind.
    - reliability: An `EnumField` representing the reliability of the organization kind. It has the following possible
    values:
        - LOW: 0
        - MEDIUM: 1
        - HIGH: 2

    Methods:
    - __str__(): Returns the name of the organization kind as a string.

    """
    class ORGANIZATION_RELIABILITY(enum.Enum):
        LOW = 0
        MEDIUM = 1
        HIGH = 2
    name = models.CharField(verbose_name=_('Title'), max_length=256)
    reliability = enum.EnumField(
        ORGANIZATION_RELIABILITY, verbose_name=_('Reliability'),
        default=ORGANIZATION_RELIABILITY.LOW
    )

    def __str__(self):
        return self.name


class Organization(MetaInformationArchiveAbstractModel,
                   SoftDeleteModel,
                   models.Model):
    """
    Class representing an organization.

    This class inherits from `MetaInformationArchiveAbstractModel`, `SoftDeleteModel`, and `models.Model`.

    Attributes:
        name (CharField): The title of the organization.
        short_name (CharField): The short name of the organization.
        category (EnumField): The geographical coverage category of the organization.
        countries (ManyToManyField): The countries associated with the organization.
        organization_kind (ForeignKey): The type of organization.
        methodology (TextField): Methodology description of the organization.
        parent (ForeignKey): The parent organization.

    Methods:
        get_excel_sheets_data(cls, user_id, filters): Returns data for Excel sheets.
        __str__(): Returns a string representation of the organization.

    Nested Classes:
        ORGANIZATION_CATEGORY (Enum): Enumeration representing the organization category.
    """
    class ORGANIZATION_CATEGORY(enum.Enum):
        UNKNOWN = 0
        REGIONAL = 1
        INTERNATIONAL = 2
        NATIONAL = 3
        LOCAL = 4
        OTHER = 5

        __labels__ = {
            UNKNOWN: _("Unknown"),
            REGIONAL: _("Regional"),
            INTERNATIONAL: _("International"),
            NATIONAL: _("National"),
            LOCAL: _("Local"),
            OTHER: _("Other"),
        }
    name = models.CharField(verbose_name=_('Title'), max_length=512)
    short_name = models.CharField(verbose_name=_('Short Name'), max_length=64,
                                  null=True)
    category = enum.EnumField(ORGANIZATION_CATEGORY, verbose_name=_('Geographical Coverage'),
                              default=ORGANIZATION_CATEGORY.UNKNOWN)
    countries = models.ManyToManyField('country.Country', blank=True, verbose_name=_('Countries'),
                                       related_name='organizations')
    organization_kind = models.ForeignKey('OrganizationKind', verbose_name=_('Organization Type'),
                                          blank=True, null=True,
                                          on_delete=models.SET_NULL,
                                          related_name='organizations')
    methodology = models.TextField(verbose_name=_('Methodology'), blank=True, null=True)
    parent = models.ForeignKey('Organization', verbose_name=_('Organization'),
                               null=True, blank=True,
                               on_delete=models.CASCADE, related_name='sub_organizations')

    @classmethod
    def get_excel_sheets_data(cls, user_id, filters):
        from apps.organization.filters import OrganizationFilter

        class DummyRequest:
            def __init__(self, user):
                self.user = user

        headers = OrderedDict(
            id='ID',
            created_by__full_name='Created by',
            created_at='Created at',
            last_modified_by__full_name='Updated by',
            modified_at='Updated at',
            name='Name',
            organization_kind__name='Organization type',
            # Extra added fields
            countries_iso3='ISO3',
            category='Geographical coverage',
            countries_name='Countries',
            # Extra added fields
            old_id='Old ID',
            short_name='Short name',
            methodology='Methodology',
        )
        data = OrganizationFilter(
            data=filters,
            request=DummyRequest(user=User.objects.get(id=user_id)),
        ).qs.annotate(
            countries_iso3=StringAgg('countries__iso3', EXTERNAL_ARRAY_SEPARATOR, distinct=True),
            # sourced_entries_count=models.Count('sourced_entries', distinct=True),
            # published_entries_count=models.Count('published_entries', distinct=True),
            countries_name=StringAgg('countries__idmc_short_name', EXTERNAL_ARRAY_SEPARATOR, distinct=True),
        ).order_by('created_at')

        def transformer(datum):
            return {
                **datum,
                **dict(
                    category=getattr(Organization.ORGANIZATION_CATEGORY.get(datum['category']), 'label', ''),
                )
            }

        return {
            'headers': headers,
            'data': data.values(*[header for header in headers.keys()]),
            'formulae': None,
            'transformer': transformer,
        }

    def __str__(self):
        return self.name

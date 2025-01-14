from collections import OrderedDict
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_enumfield import enum
from django.db.models import JSONField
from django.contrib.auth import get_user_model
from apps.contrib.models import MetaInformationAbstractModel

User = get_user_model()


class ParkedItem(MetaInformationAbstractModel):
    """
    ParkedItem is a class that represents a parked item in a parking lot. It is a subclass of
    MetaInformationAbstractModel.

    Attributes:
    - country: A ForeignKey field that refers to the Country model. It represents the country in which the parked item
    is located.
    - title: A TextField that represents the title of the parked item.
    - url: A URLField that represents the URL of the parked item.
    - assigned_to: A ForeignKey field that refers to the User model. It represents the user assigned to the parked item.
    - status: An enum.EnumField field that represents the status of the parked item. It is a member of the
    PARKING_LOT_STATUS enum.
    - comments: A TextField that represents the comments for the parked item.
    - source: An enum.EnumField field that represents the source of the parked item. It is a member of the
    PARKING_LOT_SOURCE enum.
    - source_uuid: A CharField that represents the UUID of the source.
    - meta_data: A JSONField that stores additional metadata for the parked item.

    Methods:
    - __str__: Returns a string representation of the parked item.
    - get_excel_sheets_data: Retrieves data for generating Excel sheets based on the provided filters and user ID.
    - get_parking_lot_excel_sheets_data: Retrieves data for generating Excel sheets based on the provided parking lot
    queryset.

    """
    class PARKING_LOT_STATUS(enum.Enum):
        TO_BE_REVIEWED = 0
        REVIEWED = 1
        ON_GOING = 2

        __labels__ = {
            TO_BE_REVIEWED: _('To be reviewed'),
            REVIEWED: _('Reviewed'),
            ON_GOING: _('On going'),
        }

    class PARKING_LOT_SOURCE(enum.Enum):
        IDETECT = 0
        HAZARD_MONITORING = 1
        ACLED = 2

        __labels__ = {
            IDETECT: _('Idetect'),
            HAZARD_MONITORING: _('Hazard Monitoring'),
            ACLED: _('Acled')
        }

    country = models.ForeignKey(
        'country.Country',
        verbose_name=_('Country'),
        related_name='parked_items',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    title = models.TextField(verbose_name=_('Title'))
    url = models.URLField(verbose_name=_('URL'), max_length=2000)
    assigned_to = models.ForeignKey('users.User', verbose_name=_('Assigned To'),
                                    related_name='assigned_parked_items',
                                    on_delete=models.SET_NULL,
                                    blank=True, null=True)
    status = enum.EnumField(PARKING_LOT_STATUS, verbose_name=_('Status'),
                            default=PARKING_LOT_STATUS.TO_BE_REVIEWED)
    comments = models.TextField(verbose_name=_('Comments'),
                                blank=True, null=True)
    source = enum.EnumField(PARKING_LOT_SOURCE, verbose_name=_('Source'),
                            blank=True, null=True)
    source_uuid = models.CharField(verbose_name=_('Source Uuid'),
                                   max_length=255, blank=True, null=True)
    meta_data = JSONField(blank=True, null=True, default=None)

    def __str__(self):
        return f'{self.country.name} - {self.title}'

    @classmethod
    def get_excel_sheets_data(cls, user_id, filters):
        from apps.parking_lot.filters import ParkingLotFilter

        class DummyRequest:
            def __init__(self, user):
                self.user = user

        qs = ParkingLotFilter(
            data=filters,
            request=DummyRequest(user=User.objects.get(id=user_id)),
        ).qs
        return cls.get_parking_lot_excel_sheets_data(qs)

    @classmethod
    def get_parking_lot_excel_sheets_data(cls, parking_lot: models.QuerySet):

        headers = OrderedDict(
            id='ID',
            created_at='Date Created',
            created_by__full_name='Created by',
            assigned_to__full_name='Assignee',
            title='Title',
            status='Status',
            url='Url',
            comments='Comments',
        )
        values = parking_lot.order_by(
            'created_at',
        ).values(*[header for header in headers.keys()])

        def transformer(datum):

            def get_enum_label(key, Enum):
                val = datum[key]
                obj = Enum.get(val)
                return getattr(obj, "label", val)

            return {
                **datum,
                'status': get_enum_label(
                    'status', ParkedItem.PARKING_LOT_STATUS
                )
            }

        return {
            'headers': headers,
            'data': values,
            'formulae': None,
            'transformer': transformer,
        }

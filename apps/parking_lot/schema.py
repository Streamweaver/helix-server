import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from utils.graphene.enums import EnumDescription

from apps.parking_lot.models import ParkedItem
from apps.parking_lot.enums import (
    ParkingLotStatusGrapheneEnum,
    ParkingLotSourceGrapheneEnum,
)
from apps.parking_lot.filters import ParkingLotFilter
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount


class ParkedItemType(DjangoObjectType):
    """
    Class representing a ParkedItemType.

    This class is a subclass of DjangoObjectType and is used to translate ParkedItem model fields into GraphQL fields.
    It provides additional fields for status, status_display, source, source_display, and entry.

    Attributes:
        status (graphene.Field): A field representing the status of the ParkedItemType.
        status_display (EnumDescription): A field representing the display value of the status field.
        source (graphene.Field): A field representing the source of the ParkedItemType.
        source_display (EnumDescription): A field representing the display value of the source field.
        entry (graphene.Field): A field representing the entry associated with the ParkedItemType.

    """
    class Meta:
        model = ParkedItem

    status = graphene.Field(ParkingLotStatusGrapheneEnum)
    status_display = EnumDescription(source='get_status_display')
    source = graphene.Field(ParkingLotSourceGrapheneEnum)
    source_display = EnumDescription(source='get_source_display')
    entry = graphene.Field('apps.entry.schema.EntryType')


class ParkedItemListType(CustomDjangoListObjectType):
    """
    A class representing a list of Parked Items.

    Attributes:
    - model (Model): The Django model associated with the Parked Item.
    - filterset_class (FilterSet): The FilterSet class to be used for filtering the list of Parked Items.

    """
    class Meta:
        model = ParkedItem
        filterset_class = ParkingLotFilter


class Query:
    """

    Class Query

    This class represents a query for retrieving parked items and parked item list.

    Attributes:
    - parked_item: DjangoObjectField
        A field representing a parked item.
    - parked_item_list: DjangoPaginatedListObjectField
        A field representing a paginated list of parked items.

    """
    parked_item = DjangoObjectField(ParkedItemType)
    parked_item_list = DjangoPaginatedListObjectField(ParkedItemListType,
                                                      pagination=PageGraphqlPaginationWithoutCount(
                                                          page_size_query_param='pageSize'
                                                      ))

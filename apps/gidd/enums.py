import graphene
from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
)
from django_enumfield import enum
from apps.gidd.models import StatusLog, ReleaseMetadata
from django.utils.translation import gettext_lazy as _

GiddStatusLogEnum = convert_enum_to_graphene_enum(StatusLog.Status, name='GiddStatusLogTypeEnum')
GiddReleaseEnvironmentsEnum = convert_enum_to_graphene_enum(
    ReleaseMetadata.ReleaseEnvironment, name='GiddReleaseEnvironmentsEnum'
)


enum_map = dict(
    GiddLogStatusEnum=GiddStatusLogEnum,
    GiddReleaseEnvironmentsEnum=GiddReleaseEnvironmentsEnum,
)


class GiddEnumType(graphene.ObjectType):
    """

    This class represents a GiddEnumType object.

    Methods:
        - gidd_release_meta_data: Retrieve the GiddReleaseEnvironmentsEnum field.

    """
    gidd_release_meta_data = graphene.Field(GiddReleaseEnvironmentsEnum)


# NOTE: We are creating a separate enum because we are not exposting "OTEHR" in GIDD
class CRISIS_TYPE_PUBLIC(enum.Enum):
    """
    CRISIS_TYPE_PUBLIC is an enumeration class that defines various types of public crises.

    Attributes:
        CONFLICT (int): Represents a public crisis related to conflict.
        DISASTER (int): Represents a public crisis related to a natural or man-made disaster.

    Attributes:
        __labels__ (dict): A dictionary that maps each crisis type to its corresponding label.

    Example usage:
        >>> crisis_type = CRISIS_TYPE_PUBLIC.CONFLICT
        >>> print(crisis_type)
        CONFLICT

        >>> print(CRISIS_TYPE_PUBLIC.__labels__[CRISIS_TYPE_PUBLIC.DISASTER])
        Disaster
    """
    CONFLICT = 0
    DISASTER = 1

    __labels__ = {
        CONFLICT: _("Conflict"),
        DISASTER: _("Disaster"),
    }

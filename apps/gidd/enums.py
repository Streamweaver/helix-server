import graphene
from django.db import models
from utils.graphene.enums import (
    convert_enum_to_graphene_enum,
)

from apps.gidd.models import StatusLog, ReleaseMetadata

GiddStatusLogEnum = convert_enum_to_graphene_enum(StatusLog.Status, name='GiddStatusLogTypeEnum')
GiddReleaseEnvironmentsEnum = convert_enum_to_graphene_enum(
    ReleaseMetadata.ReleaseEnvironment, name='GiddReleaseEnvironmentsEnum'
)


enum_map = dict(
    GiddLogStatusEnum=GiddStatusLogEnum,
    GiddReleaseEnvironmentsEnum=GiddReleaseEnvironmentsEnum,
)


class GiddEnumType(graphene.ObjectType):
    gidd_release_meta_data = graphene.Field(GiddReleaseEnvironmentsEnum)


# -- Used by External-Endpoints

class DisaggregationExportTypeEnum(models.TextChoices):
    EXCEL = 'EXCEL', 'EXCEL'
    GEO_JSON = 'GeoJSON', 'GeoJSON'

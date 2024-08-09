from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_enumfield import enum

from apps.contrib.models import MetaInformationArchiveAbstractModel
from apps.crisis.models import Crisis


class ContextualUpdate(MetaInformationArchiveAbstractModel, models.Model):
    """

    The ContextualUpdate class represents a model that stores contextual information related to an event or crisis
    update. It inherits from the MetaInformationArchiveAbstractModel and models.Model classes.

    Attributes:
    - url (models.URLField): Represents the source URL associated with the update. It is optional and can have a maximum
    length of 2000 characters.
    - preview (models.ForeignKey): Represents the preview of the update, which is associated with a SourcePreview model.
    It is nullable and is set to null when the preview is deleted. This field allows retrieving the preview during entry
    creation or update.
    - document (models.ForeignKey): Represents the attachment associated with the update, which is related to the
    Attachment model. It is nullable and is set to null when the attachment is deleted.
    - article_title (models.TextField): Represents the title of the event or crisis update.
    - sources (models.ManyToManyField): Represents the sources of the update, which are associated with the Organization
    model. It allows multiple sources and is nullable.
    - publishers (models.ManyToManyField): Represents the publishers of the update, which are associated with the
    Organization model. It allows multiple publishers and is nullable.
    - publish_date (models.DateTimeField): Represents the date and time when the update was published.
    - source_excerpt (models.TextField): Represents an excerpt from the source related to the update. It is optional and
    nullable.
    - excerpt_idu (models.TextField): Represents an excerpt for Internal Displacement Unit (IDU). It is optional and
    nullable.
    - idmc_analysis (models.TextField): Represents the trends and patterns of displacement to be highlighted in the
    update. It is nullable.
    - caveats (models.TextField): Represents any caveats related to the update. It is optional and nullable.
    - is_confidential (models.BooleanField): Represents whether the source of the update is confidential or not. It is a
    boolean field and is set to False by default.
    - tags (models.ManyToManyField): Represents the tags associated with the update, which are related to the FigureTag
    model. It allows multiple tags and is nullable.
    - countries (models.ManyToManyField): Represents the countries associated with the update, which are related to the
    Country model. It allows multiple countries and is nullable.
    - crisis_types (ArrayField): Represents the crisis types or causes associated with the update. It is implemented as
    an ArrayField of enum.EnumField, where the base_field is set to the Crisis.CRISIS_TYPE enum. It allows multiple
    crisis types and is nullable.


    Note: Please refer to the respective model documentation for more information on their attributes and usage.

    """
    url = models.URLField(verbose_name=_('Source URL'), max_length=2000,
                          blank=True, null=True)
    preview = models.ForeignKey('contrib.SourcePreview',
                                related_name='contextual_update', on_delete=models.SET_NULL,
                                blank=True, null=True,
                                help_text=_('After the preview has been generated pass its id'
                                            ' along during entry creation, so that during entry '
                                            'update the preview can be obtained.'))
    document = models.ForeignKey('contrib.Attachment', verbose_name='Attachment',
                                 on_delete=models.CASCADE, related_name='+',
                                 null=True, blank=True)
    article_title = models.TextField(verbose_name=_('Event Title'))
    sources = models.ManyToManyField('organization.Organization', verbose_name=_('Source'),
                                     blank=True, related_name='sourced_contextual_updates')
    publishers = models.ManyToManyField('organization.Organization', verbose_name=_('Publisher'),
                                        blank=True, related_name='published_contextual_updates')
    publish_date = models.DateTimeField(verbose_name=_('Published DateTime'),
                                        blank=True, null=True)
    source_excerpt = models.TextField(verbose_name=_('Excerpt from Source'),
                                      blank=True, null=True)
    excerpt_idu = models.TextField(verbose_name=_('Excerpt for IDU'), blank=True, null=True)
    idmc_analysis = models.TextField(verbose_name=_('Trends and patterns of displacement to be highlighted'),
                                     blank=False, null=True)
    caveats = models.TextField(verbose_name=_('Caveats'), blank=True, null=True)
    is_confidential = models.BooleanField(
        verbose_name=_('Confidential Source'),
        default=False,
    )
    tags = models.ManyToManyField('entry.FigureTag', blank=True)
    countries = models.ManyToManyField('country.Country', blank=True)
    crisis_types = ArrayField(
        base_field=enum.EnumField(Crisis.CRISIS_TYPE, verbose_name=_('Cause')),
        blank=True, null=True
    )

from typing import Tuple

from django.db import models
from django.db.models import ProtectedError
from django.utils.translation import gettext, gettext_lazy as _
from django.core.exceptions import ValidationError

from helix.settings import RESOURCE_NUMBER, RESOURCEGROUP_NUMBER

from apps.contrib.models import MetaInformationArchiveAbstractModel


class ResourceGroup(MetaInformationArchiveAbstractModel):
    """
    Represents a group of resources.

    Attributes:
        name (str): The name of the resource group.

    Methods:
        is_deletable(): Checks if the resource group is deletable.
        can_delete(): Checks if the resource group can be deleted and returns a tuple with a boolean and a string.
        __str__(): Returns a string representation of the resource group.
        save(): Saves the resource group.

    Inherits from:
        MetaInformationArchiveAbstractModel
    """
    name = models.CharField(verbose_name=_('Name'), max_length=256)

    def is_deletable(self) -> bool:
        if res := self.resources.count():
            raise ProtectedError(gettext('There are %d resource(s)'
                                         ' associated to this group.'
                                         ' Please delete them first') % res, [])
        return True

    def can_delete(self, *args, **kwargs) -> Tuple[bool, str]:
        try:
            self.is_deletable()
        except ProtectedError as e:
            return False, e.args[0]
        return True, ''

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk is None and ResourceGroup.objects.filter(created_by=self.created_by).count() >= RESOURCEGROUP_NUMBER:
            raise ValidationError(gettext('Can only create %s resource groups') % RESOURCEGROUP_NUMBER)
        return super(ResourceGroup, self).save(*args, **kwargs)


class Resource(MetaInformationArchiveAbstractModel):
    """

    Class Resource

    This class represents a resource and inherits from the MetaInformationArchiveAbstractModel class.

    Attributes:
    - name (CharField): The name of the resource (256 characters maximum).
    - url (URLField): The URL of the resource (2000 characters maximum).
    - group (ForeignKey): The resource group that this resource belongs to.
    - countries (ManyToManyField): The countries where this resource is available.
    - last_accessed_on (DateTimeField): The datetime when this resource was last accessed.

    Methods:
    - __str__(): Returns a string representation of the resource.
    - save(\*args, \*\*kwargs): Overrides the save method to enforce a maximum number of resources that can be created.

    """
    name = models.CharField(verbose_name=_('Name'), max_length=256)
    url = models.URLField(verbose_name=_('URL'), max_length=2000)
    group = models.ForeignKey('ResourceGroup', verbose_name=_('Resource Group'),
                              related_name='resources', on_delete=models.SET_NULL,
                              blank=True, null=True)
    countries = models.ManyToManyField('country.Country', verbose_name=_('Countries'),
                                       related_name='+', blank=False)
    last_accessed_on = models.DateTimeField(verbose_name=_('Last Accessed On'),
                                            blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk is None and Resource.objects.filter(created_by=self.created_by).count() >= RESOURCE_NUMBER:
            raise ValidationError(gettext('Can only create %s Resource') % RESOURCE_NUMBER)
        return super(Resource, self).save(*args, **kwargs)

from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates.general import StringAgg
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_enumfield import enum
from apps.common.enums import GENDER_TYPE
from apps.contrib.models import MetaInformationArchiveAbstractModel
from apps.common.utils import EXTERNAL_ARRAY_SEPARATOR

User = get_user_model()


class Contact(MetaInformationArchiveAbstractModel, models.Model):
    """

    Module: contact

    This module contains the Contact class which represents a contact person.

    Classes:
    - Contact: Represents a contact person.

    Methods:
    - __str__: Returns a string representation of the contact.
    - get_full_name: Returns the full name of the contact.
    - get_excel_sheets_data: Retrieves data for Excel sheets.
    - save: Saves the contact to the database.

    Attributes:
    - designation: Enum field representing the designation of the contact (e.g., Mr, Ms, Mrs).
    - first_name: Char field representing the first name of the contact.
    - last_name: Char field representing the last name of the contact.
    - full_name: Char field representing the full name of the contact.
    - gender: Enum field representing the gender of the contact.
    - job_title: Char field representing the job title of the contact.
    - organization: Foreign key field representing the organization the contact belongs to.
    - countries_of_operation: Many-to-many field representing the countries in which the contact operates.
    - country: Foreign key field representing the country of the contact.
    - email: Email field representing the email of the contact.
    - skype: Char field representing the Skype ID of the contact.
    - phone: Char field representing the phone number of the contact.
    - comment: Text field representing additional comments about the contact.

    """
    class DESIGNATION(enum.Enum):
        MR = 0
        MS = 1
        MRS = 2

        __labels__ = {
            MR: _("Mr"),
            MS: _("Ms"),
            MRS: _("Mrs"),
        }

    designation = enum.EnumField(DESIGNATION)
    first_name = models.CharField(verbose_name=_('First Name'), max_length=256)
    last_name = models.CharField(verbose_name=_('Last Name'), max_length=256)
    full_name = models.CharField(verbose_name=_('Full Name'), max_length=512,
                                 blank=True, null=True,
                                 help_text=_('Auto generated'))
    gender = enum.EnumField(GENDER_TYPE, verbose_name=_('Gender'))
    job_title = models.CharField(verbose_name=_('Job Title'), max_length=256)
    organization = models.ForeignKey('organization.Organization', verbose_name=_('Organization'),
                                     blank=True, null=True,
                                     related_name='contacts', on_delete=models.CASCADE)
    countries_of_operation = models.ManyToManyField('country.Country',
                                                    verbose_name=_('Countries of Operation'),
                                                    blank=True,
                                                    related_name='operating_contacts',
                                                    help_text=_(
                                                        'In which countries does this contact person'
                                                        ' operate?'
                                                    ))
    country = models.ForeignKey('country.Country',
                                verbose_name=_('Country'),
                                blank=True, null=True,
                                related_name='contacts', on_delete=models.SET_NULL)
    email = models.EmailField(verbose_name=_('Email'), blank=True, null=True)
    skype = models.CharField(verbose_name=_('Skype'), max_length=32,
                             blank=True, null=True)
    phone = models.CharField(verbose_name=_('Phone'), max_length=256,
                             blank=True, null=True)
    comment = models.TextField(verbose_name=_('Comment'), blank=True, null=True)

    def __str__(self):
        return f'{self.designation.name} {self.first_name} {self.last_name}'

    def get_full_name(self):
        return ' '.join([
            name for name in [self.first_name, self.last_name] if name
        ]) or self.email

    @classmethod
    def get_excel_sheets_data(cls, user_id, filters):
        from apps.contact.filters import ContactFilter

        class DummyRequest:
            def __init__(self, user):
                self.user = user

        headers = OrderedDict(
            id='ID',
            created_by__full_name='Created by',
            created_at='Created at',
            last_modified_by__full_name='Updated by',
            last_modified_by='Updated at',
            full_name='Name',
            gender='Gender',
            organization__name='Organization',
            job_title='Job title',
            country__idmc_short_name='Country',
            operating_countries='Countries of operation',
            operating_countries_regions='Regions of operation',
            # Extra added fields
            old_id='Old ID',
            designation='Designation',
            communications_count='Communications count'
        )
        data = ContactFilter(
            data=filters,
            request=DummyRequest(user=User.objects.get(id=user_id)),
        ).qs.annotate(
            operating_countries=StringAgg(
                'countries_of_operation__idmc_short_name', EXTERNAL_ARRAY_SEPARATOR, distinct=True
            ),
            operating_countries_regions=StringAgg(
                'countries_of_operation__region__name', EXTERNAL_ARRAY_SEPARATOR, distinct=True
            ),
            communications_count=models.Count('communications', distinct=True),
        ).order_by(
            'created_at',
        )

        def transformer(datum):
            return {
                **datum,
                **dict(
                    designation=getattr(Contact.DESIGNATION.get(datum['designation']), 'label', ''),
                    gender=getattr(GENDER_TYPE.get(datum['gender']), 'label', ''),
                )
            }

        return {
            'headers': headers,
            'data': data.values(*[header for header in headers.keys()]),
            'formulae': None,
            'transformer': transformer,
        }

    def save(self, *args, **kwargs):
        self.full_name = self.get_full_name()
        return super().save(*args, **kwargs)


class CommunicationMedium(models.Model):
    """
    A class representing a communication medium.

    Attributes:
        name (str): The name of the communication medium.

    Methods:
        __str__(): Returns a string representation of the communication medium.

    """
    name = models.CharField(verbose_name=_('Name'), max_length=256)

    def __str__(self):
        return f'{self.name}'


class Communication(MetaInformationArchiveAbstractModel, models.Model):
    """

    Communication class is a model class that represents a communication between a contact and a user. It extends the MetaInformationArchiveAbstractModel and models.Model classes.

    Attributes:
    - contact (ForeignKey): Represents the related contact for the communication.
    - country (ForeignKey): Represents the related country for the communication. Can be blank and null.
    - subject (CharField): Represents the subject of the communication. Has a maximum length of 512.
    - content (TextField): Represents the content of the communication.
    - date (DateField): Represents the date on which the communication occurred. Can be null and blank.
    - medium (ForeignKey): Represents the medium of communication. Can be null and blank.
    - attachment (ForeignKey): Represents the attachment related to the communication. Can be null and blank.

    Methods:
    - __str__(): Returns a string representation of the communication object.

    """
    class COMMUNICATION_MEDIUM(enum.Enum):
        # keeping for the sake of migrations, remove it when recreating all migrations
        pass

    contact = models.ForeignKey('Contact', verbose_name=_('Contact'),
                                related_name='communications', on_delete=models.CASCADE)
    country = models.ForeignKey('country.Country', verbose_name=_('Country'),
                                blank=True, null=True,
                                related_name='communications', on_delete=models.CASCADE)
    subject = models.CharField(verbose_name=_('Subject'), max_length=512)
    content = models.TextField(verbose_name=_('Content'))
    date = models.DateField(verbose_name=_('Conducted Date'),
                            null=True, blank=True,
                            help_text=_('Date on which communication occurred.'))
    medium = models.ForeignKey(CommunicationMedium,
                               null=True, blank=False,
                               related_name='+', on_delete=models.SET_NULL)
    attachment = models.ForeignKey('contrib.Attachment', verbose_name='Attachment',
                                   on_delete=models.CASCADE, related_name='+',
                                   null=True, blank=True)

    def __str__(self):
        return f'{self.contact} {self.date}'

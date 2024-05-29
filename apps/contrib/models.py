import logging
import typing
import uuid
from uuid import uuid4
from collections import OrderedDict

from django.apps import apps
from django.db.models import JSONField
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_enumfield import enum

from apps.common.utils import EXTERNAL_ARRAY_SEPARATOR
from apps.users.models import User
from utils.fields import CachedFileField
from apps.contrib.redis_client_track import set_client_ids_in_redis

logger = logging.getLogger(__name__)


def global_upload_to(instance, filename: str) -> str:
    """
    Returns the upload path for a given file.

    Parameters:
        instance (object): An instance of a class.
        filename (str): The name of the file to be uploaded.

    Returns:
        str: The upload path for the file.

    Example:
        >>> instance = MyClass()
        >>> global_upload_to(instance, "file.jpg")
        'contrib/myclass/14e6e840-9009-4fc4-9f79-f0b68dd8a6cc/420e4487-3b5b-4b4f-a56a-129ccf23f0b0/file.jpg'
    """
    return f'contrib/{instance.__class__.__name__.lower()}/{uuid4()}/{uuid4()}/{filename}'


class UUIDAbstractModel(models.Model):
    """

    UUIDAbstractModel

    This class serves as an abstract model in Django for models that require a UUID field.

    Attributes:
        uuid (UUIDField): UUID field for the model.

    Meta:
        abstract (bool): Indicates that this model is abstract and cannot be instantiated directly.

    """
    uuid = models.UUIDField(verbose_name='UUID', unique=True,
                            blank=True, default=uuid4)

    class Meta:
        abstract = True


class ArchiveAbstractModel(models.Model):
    """

    Class ArchiveAbstractModel

    This is an abstract model class that can be used as a base for models that need to keep track of old primary keys.

    Attributes:
      - old_id (CharField): The old primary key for the model. This field is optional and can be null or blank.

    Meta:
      - abstract: This model should not be instantiated directly, as it is intended to be used as a base for other models.

    """
    old_id = models.CharField(verbose_name=_('Old primary key'), max_length=32,
                              null=True, blank=True)

    class Meta:
        abstract = True


class MetaInformationAbstractModel(models.Model):
    """
    This abstract class defines the meta information fields for models.

    Attributes:
        created_at (DateTimeField): The date and time when the object was created.
        modified_at (DateTimeField): The date and time when the object was last modified.
        created_by (ForeignKey): The user who created the object.
        last_modified_by (ForeignKey): The user who last modified the object.
        version_id (CharField): The version identifier of the object.
        created_by_id (Optional[int]): The ID of the user who created the object.
        last_modified_by_id (Optional[int]): The ID of the user who last modified the object.

    Meta:
        abstract (bool): Specifies that this model is abstract and cannot be used to create database tables directly.
    """
    created_at = models.DateTimeField(verbose_name=_('Created At'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_('Modified At'), auto_now=True)
    created_by = models.ForeignKey('users.User', verbose_name=_('Created By'),
                                   blank=True, null=True,
                                   related_name='created_%(class)s', on_delete=models.SET_NULL)
    last_modified_by = models.ForeignKey('users.User', verbose_name=_('Last Modified By'),
                                         blank=True, null=True,
                                         related_name='+', on_delete=models.SET_NULL)
    version_id = models.CharField(verbose_name=_('Version'), max_length=16,
                                  blank=True, null=True)

    created_by_id: typing.Optional[int]
    last_modified_by_id: typing.Optional[int]

    class Meta:
        abstract = True


class MetaInformationArchiveAbstractModel(ArchiveAbstractModel, MetaInformationAbstractModel):
    """
    A class representing the abstract model for storing meta information in an archive.

    This class is abstract and cannot be instantiated directly.

    Inherits from:
        - ArchiveAbstractModel
        - MetaInformationAbstractModel

    Attributes:
        Meta:
            abstract (bool): If True, this class is abstract and cannot be instantiated directly.

    """
    class Meta:
        abstract = True


class Attachment(MetaInformationAbstractModel):
    """

    Class Attachment

    This class represents an attachment object. It inherits from the MetaInformationAbstractModel class.

    Attributes:
        ALLOWED_MIMETYPES (tuple): A tuple containing allowed mimetypes for attachments.
        MAX_FILE_SIZE (int): The maximum file size allowed for attachments, in bytes.

    Inner class:
        FOR_CHOICES: An enumeration class representing the possible choices for the "attachment_for" attribute.

    Attributes:
        attachment (CachedFileField): A field representing the attached file.
        attachment_for (FOR_CHOICES): A field representing the type of instance for which the attachment was uploaded.
        mimetype (CharField): A field representing the mimetype of the attachment.
        encoding (CharField): A field representing the encoding of the attachment.
        filetype_detail (CharField): A field representing the detailed file type information of the attachment.

    """
    ALLOWED_MIMETYPES = (
        # text
        'application/x-abiword', 'text/csv', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/epub+zip',
        'application/vnd.oasis.opendocument.presentation',
        'application/vnd.oasis.opendocument.spreadsheet', 'application/vnd.oasis.opendocument.text', 'application/pdf',
        'application/xml', 'text/xml', 'application/vnd.ms-powerpoint', 'application/xhtml+xml', 'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/rtf', 'text/javascript',
        'text/html', 'text/calendar', 'text/plain',
        # image
        'image/gif', 'image/jpg', 'image/jpeg', 'image/png', 'image/svg+xml', 'image/tiff',
        'image/webp', 'image/bmp', 'image/vnd.microsoft.icon'
    )
    MAX_FILE_SIZE = 100 * 1024 * 1024  # MB

    class FOR_CHOICES(enum.Enum):
        ENTRY = 0
        COMMUNICATION = 1
        CONTEXTUAL_UPDATE = 2

    attachment = CachedFileField(
        verbose_name=_('Attachment'),
        blank=False,
        null=False,
        upload_to=global_upload_to,
        max_length=2000,
    )
    attachment_for = enum.EnumField(enum=FOR_CHOICES, verbose_name=_('Attachment for'),
                                    null=True, blank=True,
                                    help_text=_('The type of instance for which attachment was'
                                                ' uploaded for'))
    mimetype = models.CharField(verbose_name=_('Mimetype'), max_length=256,
                                blank=True, null=True)
    encoding = models.CharField(verbose_name=_('Encoding'), max_length=256,
                                blank=True, null=True)
    filetype_detail = models.CharField(verbose_name=_('File type detail'), max_length=2000,
                                       blank=True, null=True)


class SoftDeleteQueryset(models.QuerySet):
    """

    Class: SoftDeleteQueryset(models.QuerySet)

    A subclass of models.QuerySet that provides functionality for soft deletion.

    Methods:
    - delete(): Marks the queryset objects as deleted by updating the 'deleted_on' field with the current timestamp.

    """
    def delete(self):
        self.update(deleted_on=timezone.now())


class SoftDeleteManager(models.Manager):
    """
    Class representing a manager for soft deleting models.

    This class extends the `models.Manager` class and provides a custom `get_queryset` method to filter out deleted instances.

    Attributes:
        None

    Methods:
        get_queryset: Returns a queryset filtered to exclude deleted instances.

    """
    def get_queryset(self):
        return SoftDeleteQueryset(self.model, using=self._db).filter(deleted_on__isnull=True)


class SoftDeleteModel(models.Model):
    """
    Class for implementing soft delete functionality in models.

    SoftDeleteModel is an abstract base class that can be used to implement soft delete functionality in models. It adds a `deleted_on` field to the model to track the deletion date and time.

    Attributes:
        deleted_on (DateTimeField): A field to store the deletion date and time. It is set to `null=True` and `blank=True` to allow for undeletion.

    Methods:
        delete(*args, **kwargs): Soft deletes the model instance. Sets the `deleted_on` field to the current date and time using the `timezone.now()` function and saves the instance. Returns the updated instance.

        undelete(*args, **kwargs): Restores a soft deleted model instance. Sets the `deleted_on` field to `None` and saves the instance. Returns the updated instance.

    Meta:
        abstract = True: Specifies that this is an abstract base class and should not be created as a database table.

    Note:
        This class should be used as a base class for models that require the soft delete functionality. It provides the necessary methods and field for soft deletion and undeletion.
    """
    deleted_on = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    _objects = models.Manager()

    def delete(self, *args, **kwargs):
        self.deleted_on = timezone.now()
        self.save()
        return self

    def undelete(self, *args, **kwargs):
        self.deleted_on = None
        self.save()
        return self

    class Meta:
        abstract = True


class SourcePreview(MetaInformationAbstractModel):
    """
    This class represents a preview of a source.

    Attributes:
    - url (models.URLField): The URL of the source.
    - token (models.CharField): The token associated with the preview.
    - pdf (CachedFileField): The rendered PDF of the source.
    - status (PREVIEW_STATUS): The status of the preview.
    - remark (models.TextField): A remark associated with the preview.

    Inner class:
    - PREVIEW_STATUS (enum.Enum): The possible statuses of a preview.

    Methods:
    - get_pdf(cls, data: dict, instance: 'SourcePreview' = None) -> 'SourcePreview': Generates and stores a PDF based on the URL.
    """
    class PREVIEW_STATUS(enum.Enum):
        PENDING = 0
        COMPLETED = 1
        FAILED = 2
        IN_PROGRESS = 3
        KILLED = 4

        __labels__ = {
            PENDING: _("Pending"),
            COMPLETED: _("Completed"),
            FAILED: _("Failed"),
            IN_PROGRESS: _("In Progress"),
            KILLED: _("Killed"),
        }

    url = models.URLField(verbose_name=_('Source URL'), max_length=2000)
    token = models.CharField(verbose_name=_('Token'),
                             max_length=64, db_index=True,
                             blank=True, null=True)
    pdf = CachedFileField(
        verbose_name=_('Rendered Pdf'),
        blank=True,
        null=True,
        upload_to=global_upload_to,
        max_length=2000,
    )
    status = enum.EnumField(enum=PREVIEW_STATUS, default=PREVIEW_STATUS.PENDING)
    remark = models.TextField(verbose_name=_('Remark'),
                              blank=True, null=True)

    @classmethod
    def get_pdf(cls, data: dict, instance: 'SourcePreview' = None) -> 'SourcePreview':
        """
        Based on the url, generate a pdf and store it.
        """
        from apps.entry.tasks import generate_pdf

        url = data['url']
        created_by = data.get('created_by')
        last_modified_by = data.get('last_modified_by')
        if not instance:
            token = str(uuid.uuid4())
            instance = cls(token=token)
        instance.url = url
        instance.created_by = created_by
        instance.last_modified_by = last_modified_by
        instance.save()

        transaction.on_commit(lambda: generate_pdf.delay(
            instance.pk
        ))
        return instance


def excel_upload_to(instance, filename: str) -> str:
    """
    Constructs the file path for uploading an Excel file to the server.

    Parameters:
        instance (Any): The instance of the object being uploaded.
        filename (str): The name of the Excel file.

    Returns:
        str: The constructed file path.

    Example:
        >>> instance = MyObject()
        >>> filename = 'data.xlsx'
        >>> excel_upload_to(instance, filename)
        'contrib/excel/{generated_uuid}/{instance.download_type}/{filename}'
    """
    return f'contrib/excel/{uuid4()}/{instance.download_type}/{filename}'


def bulk_operation_snapshot(instance, filename: str) -> str:
    """
    Returns the path of a bulk operation snapshot.

    Args:
        instance: The instance of the bulk operation.
        filename: The filename of the snapshot.

    Returns:
        The path of the bulk operation snapshot in the format:
        `contrib/bulk-operation/{random_uuid}/{action_name}/{filename}`.

    """
    return f'contrib/bulk-operation/{uuid4()}/{instance.action.name}/{filename}'


class ExcelDownload(MetaInformationAbstractModel):
    """

    Class representing an Excel Download.

    Attributes:
        EXCEL_GENERATION_STATUS(enum.Enum): Enumeration of the possible generation status of the Excel file.
            PENDING: Excel generation is pending.
            IN_PROGRESS: Excel generation is in progress.
            COMPLETED: Excel generation is completed.
            FAILED: Excel generation failed.
            KILLED: Excel generation was killed.

        DOWNLOAD_TYPES(enum.Enum): Enumeration of the possible download types for the Excel file.
            CRISIS: Excel file for crisis.
            EVENT: Excel file for event.
            COUNTRY: Excel file for country.
            ENTRY: Excel file for entry.
            FIGURE: Excel file for figure.
            ORGANIZATION: Excel file for organization.
            CONTACT: Excel file for contact.
            REPORT: Excel file for report.
            ACTOR: Excel file for actor.
            INDIVIDUAL_REPORT: Excel file for individual report.
            TRACKING_DATA: Excel file for tracking data.
            PARKING_LOT: Excel file for parked items.
            FIGURE_TAG: Excel file for figure tags.
            USER: Excel file for user.
            CONTEXT_OF_VIOLENCE: Excel file for context of violence.
            MONITORING_SUB_REGION: Excel file for monitoring sub region.
            CLIENT: Excel file for client.

        started_at (DateTimeField): The timestamp when the excel generation started.
        completed_at (DateTimeField): The timestamp when the excel generation completed.
        download_type (EnumField): The type of download.
        status (EnumField): The current status of the excel generation.
        file (CachedFileField): The excel file.
        file_size (IntegerField): The size of the excel file.
        filters (JSONField): The filters used for generating the excel file.

    Methods:
        get_model_sheet_data_getter: Returns the model sheet data getter based on the download type.
        trigger_excel_generation: Triggers the excel file generation based on the given request.

    """
    class EXCEL_GENERATION_STATUS(enum.Enum):
        PENDING = 0
        IN_PROGRESS = 1
        COMPLETED = 2
        FAILED = 3
        KILLED = 4

    class DOWNLOAD_TYPES(enum.Enum):
        CRISIS = 0
        EVENT = 1
        COUNTRY = 2
        ENTRY = 3
        FIGURE = 4
        ORGANIZATION = 5
        CONTACT = 6
        REPORT = 7
        ACTOR = 8
        INDIVIDUAL_REPORT = 9
        TRACKING_DATA = 10
        PARKING_LOT = 11
        FIGURE_TAG = 12
        USER = 13
        CONTEXT_OF_VIOLENCE = 14
        MONITORING_SUB_REGION = 15
        CLIENT = 16

    started_at = models.DateTimeField(
        verbose_name=_('Started at'),
        blank=True,
        null=True,
    )
    completed_at = models.DateTimeField(
        verbose_name=_('Completed at'),
        blank=True,
        null=True,
    )
    download_type = enum.EnumField(
        DOWNLOAD_TYPES,
        null=False,
        blank=False,
    )
    status = enum.EnumField(
        EXCEL_GENERATION_STATUS,
        default=EXCEL_GENERATION_STATUS.PENDING,
    )
    file = CachedFileField(
        verbose_name=_('Excel File'),
        blank=True,
        null=True,
        upload_to=excel_upload_to,
        max_length=2000,
    )
    file_size = models.IntegerField(
        verbose_name=_('File Size'),
        blank=True,
        null=True,
    )
    filters = JSONField(
        verbose_name=_('Filters'),
        blank=True,
        null=True,
    )

    def get_model_sheet_data_getter(self):
        mapper = {
            self.DOWNLOAD_TYPES.CRISIS: apps.get_model('crisis', 'Crisis'),
            self.DOWNLOAD_TYPES.EVENT: apps.get_model('event', 'Event'),
            self.DOWNLOAD_TYPES.COUNTRY: apps.get_model('country', 'Country'),
            self.DOWNLOAD_TYPES.ENTRY: apps.get_model('entry', 'Entry'),
            self.DOWNLOAD_TYPES.FIGURE: apps.get_model('entry', 'Figure'),
            self.DOWNLOAD_TYPES.ORGANIZATION: apps.get_model('organization', 'Organization'),
            self.DOWNLOAD_TYPES.CONTACT: apps.get_model('contact', 'Contact'),
            self.DOWNLOAD_TYPES.REPORT: apps.get_model('report', 'Report'),
            self.DOWNLOAD_TYPES.ACTOR: apps.get_model('event', 'Actor'),
            self.DOWNLOAD_TYPES.INDIVIDUAL_REPORT: apps.get_model('report', 'Report'),
            self.DOWNLOAD_TYPES.TRACKING_DATA: apps.get_model('contrib', 'ClientTrackInfo'),
            self.DOWNLOAD_TYPES.PARKING_LOT: apps.get_model('parking_lot', 'ParkedItem'),
            self.DOWNLOAD_TYPES.FIGURE_TAG: apps.get_model('entry', 'FigureTag'),
            self.DOWNLOAD_TYPES.USER: apps.get_model('users', 'User'),
            self.DOWNLOAD_TYPES.CONTEXT_OF_VIOLENCE: apps.get_model('event', 'ContextOfViolence'),
            self.DOWNLOAD_TYPES.MONITORING_SUB_REGION: apps.get_model('country', 'MonitoringSubRegion'),
            self.DOWNLOAD_TYPES.CLIENT: apps.get_model('contrib', 'Client'),
        }
        model = mapper.get(self.download_type)
        if not model:
            raise AttributeError(f'Excel mapper cannot find model={model.name} in mapping.')
        if not hasattr(model, 'get_excel_sheets_data'):
            raise AttributeError(f'Excel sheet data getter missing for {model.name}')
        return model.get_excel_sheets_data

    def trigger_excel_generation(self, request, model_instance_id=None):
        '''
        This should trigger the excel file generation based on the
        given request. Filters are preserved within the instance.

        Is called by serializer.create method
        '''
        from apps.contrib.tasks import generate_excel_file

        transaction.on_commit(lambda: generate_excel_file.delay(
            self.pk, request.user.id, model_instance_id=model_instance_id
        ))


class Client(MetaInformationAbstractModel):
    """

    This class represents a Client in the application. It inherits from the MetaInformationAbstractModel class.

    Attributes:
        USE_CASE_TYPES (enum.Enum): Enum class representing the different types of use cases for a client.
            ANTICIPATORY_ACTION (int): Anticipatory Action use case type.
            RESPONSE (int): Response use case type.
            PREVENTION (int): Prevention use case type.
            RESEARCH_DATA_ANALYSIS (int): Research / Data analysis use case type.
            MODELLING_FORECASTING (int): Modelling / Data science project / forecasting use case type.
            DATA_SHARING_EXTERNAL_REPOSITORIES (int): Data Sharing and External Repositories Usage use case type.
            OTHER (int): Other use case type.
            __labels__ (dict): A dictionary representing the labels for each use case type.

        name (str): The name of the client.
        code (str): The code of the client.
        acronym (str): The acronym of the client.
        contact_name (str): The name of the contact person for the client.
        contact_email (str): The email address of the contact person for the client.
        contact_website (str): The website of the client.
        opted_out_of_emails (bool): Whether the client has opted out of receiving emails.
        use_cases (list): A list of use cases for the client.
        other_notes (str): Other notes related to the client.
        is_active (bool): Whether the client is active or not.

    Methods:
        __str__(): Returns a string representation of the client.

        get_excel_sheets_data(user_id: int, filters: dict) -> dict:
            Generates data for Excel sheets based on filters applied to the client queryset.

            Parameters:
                user_id (int): The ID of the user requesting the data.
                filters (dict): A dictionary of filters to apply to the client queryset.

            Returns:
                dict: A dictionary containing headers, data, formulae, and a transformer function
                      for Excel sheet generation.

        save(*args, **kwargs) -> None:
            Overrides the save method to update the client IDs in Redis after saving the client.

        delete(*args, **kwargs) -> None:
            Overrides the delete method to update the client IDs in Redis after deleting the client.

    """
    class USE_CASE_TYPES(enum.Enum):
        ANTICIPATORY_ACTION = 0
        RESPONSE = 1
        PREVENTION = 2
        RESEARCH_DATA_ANALYSIS = 3
        MODELLING_FORECASTING = 4
        DATA_SHARING_EXTERNAL_REPOSITORIES = 5
        OTHER = 6

        __labels__ = {
            ANTICIPATORY_ACTION: _("Anticipatory action"),
            RESPONSE: _("Response"),
            PREVENTION: _("Prevention"),
            RESEARCH_DATA_ANALYSIS: _("Research / Data analysis"),
            MODELLING_FORECASTING: _("Modelling/Data science project/forecasting"),
            DATA_SHARING_EXTERNAL_REPOSITORIES: _("Data Sharing and External Repositories Usage"),
            OTHER: _("Other"),
        }

    name = models.CharField(max_length=255)
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Client Code'),
        editable=False
    )
    acronym = models.CharField(
        max_length=255,
        verbose_name=_('Client Acronym'),
        blank=True,
        null=True
    )
    contact_name = models.CharField(
        max_length=255,
        verbose_name=_('Client Contact Name'),
        help_text=_('Client Contact Name: focal person'),
        blank=False,
        null=True
    )
    contact_email = models.EmailField(
        verbose_name=_('Client Contact Email'),
        help_text=_('Client Contact Email: email focal person'),
        blank=False,
        null=True
    )
    contact_website = models.URLField(
        verbose_name=_('Client Contact Website'),
        help_text=_('Client Contact Website: link to the website (IDMC application)'),
        blank=True,
        null=True
    )
    opted_out_of_emails = models.BooleanField(verbose_name='Opted out of receiving emails', default=False)
    use_cases = ArrayField(
        base_field=enum.EnumField(USE_CASE_TYPES, verbose_name=_('Use case')),
        null=False, default=list
    )
    other_notes = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(
        verbose_name=_('Is active?'),
        default=False
    )

    def __str__(self):
        return self.code

    @classmethod
    def get_excel_sheets_data(cls, user_id, filters):
        """
        Generates data for Excel sheets based on filters applied to the client queryset.

        Parameters:
            user_id: The ID of the user requesting the data.
            filters: A dictionary of filters to apply to the client queryset.

        Returns:
            A dictionary containing headers, data, formulae, and a transformer function for Excel sheet generation.
        """
        from apps.contrib.filters import ClientFilter

        class DummyRequest:
            def __init__(self, user):
                self.user = user

        headers = OrderedDict(
            id='ID',
            name='Name',
            code='Code',
            acronym='Acronym',
            contact_name='Contact Name',
            contact_email='Contact Email',
            contact_website='Website',
            use_cases='Use cases',
            other_notes='Notes',
            opted_out_of_emails='Opted out of receiving emails',
            created_by__full_name='Created By',
            created_at='Created At',
            last_modified_by__full_name='Last Modified By',
            modified_at='Modified At',
            is_active='Active',
        )

        data = ClientFilter(
            data=filters,
            request=DummyRequest(user=User.objects.get(id=user_id)),
        ).qs.order_by('created_at')

        def transformer(datum):
            transformed_use_cases = [
                getattr(Client.USE_CASE_TYPES.get(use_case), 'label', '')
                for use_case in datum['use_cases']
            ]
            return {
                **datum,
                'use_cases': EXTERNAL_ARRAY_SEPARATOR.join(transformed_use_cases),
                'is_active': 'Yes' if datum['is_active'] else 'No',
                'opted_out_of_emails': 'Yes' if datum['opted_out_of_emails'] else 'No'
            }

        return {
            'headers': headers,
            'data': data.values(*[header for header in headers.keys()]),
            'formulae': None,
            'transformer': transformer,
        }

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        client_ids = list(Client.objects.values_list('code', flat=True))
        set_client_ids_in_redis(client_ids)
        return instance

    def delete(self, *args, **kwargs):
        deleted = super().delete(*args, **kwargs)
        client_ids = list(Client.objects.values_list('code', flat=True))
        set_client_ids_in_redis(client_ids)
        return deleted


class ClientTrackInfo(models.Model):
    """
    A class representing the track information for a client.

    Attributes:
        client (ForeignKey): The foreign key to the Client model.
        api_type (CharField): The type of external API dump.
        requests_per_day (IntegerField): The number of requests per day for the API dump.
        tracked_date (DateField): The date when the track information was recorded.

    Meta:
        unique_together (tuple): The combination of client, api_type, and tracked_date must be unique.

    Methods:
        __str__(): Returns a string representation of the ClientTrackInfo object.
        get_excel_sheets_data(cls, user_id, filters): Retrieves data for generating Excel sheets.
        annotate_api_name(cls): Annotates the API names for the ClientTrackInfo objects.
    """
    from apps.entry.models import ExternalApiDump
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    api_type = models.CharField(
        max_length=40,
        choices=ExternalApiDump.ExternalApiType.choices,
    )
    requests_per_day = models.IntegerField()
    tracked_date = models.DateField()

    class Meta:
        unique_together = ('client', 'api_type', 'tracked_date')

    def __str__(self):
        return f'{self.client} - {self.tracked_date}'

    @classmethod
    def get_excel_sheets_data(cls, user_id, filters):
        from apps.entry.models import ExternalApiDump
        from .filters import ClientTrackInfoFilter

        class DummyRequest:
            def __init__(self, user):
                self.user = user

            def build_absolute_uri(self, url):
                # FIXME: implement this with concatenation
                return url

        headers = OrderedDict(
            client_name='Client name',
            client_code='Client code',
            api_name='API',
            api_type='API type',
            tracked_date='Date',
            requests_per_day='Requests',
        )

        dummy_request = DummyRequest(user=User.objects.get(id=user_id))

        data = ClientTrackInfoFilter(
            data=filters,
            request=dummy_request,
        ).qs.exclude(
            api_type='None',
        ).annotate(
            client_name=models.F('client__name'),
            client_code=models.F('client__code'),
            api_name=models.F('api_type'),
        ).order_by('-tracked_date')

        def transformer(datum):
            metadata = ExternalApiDump.API_TYPE_METADATA[datum['api_type']]
            return {
                **datum,
                'api_name': getattr(ExternalApiDump.ExternalApiType(datum['api_type']), 'label', ''),
                'api_example_request': metadata.get_example_request(dummy_request, datum['client_code']),
                'api_response_type': metadata.response_type,
                'api_usage': metadata.get_usage(dummy_request, datum['client_code']),
                'api_description': metadata.description,
            }
        return {
            'headers': OrderedDict(
                **headers,
                api_example_request='API Example Request',
                api_response_type='API Response',
                api_usage='API Usage',
                api_description='API Description',
            ),
            'data': data.values(*[header for header in headers.keys()]),
            'formulae': None,
            'transformer': transformer,
        }

    @classmethod
    def annotate_api_name(cls):
        from apps.entry.models import ExternalApiDump
        return {
            'api_name': models.Case(
                *[
                    models.When(
                        api_type=enum_obj.value,
                        then=models.Value(enum_obj.label, output_field=models.CharField())
                    ) for enum_obj in ExternalApiDump.ExternalApiType
                ]
            )
        }


class BulkApiOperation(models.Model):
    """
    Class representing a bulk operation.

    Attributes:
        BULK_OPERATION_ACTION (enum.Enum): Enum class defining the possible actions for a bulk operation.
        BULK_OPERATION_STATUS (enum.Enum): Enum class defining the possible status values for a bulk operation.
        QUERYSET_COUNT_THRESHOLD (int): Threshold count for a queryset.
        WAIT_TIME_THRESHOLD_IN_MINUTES (int): Threshold time for waiting in minutes.
        created_at (models.DateTimeField): DateTimeField representing the creation time of the bulk operation.
        created_by (models.ForeignKey): ForeignKey representing the user who created the bulk operation.
        started_at (models.DateTimeField): DateTimeField representing the start time of the bulk operation.
        completed_at (models.DateTimeField): DateTimeField representing the completion time of the bulk operation.
        action (enum.EnumField): EnumField representing the action of the bulk operation.
        filters (JSONField): JSONField representing the filters for the bulk operation.
        payload (JSONField): JSONField representing the operation payload of the bulk operation.
        status (enum.EnumField): EnumField representing the status of the bulk operation.
        success_count (models.PositiveIntegerField): PositiveIntegerField representing the count of successful operations.
        success_list (models.JSONField): JSONField representing the list of successful operations.
        failure_count (models.PositiveIntegerField): PositiveIntegerField representing the count of failed operations.
        failure_list (models.JSONField): JSONField representing the list of failed operations.
        snapshot (CachedFileField): CachedFileField representing the existing data snapshot.

    Methods:
        __str__(): Returns a string representation of the bulk operation.
        update_status(status: BULK_OPERATION_STATUS, commit=True): Updates the status of the bulk operation.

    """
    class BULK_OPERATION_ACTION(enum.Enum):
        FIGURE_ROLE = 0
        FIGURE_EVENT = 1

        __labels__ = {
            FIGURE_ROLE: _("Figure Role"),
            FIGURE_EVENT: _("Figure Event"),
        }

    class BULK_OPERATION_STATUS(enum.Enum):
        PENDING = 0
        IN_PROGRESS = 1
        COMPLETED = 2
        FAILED = 3
        KILLED = 4

    QUERYSET_COUNT_THRESHOLD = 100
    WAIT_TIME_THRESHOLD_IN_MINUTES = 5

    created_at = models.DateTimeField(verbose_name=_('Created At'), auto_now_add=True)
    created_by = models.ForeignKey(
        'users.User', verbose_name=_('Created By'),
        related_name='created_%(class)s', on_delete=models.PROTECT,
    )
    # Runtime information
    started_at = models.DateTimeField(verbose_name=_('Started At'), null=True, blank=True)
    completed_at = models.DateTimeField(verbose_name=_('Completed At'), null=True, blank=True)

    # User provided fields
    action = enum.EnumField(enum=BULK_OPERATION_ACTION)
    filters = JSONField(
        verbose_name=_('Filters'),
        blank=True,
        null=True,
    )
    payload = JSONField(
        verbose_name=_('Operation Payload'),
        blank=True,
        null=True,
    )

    # System generated fields
    status = enum.EnumField(enum=BULK_OPERATION_STATUS, default=BULK_OPERATION_STATUS.PENDING)
    # Output from operation
    success_count = models.PositiveIntegerField(blank=True, null=True)
    success_list = models.JSONField(default=list)
    failure_count = models.PositiveIntegerField(blank=True, null=True)
    failure_list = models.JSONField(default=list)
    snapshot = CachedFileField(
        verbose_name=_('Existing data snapshot'),
        blank=True,
        null=True,
        upload_to=bulk_operation_snapshot,
        max_length=2000,
    )

    get_action_display: typing.Callable
    get_status_display: typing.Callable

    def __str__(self):
        return f'{self.get_action_display()}-{self.pk}'

    def update_status(self, status: BULK_OPERATION_STATUS, commit=True):
        # If status has changed
        if status != self.status:
            if status == self.BULK_OPERATION_STATUS.IN_PROGRESS:
                self.started_at = timezone.now()
            elif status in [
                self.BULK_OPERATION_STATUS.COMPLETED,
                self.BULK_OPERATION_STATUS.FAILED,
                self.BULK_OPERATION_STATUS.KILLED,
            ]:
                self.completed_at = timezone.now()
        self.status = status
        if commit:
            self.save(update_fields=('status',))

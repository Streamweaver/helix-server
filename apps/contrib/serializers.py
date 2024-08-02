import magic
import random
import string
from datetime import timedelta
from django.utils import timezone

from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext
from rest_framework import serializers

from utils.serializers import IntegerIDField
from apps.entry.tasks import PDF_TASK_TIMEOUT
from apps.contrib.models import (
    Attachment,
    Client,
    ExcelDownload,
    SourcePreview,
)


class MetaInformationSerializerMixin(serializers.Serializer):
    """
    A mixin class for including meta information fields in a serializer.

    Attributes:
        created_at (DateTimeField): A read-only field representing the timestamp of creation.
        modified_at (DateTimeField): A read-only field representing the timestamp of the last modification.
        created_by (PrimaryKeyRelatedField): A read-only field representing the user who created the instance.
        last_modified_by (PrimaryKeyRelatedField): A read-only field representing the user who last modified the
        instance.

    Methods:
        validate(attrs: dict) -> dict:
            Validates the attribute dictionary and adds the appropriate meta information based on the instance.

            Parameters:
                attrs (dict): The attribute dictionary to be validated.

            Returns:
                dict: The validated attribute dictionary with meta information added.

    """
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    last_modified_by = serializers.PrimaryKeyRelatedField(read_only=True)

    def validate(self, attrs) -> dict:
        attrs = super().validate(attrs)
        if self.instance is None:
            attrs.update({
                'created_by': self.context['request'].user
            })
        else:
            attrs.update({
                'last_modified_by': self.context['request'].user
            })
        return attrs


class AttachmentSerializer(serializers.ModelSerializer):
    """

    AttachmentSerializer

    This class is responsible for serializing/deserializing Attachment objects.

    Usage:
        You can instantiate the AttachmentSerializer class and use it to validate and serialize Attachment objects.

    Attributes:
        - model (required): The model class to be used for serialization/deserialization.
        - fields (optional): The fields to be included in the serialized output. If not specified, all fields will be
        included.

    Methods:
        - _validate_file_size(file_content)
            Description:
                This method is used to validate the size of the file content.
            Parameters:
                - file_content: The file content to be validated.
            Raises:
                - serializers.ValidationError: If the file size exceeds the maximum file size allowed.

        - _validate_mimetype(mimetype)
            Description:
                This method is used to validate the mimetype of the file.
            Parameters:
                - mimetype: The mimetype to be validated.
            Raises:
                - serializers.ValidationError: If the mimetype is not allowed.

        - validate(attrs) -> dict
            Description:
                This method is used to validate the attributes of the Attachment object.
            Parameters:
                - attrs: The attributes to be validated.
            Returns:
                - dict: The validated attributes.
            Raises:
                - serializers.ValidationError: If any of the attributes fail validation.

    """
    class Meta:
        model = Attachment
        fields = '__all__'

    def _validate_file_size(self, file_content):
        if file_content.size > Attachment.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                gettext('Filesize should be less than: %s. Current is: %s') % (
                    filesizeformat(Attachment.MAX_FILE_SIZE),
                    filesizeformat(file_content.size),
                )
            )

    def _validate_mimetype(self, mimetype):
        if mimetype not in Attachment.ALLOWED_MIMETYPES:
            raise serializers.ValidationError(gettext('Filetype not allowed: %s') % mimetype)

    def validate(self, attrs) -> dict:
        attachment = attrs['attachment']
        self._validate_file_size(attachment)
        byte_stream = attachment.file.read()
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
            attrs['mimetype'] = m.id_buffer(byte_stream)
            self._validate_mimetype(attrs['mimetype'])
        with magic.Magic(flags=magic.MAGIC_MIME_ENCODING) as m:
            attrs['encoding'] = m.id_buffer(byte_stream)
        with magic.Magic() as m:
            attrs['filetype_detail'] = m.id_buffer(byte_stream)
        return attrs


class SourcePreviewSerializer(MetaInformationSerializerMixin,
                              serializers.ModelSerializer):
    """
    The SourcePreviewSerializer class is responsible for serializing and deserializing instances of SourcePreview model
    into JSON and vice versa.

    The class inherits from the MetaInformationSerializerMixin and the serializers.ModelSerializer classes.

    Attributes:
        - model: The model attribute is set to the SourcePreview model.
        - fields: The fields attribute is set to '__all__', which means that all fields of the SourcePreview model will
        be serialized.

    Methods:
        - create(self, validated_data): This method is called when creating a new SourcePreview instance. It takes the
        validated data as input and returns a new SourcePreview instance. It first checks if there is an existing
        SourcePreview instance with the same url, created_by, and status equal to 'IN_PROGRESS' within the specified
        timeout. If such an instance exists, it returns the first matching instance. Otherwise, it calls the get_pdf
        method of the SourcePreview model to generate a PDF preview for the validated data and returns the result.

        - update(self, instance, validated_data): This method is called when updating an existing SourcePreview
        instance. It takes the existing instance and the validated data as input and returns the updated instance. It
        calls the get_pdf method of the SourcePreview model to generate a PDF preview for the validated data, using the
        existing instance if provided.

    Note: The SourcePreview model and the MetaInformationSerializerMixin class are not defined in the given code, so it
    is assumed that they are imported from somewhere else.
    """
    class Meta:
        model = SourcePreview
        fields = '__all__'

    def create(self, validated_data):
        filter_params = dict(
            url=validated_data['url'],
            created_by=validated_data['created_by'],
            status=SourcePreview.PREVIEW_STATUS.IN_PROGRESS,
            created_at__gte=timezone.now() - timedelta(seconds=PDF_TASK_TIMEOUT)
        )

        if SourcePreview.objects.filter(
            **filter_params
        ).exists():
            return SourcePreview.objects.filter(
                **filter_params
            ).first()
        return SourcePreview.get_pdf(validated_data)

    def update(self, instance, validated_data):
        return SourcePreview.get_pdf(validated_data, instance=instance)


class ExcelDownloadSerializer(MetaInformationSerializerMixin,
                              serializers.ModelSerializer):
    """
    ExcelDownloadSerializer class is responsible for serializing and deserializing ExcelDownload objects.

    Attributes:
    - model_instance_id (serializers.IntegerField, optional): ID of the model instance associated with the ExcelDownload
    object.

    Meta:
    - model (ExcelDownload): The model class associated with the serializer.
    - fields (str): A string representing the fields to include in the serialized output. In this case, all fields are
    included.

    Methods:
    - validate_concurrent_downloads(attrs: dict) -> None: Validates the number of concurrent downloads for the current
    user. Raises a ValidationError if the limit is exceeded.
    - validate(attrs: dict) -> dict: Validates the input data. Calls the superclass validate method and performs
    additional validation for concurrent downloads.
    - create(validated_data) -> ExcelDownload: Creates a new ExcelDownload instance. Triggers the generation of the
    Excel file and returns the instance.

    Note: This class inherits from the MetaInformationSerializerMixin and serializers.ModelSerializer.
    """
    model_instance_id = serializers.IntegerField(required=False)

    class Meta:
        model = ExcelDownload
        fields = '__all__'

    def validate_concurrent_downloads(self, attrs: dict) -> None:
        if ExcelDownload.objects.filter(
            status__in=[
                ExcelDownload.EXCEL_GENERATION_STATUS.PENDING,
                ExcelDownload.EXCEL_GENERATION_STATUS.IN_PROGRESS
            ],
            created_by=self.context['request'].user,
        ).count() >= settings.EXCEL_EXPORT_CONCURRENT_DOWNLOAD_LIMIT:
            raise serializers.ValidationError(gettext(
                'Only %s excel export(s) is allowed at a time'
            ) % settings.EXCEL_EXPORT_CONCURRENT_DOWNLOAD_LIMIT, code='limited-at-a-time')

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        self.validate_concurrent_downloads(attrs)
        return attrs

    def create(self, validated_data):
        model_instance_id = validated_data.pop("model_instance_id", None)
        instance = super().create(validated_data)
        instance.trigger_excel_generation(self.context['request'], model_instance_id=model_instance_id)
        return instance


class UpdateSerializerMixin:
    """

    UpdateSerializerMixin

    Mixin class for patch updates in serializers.

    Attributes:
        - fields (dict): A dictionary containing the fields of the serializer.

    Methods:
        - __init__(*args, **kwargs): Initializes the mixin.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # all updates will be a patch update
        for name in self.fields:
            self.fields[name].required = False
        self.fields['id'].required = True


class ClientSerializer(
    MetaInformationSerializerMixin,
    serializers.ModelSerializer
):
    """
    Serializer for the Client model.

    Fields:
    - contact_name (CharField): The name of the contact person for the client. Required.
    - contact_email (EmailField): The email address of the contact person for the client. Required.
    - use_cases (ListField): The list of use cases for the client. Required. Each use case should be one of the choices
    in Client.USE_CASE_TYPES.
    - id (IntegerField): The ID of the client.
    - name (CharField): The name of the client.
    - is_active (BooleanField): Indicates whether the client is active or not.
    - acronym (CharField): The acronym of the client.
    - contact_website (CharField): The website of the contact person for the client.
    - other_notes (CharField): Additional notes about the client.
    - opted_out_of_emails (BooleanField): Indicates whether the client has opted out of receiving emails.

    Meta:
    - model (Client): The Client model.
    - fields (Tuple): The fields to be included in the serialized output.

    Methods:
    - validate(self, attrs): Custom validation method. Ensures 'other_notes' is provided when 'Other' is selected in
    use_cases.
    - create(self, validated_data): Creates a new Client instance. Generates a unique client code before creating the
    instance.
    - _generate_unique_client_code(self, code_length=16, max_attempts=5): Generates a unique client code consisting of
    uppercase letters and digits.

    """
    contact_name = serializers.CharField(required=True)
    contact_email = serializers.EmailField(required=True)
    use_cases = serializers.ListField(
        child=serializers.ChoiceField(choices=Client.USE_CASE_TYPES.choices()),
        required=True,
    )

    class Meta:
        model = Client
        fields = (
            'id',
            'name',
            'is_active',
            'acronym',
            'contact_name',
            'contact_email',
            'contact_website',
            'use_cases',
            'other_notes',
            'opted_out_of_emails',
        )

    def validate(self, attrs):
        """
        Ensures 'other_notes' is provided when 'Other' is selected in use_cases.
        """
        attrs = super().validate(attrs)
        use_cases = attrs.get('use_cases', [])
        if Client.USE_CASE_TYPES.OTHER.value in use_cases and not attrs.get('other_notes'):
            raise serializers.ValidationError({"other_notes": "Required when 'Other' is selected in use cases."})
        return attrs

    def create(self, validated_data):
        """
        Generates a unique client code before creating a new Client instance.
        """
        validated_data['code'] = self._generate_unique_client_code()
        return super().create(validated_data)

    def _generate_unique_client_code(self, code_length=16, max_attempts=5):
        """
        Generates a unique client code consisting of uppercase letters and digits.

        This method attempts to generate a unique code by combining random uppercase letters and digits.
        It checks the uniqueness of the generated code against existing client codes in the database.
        If a unique code is found within the specified number of attempts, it is returned.
        Otherwise, an exception is raised indicating the failure to generate a unique code.

        Parameters:
        - code_length (int): The length of the code to be generated. Defaults to 16.
        - max_attempts (int): The maximum number of attempts to generate a unique code. Defaults to 5.

        Returns:
        - str: A unique client code.

        Raises:
        - Exception: If a unique code cannot be generated after the specified number of attempts.
        """
        for _ in range(max_attempts):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=code_length))
            if not Client.objects.filter(code=code).exists():
                return code
        raise Exception("Failed to generate a unique code after several attempts.")


class ClientUpdateSerializer(UpdateSerializerMixin, ClientSerializer):
    """
    Client Update Serializer class.

    This class is used to serialize and validate data for updating a client.

    Attributes:
        id (IntegerIDField): The client ID field.

    """
    id = IntegerIDField(required=True)

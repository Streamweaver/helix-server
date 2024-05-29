from collections import OrderedDict

from django.utils.translation import gettext
from rest_framework import serializers

from apps.contextualupdate.models import ContextualUpdate
from apps.contrib.serializers import MetaInformationSerializerMixin


class ContextualUpdateSerializer(MetaInformationSerializerMixin,
                                 serializers.ModelSerializer):
    """
    The ContextualUpdateSerializer class is a serializer class used for serializing and deserializing ContextualUpdate objects. It is a subclass of the MetaInformationSerializerMixin and the ModelSerializer classes provided by the Django REST Framework.

    Attributes:
    - model: The model that this serializer class is associated with (ContextualUpdate).
    - fields: A string or a list/tuple of field names to be included when serializing and deserializing objects. In this case, it includes all fields using the '__all__' shortcut.

    Methods:
    - validate_url_document(self, attrs): This method is used to validate the 'url' and 'document' fields in the input data during the deserialization process. If either of these fields is missing, it raises a serializers.ValidationError with appropriate error messages.

    - validate(self, attrs) -> dict: This method is called during the validation process and is responsible for performing any additional validation on the input data. It calls the superclass's validate method first and then calls the validate_url_document method to validate the 'url' and 'document' fields. It returns a dictionary of validated data.

    Example usage:
        serializer = ContextualUpdateSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            # Process the validated data
        else:
            errors = serializer.errors
            # Handle validation errors
    """
    class Meta:
        model = ContextualUpdate
        fields = '__all__'

    def validate_url_document(self, attrs):
        if not self.instance:
            errors = OrderedDict()
            if not attrs.get('url') and not attrs.get('document'):
                errors['url'] = gettext('Please fill the URL or upload a document.')
                errors['document'] = gettext('Please fill the URL or upload a document.')
                raise serializers.ValidationError(errors)

    def validate(self, attrs) -> dict:
        attrs = super(ContextualUpdateSerializer, self).validate(attrs)
        self.validate_url_document(attrs)
        return attrs

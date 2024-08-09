from rest_framework import serializers

from apps.organization.models import Organization, OrganizationKind
from apps.contrib.serializers import UpdateSerializerMixin, IntegerIDField, MetaInformationSerializerMixin


class OrganizationKindSerializer(serializers.ModelSerializer, MetaInformationSerializerMixin):
    """

    The OrganizationKindSerializer class is responsible for serializing and deserializing instances of the
    OrganizationKind model. It is a subclass of the ModelSerializer class provided by the Django REST Framework.

    This serializer class includes the MetaInformationSerializerMixin, which provides additional meta information
    related to the serializer.

    Usage:
    ------
    To use the OrganizationKindSerializer, you need to import it into your project and create an instance of it in your
    view or serializer.

    Example usage:

        from rest_framework import serializers
        from your_app.models import OrganizationKind
        from your_app.serializers.mixins import MetaInformationSerializerMixin

        class OrganizationKindSerializer(serializers.ModelSerializer, MetaInformationSerializerMixin):
            class Meta:
                model = OrganizationKind
                fields = '__all__'

            # Include any additional methods or customizations here

    Serializer Fields:
    -----------------
    The OrganizationKindSerializer class automatically generates fields based on the model fields defined in the
    OrganizationKind model. It includes the following fields:

    - id: The unique identifier of the OrganizationKind.
    - name: The name of the OrganizationKind.
    - ... (Any other fields defined in the OrganizationKind model)

    Meta Class:
    -----------
    The Meta class within the OrganizationKindSerializer defines the model and fields to be used by the serializer. In
    this case, the model is set to OrganizationKind, and the fields are set to '__all__', which means all fields defined
    in the model will be included in the serialized output.

    Additional Methods:
    -------------------
    You can include additional methods or customizations within the OrganizationKindSerializer class as needed for your
    project.

    Please refer to the Django REST Framework documentation for more information on serializers:
    https://www.django-rest-framework.org/api-guide/serializers/

    """
    class Meta:
        model = OrganizationKind
        fields = '__all__'


class OrganizationKindUpdateSerializer(UpdateSerializerMixin, OrganizationKindSerializer):
    """
    Serializer class for updating an organization kind.

    This class inherits from `UpdateSerializerMixin` and `OrganizationKindSerializer`.

    Attributes:
        id (int): The ID of the organization kind to be updated.

    """
    id = IntegerIDField(required=True)


class OrganizationSerializer(serializers.ModelSerializer, MetaInformationSerializerMixin):
    """
    This class is responsible for serializing and deserializing Organization objects.

    Attributes:
        model (Model): The Organization model to be serialized/deserialized.
        fields (List[str]): The fields to include in the serialized representation. If set to '__all__', all fields will
        be included.
        extra_kwargs (Dict[str, Dict[str, Any]]): Extra keyword arguments for specific fields.

    Methods:
        to_representation(instance: Model) -> OrderedDict:
            Converts the given Organization instance into a serialized representation.

        to_internal_value(data: Dict[str, Any]) -> Dict[str, Any]:
            Converts the serialized data into a validated internal value dictionary.

        create(validated_data: Dict[str, Any]) -> Model:
            Creates and returns a new Organization instance using the given validated data.

        update(instance: Model, validated_data: Dict[str, Any]) -> Model:
            Updates and returns an existing Organization instance using the given validated data.

    """
    class Meta:
        model = Organization
        fields = '__all__'
        extra_kwargs = {
            'countries': {
                'required': False
            },
        }


class OrganizationUpdateSerializer(UpdateSerializerMixin, OrganizationSerializer, MetaInformationSerializerMixin):
    """
    Serializer class for updating an organization.

    Attributes:
        id (int): The unique identifier of the organization to be updated.

    """
    id = IntegerIDField(required=True)

from django.utils.translation import gettext
from rest_framework import serializers

from helix.settings import RESOURCE_NUMBER, RESOURCEGROUP_NUMBER

from apps.resource.models import Resource, ResourceGroup

from apps.contrib.serializers import (
    MetaInformationSerializerMixin,
    UpdateSerializerMixin,
    IntegerIDField,
)


class ResourceSerializer(MetaInformationSerializerMixin, serializers.ModelSerializer):
    """

    A class that provides resource serialization functionality.

    This class inherits from `MetaInformationSerializerMixin` and `serializers.ModelSerializer`.

    Attributes:
        model (class): The Django model class associated with the serializer.
        fields (str or list, optional): The fields to include in the serialized representation. Defaults to '__all__'.

    Methods:
        validate_group(group)
            Validates the group field of the resource.

            Args:
                group (Group): The group to validate.

            Returns:
                Group: The validated group.

            Raises:
                serializers.ValidationError: If the group does not exist.

        validate(attrs) -> dict
            Validates the resource attributes.

            Args:
                attrs (dict): The attributes to validate.

            Returns:
                dict: The validated attributes.

            Raises:
                serializers.ValidationError: If the number of resources created by the request user exceeds
                RESOURCE_NUMBER.
    """
    class Meta:
        model = Resource
        fields = '__all__'

    def validate_group(self, group):
        if group and group.created_by != self.context['request'].user:
            raise serializers.ValidationError(gettext('Group does not exist.'))
        return group

    def validate(self, attrs) -> dict:
        if self.instance is None and Resource.objects.filter(
            created_by=self.context['request'].user
        ).count() >= RESOURCE_NUMBER:
            raise serializers.ValidationError(gettext('Can only create %s resources') % RESOURCE_NUMBER)
        return super().validate(attrs)


class ResourceUpdateSerializer(UpdateSerializerMixin, ResourceSerializer):
    """
    ResourceUpdateSerializer

    A class that handles the serialization and deserialization of resource update data.

    Attributes:
        id (int): The ID of the resource that is being updated. Required.

    """
    id = IntegerIDField(required=True)


class ResourceGroupSerializer(MetaInformationSerializerMixin, serializers.ModelSerializer):
    """
    ResourceGroupSerializer Documentation

    This class is a serializer for the ResourceGroup model.

    Attributes:
        Meta: A nested class that defines the metadata of the serializer.
            - model: The model class that this serializer is based on.
            - fields: The fields to include in the serialized representation.
        instance: An instance of the ResourceGroup model.
        context: A dictionary containing additional context provided to the serializer.

    Methods:
        validate(attrs) -> dict:
            This method is used to validate the attributes of the serializer object.
            It checks if the instance is None and if the number of resource groups created by the user is equal to or
            greater than a constant value.
            If the conditions are met, it raises a validation error.
            Otherwise, it calls the validate() method of the superclass and returns the validated attributes.

    """
    class Meta:
        model = ResourceGroup
        fields = '__all__'

    def validate(self, attrs) -> dict:
        if self.instance is None and ResourceGroup.objects.filter(
            created_by=self.context['request'].user
        ).count() >= RESOURCEGROUP_NUMBER:
            raise serializers.ValidationError(gettext('Can only create %s resource groups') % RESOURCEGROUP_NUMBER)
        return super().validate(attrs)


class ResourceGroupUpdateSerializer(UpdateSerializerMixin, ResourceGroupSerializer):
    """
    Serializer class for updating a resource group.

    Inherits from UpdateSerializerMixin and ResourceGroupSerializer.

    Attributes:
        id (IntegerField): The ID of the resource group to be updated.

    """
    id = IntegerIDField(required=True)

from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets


from apps.parking_lot.models import ParkedItem
from apps.parking_lot.serializers import ParkedItemSerializer


class CreateListMixin():
    """
    Class: CreateListMixin

    This class provides a mixin for Django Rest Framework viewsets that allows the automatic detection of list data in
    the request payload. When the data is a list, it sets the 'many' argument of the serializer to True.

    Methods:
    - get_serializer(*args, **kwargs): Returns the serializer instance with the 'many' argument set to True if the data
    is a list.

    Usage:

    1. Inherit the CreateListMixin class in your Django Rest Framework viewset:

    class MyViewSet(CreateListMixin, viewsets.ModelViewSet):
        ...

    2. Override the get_queryset() method in your viewset to customize the queryset for your view.

    3. Use the 'get_serializer' method to obtain the serializer instance with the 'many' argument set to True if the
    data is a list.

    Example:

    class MyViewSet(CreateListMixin, viewsets.ModelViewSet):

        def get_queryset(self):
            ...

        def create(self, request, *args, **kwargs):
            serializer = self.get_serializer(data=request.data)
            ...
    """
    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)


class ParkedItemViewSet(CreateListMixin, viewsets.ModelViewSet):
    """
    A view set for managing parked items.

    This class inherits from `CreateListMixin` and `viewsets.ModelViewSet` to handle the CRUD operations
    on the `ParkedItem` model.

    Attributes:
        queryset (QuerySet): The queryset of `ParkedItem` objects to be retrieved or modified.
        serializer_class (Serializer): The serializer class used for serializing and deserializing `ParkedItem` objects.
        permission_classes (list): A list of permission classes that controls access to the view set.
        pagination_class (NoneType): The pagination class used for paginating the queryset. Set to `None` to disable
        pagination.
        swagger_schema (NoneType): The schema used for OpenAPI documentation.

    """
    queryset = ParkedItem.objects.all()
    serializer_class = ParkedItemSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    swagger_schema = None

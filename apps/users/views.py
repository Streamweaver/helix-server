from rest_framework.views import APIView
from rest_framework.filters import (
    SearchFilter
)
from rest_framework.permissions import IsAuthenticated
from rest_framework import response, viewsets, mixins

from apps.users.models import User
from apps.users.serializers import UserSerializer


class UserViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    UserViewSet Class

    This class represents the viewset for the User model.

    Attributes:
        serializer_class (class): The serializer class to be used for serializing and deserializing User instances.
        permission_classes (list): The list of permission classes to be used for authentication and authorization.
        filter_backends (list): The list of filter backends to be used for filtering the queryset.
        search_fields (list): The list of fields to be used for searching the queryset.
        pagination_class (class): The pagination class to be used for paginating the queryset.
        swagger_schema (NoneType): The schema to be used for generating the Swagger documentation.

    Methods:
        get_queryset(): Returns the queryset of all User instances.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [SearchFilter]
    search_fields = ['username', 'email']
    # NOTE: In IDU Map currently none paginated api is used, Set pagination simultaneously
    pagination_class = None
    swagger_schema = None

    def get_queryset(self):
        return User.objects.all()


class MeView(APIView):
    """
    A class that represents the MeView.

    Attributes:
    - serializer_class: The serializer class to be used for the User model.
    - permission_classes: The list of permission classes for the MeView.
    - swagger_schema: The schema for the MeView in the Swagger documentation.

    Methods:
    - get: Handles the HTTP GET request and returns the serialized data of the authenticated user.

    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, ]
    swagger_schema = None

    def get(self, request):
        serializer = UserSerializer(request.user)
        return response.Response(serializer.data)

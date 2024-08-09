import graphene
from django.utils.translation import gettext

from apps.crisis.enums import CrisisTypeGrapheneEnum
from apps.contextualupdate.models import ContextualUpdate
from apps.contextualupdate.schema import ContextualUpdateType
from apps.contextualupdate.serializers import ContextualUpdateSerializer
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker


class ContextualUpdateInputMixin:
    """
    A mixin class for updating contextual information in an input object.

    Attributes:
        preview (graphene.ID): The ID of the preview.
        article_title (graphene.String): The title of the article.
        sources (list): The list of source IDs.
        publishers (list): The list of publisher IDs.
        publish_date (graphene.DateTime): The publish date of the article.
        source_excerpt (graphene.String): The excerpt of the article source.
        idmc_analysis (graphene.String): The IDMC analysis for the article.
        is_confidential (graphene.Boolean): Flag indicating if the article is confidential.
        tags (list): The list of tag IDs.
        countries (list): The list of country IDs.
        crisis_types (list): The list of crisis types enumerated as CrisisTypeGrapheneEnum.
    """
    preview = graphene.ID()
    article_title = graphene.String()
    sources = graphene.List(graphene.NonNull(graphene.ID))
    publishers = graphene.List(graphene.NonNull(graphene.ID))
    publish_date = graphene.DateTime()
    source_excerpt = graphene.String()
    idmc_analysis = graphene.String()
    is_confidential = graphene.Boolean()
    tags = graphene.List(graphene.NonNull(graphene.ID))
    countries = graphene.List(graphene.NonNull(graphene.ID))
    crisis_types = graphene.List(graphene.NonNull(CrisisTypeGrapheneEnum))


class ContextualUpdateCreateInputType(ContextualUpdateInputMixin,
                                      graphene.InputObjectType):
    """A class representing the input type for creating a contextual update.

    This class inherits from ContextualUpdateInputMixin and graphene.InputObjectType.
    It provides fields for the URL and document ID of the update.

    Attributes:
        url (str): The URL of the update.
        document (str): The document ID associated with the update.

    """
    url = graphene.String()
    document = graphene.ID()


class ContextualUpdateUpdateInputType(ContextualUpdateInputMixin,
                                      graphene.InputObjectType):
    """
    ContextualUpdateUpdateInputType is a class that represents the input data for updating a contextual update.

    Attributes:
        id (graphene.ID): The unique identifier of the contextual update to update.

    """
    id = graphene.ID(required=True)


class CreateContextualUpdate(graphene.Mutation):
    """
    This class represents a GraphQL mutation for creating a contextual update.

    Attributes:
        data (ContextualUpdateCreateInputType): The input data for creating a contextual update.
        errors (List[CustomErrorType]): The list of errors that occurred during the mutation.
        ok (bool): Indicates whether the mutation was successful.
        result (ContextualUpdateType): The created contextual update.

    Methods:
        mutate(root, info, data): Static method for executing the mutation.

    """
    class Arguments:
        data = ContextualUpdateCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ContextualUpdateType)

    @staticmethod
    @permission_checker(['contextualupdate.add_contextualupdate'])
    def mutate(root, info, data):
        serializer = ContextualUpdateSerializer(data=data, context=dict(request=info.context.request))
        if errors := mutation_is_not_valid(serializer):
            return CreateContextualUpdate(errors=errors, ok=False)
        instance = serializer.save()
        return CreateContextualUpdate(result=instance, errors=None, ok=True)


class UpdateContextualUpdate(graphene.Mutation):
    """
    Class: UpdateContextualUpdate

    This class represents a graphene mutation for updating a ContextualUpdate object.

    Attributes:
    - data: Required argument of type ContextualUpdateUpdateInputType. Represents the updated data for the
    ContextualUpdate object.
    - errors: List of CustomErrorType objects. Contains any errors that occur during the mutation process.
    - ok: Boolean value indicating the success or failure of the mutation.
    - result: Field of type ContextualUpdateType. Represents the updated ContextualUpdate object.

    Methods:
    - mutate(root, info, data): Static method decorated with the @permission_checker decorator. Performs the mutation
    operation by updating the ContextualUpdate object with the provided data. Returns an instance of
    UpdateContextualUpdate with the updated object, any errors that occur, and the success status of the mutation.

    """
    class Arguments:
        data = ContextualUpdateUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ContextualUpdateType)

    @staticmethod
    @permission_checker(['contextualupdate.change_contextualupdate'])
    def mutate(root, info, data):
        try:
            instance = ContextualUpdate.objects.get(id=data['id'])
        except ContextualUpdate.DoesNotExist:
            return UpdateContextualUpdate(errors=[
                dict(field='nonFieldErrors', messages=gettext('Contextual update does not exist.'))
            ])
        serializer = ContextualUpdateSerializer(instance=instance, data=data, partial=True,
                                                context=dict(request=info.context.request))
        if errors := mutation_is_not_valid(serializer):
            return UpdateContextualUpdate(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateContextualUpdate(result=instance, errors=None, ok=True)


class DeleteContextualUpdate(graphene.Mutation):
    """

    DeleteContextualUpdate - A class representing a GraphQL mutation to delete a contextual update.

    Args:
        id (graphene.ID): The ID of the contextual update to delete. (required)

    Attributes:
        errors (graphene.List[graphene.NonNull[CustomErrorType]]): A list of custom error types.
        ok (graphene.Boolean): A boolean indicating if the deletion was successful.
        result (graphene.Field[ContextualUpdateType]): The deleted contextual update.

    Methods:
        mutate(root, info, id) - A static method that executes the deletion of a contextual update.

    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ContextualUpdateType)

    @staticmethod
    @permission_checker(['contextualupdate.delete_contextualupdate'])
    def mutate(root, info, id):
        try:
            instance = ContextualUpdate.objects.get(id=id)
        except ContextualUpdate.DoesNotExist:
            return DeleteContextualUpdate(errors=[
                dict(field='nonFieldErrors', messages=gettext('Contextual update does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteContextualUpdate(result=instance, errors=None, ok=True)


class Mutation(object):
    """
    Class: Mutation

    Provides the following methods for performing contextual updates:

    1. create_contextual_update(): Creates a new contextual update.
    2. update_contextual_update(): Updates an existing contextual update.
    3. delete_contextual_update(): Deletes a contextual update.

    """
    create_contextual_update = CreateContextualUpdate.Field()
    update_contextual_update = UpdateContextualUpdate.Field()
    delete_contextual_update = DeleteContextualUpdate.Field()

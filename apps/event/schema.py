import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from utils.graphene.enums import EnumDescription
from apps.contrib.commons import DateAccuracyGrapheneEnum
from apps.crisis.enums import CrisisTypeGrapheneEnum
from apps.event.enums import (
    QaRecommendedFigureEnum,
    EventReviewStatusEnum,
    EventCodeTypeGrapheneEnum,
)
from apps.event.models import (
    Event,
    EventCode,
    Violence,
    ViolenceSubType,
    Actor,
    DisasterSubCategory,
    DisasterCategory,
    DisasterSubType,
    DisasterType,
    OsvSubType,
    ContextOfViolence,
    OtherSubType,
)
from apps.event.filters import (
    ActorFilter,
    EventFilter,
    DisasterSubTypeFilter,
    DisasterTypeFilter,
    DisasterCategoryFilter,
    DisasterSubCategoryFilter,
    OsvSubTypeFilter,
    OtherSubTypeFilter,
    ContextOfViolenceFilter,
    ViolenceFilter,
    ViolenceSubTypeFilter,
)
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount


class ViolenceSubObjectType(DjangoObjectType):
    """

    This class is a subclass of DjangoObjectType and represents a GraphQL ObjectType for a ViolenceSubType model.

    Attributes:
        model (Model): The ViolenceSubType model that this ObjectType represents.
        exclude_fields (tuple): The fields to be excluded from the GraphQL schema.

    """
    class Meta:
        model = ViolenceSubType
        exclude_fields = ('events', 'violence')


class ViolenceSubObjectListType(CustomDjangoListObjectType):
    """
    This class is a custom Django list object type for ViolenceSubType model. It inherits from
    CustomDjangoListObjectType.

    Attributes:
        model (Model): The Django model that this object list type is related to.
        filterset_class (FilterSet): The Django filterset class to be used for filtering the query results.

    """
    class Meta:
        model = ViolenceSubType
        filterset_class = ViolenceSubTypeFilter


class ViolenceType(DjangoObjectType):
    """
    A class representing the ViolenceType.

    ViolenceType is a DjangoObjectType class used to define the structure and behavior of the 'Violence' model in the
    database.

    Attributes:
        Meta: A class representing the meta options for the ViolenceType class.
            model (class): The model class associated with the ViolenceType.
            exclude_fields (tuple): The fields to be excluded from the ViolenceType.
        sub_types: A DjangoPaginatedListObjectField representing the related 'sub_types' field in the Violence model.
            ViolenceSubObjectListType (class): The type of the related 'sub_types' field.
            related_name (str): The related name used to access the 'sub_types' field from the
            ViolenceSubObjectListType.
            reverse_related_name (str): The reverse related name used to access the 'violence' field from the
            ViolenceSubObjectListType.
    """
    class Meta:
        model = Violence
        exclude_fields = ('events',)

    sub_types = DjangoPaginatedListObjectField(
        ViolenceSubObjectListType,
        related_name='sub_types',
        reverse_related_name='violence',
    )


class ViolenceListType(CustomDjangoListObjectType):
    """
    Represents a GraphQL type for listing instances of Violence.

    This class extends the CustomDjangoListObjectType class to provide functionality for listing instances of Violence.
    It uses the Violence model and ViolenceFilter filterset class for querying and filtering Violence instances.

    Attributes:
        Meta (class): Defines the metadata for the ViolenceListType.
            - model (Violence): The model to be used for querying Violence instances.
            - filterset_class (ViolenceFilter): The filterset class to be used for filtering Violence instances.

    """
    class Meta:
        model = Violence
        filterset_class = ViolenceFilter


class ActorType(DjangoObjectType):
    """
    A class representing an ActorType object in the system.

    This class is derived from the DjangoObjectType and is specifically designed to work with the Actor model.
    It includes a Meta class that defines the model and excludes certain fields.

    Attributes:
        model (Actor): The model used for the ActorType object.
        exclude_fields (tuple): The fields to be excluded from the ActorType object.

    """
    class Meta:
        model = Actor
        exclude_fields = ('events',)


class ActorListType(CustomDjangoListObjectType):
    """
    Class representing a GraphQL list type for actors.

    Inherits from the CustomDjangoListObjectType class.

    Attributes:
        Meta: A nested class that specifies metadata for the ActorListType.

    """
    class Meta:
        model = Actor
        filterset_class = ActorFilter


class DisasterSubObjectType(DjangoObjectType):
    """

    Class representing a GraphQL Object Type for DisasterSubType in Django.

    Attributes:
        model (Model): The Django model class representing DisasterSubType.
        exclude_fields (Tuple): The names of fields to exclude from the GraphQL object.

    """
    class Meta:
        model = DisasterSubType
        exclude_fields = ('events', 'type')


class DisasterSubObjectListType(CustomDjangoListObjectType):
    """

    Subclass of CustomDjangoListObjectType that represents a list of DisasterSubType objects.

    Attributes:
        model (Model): The Django model used to generate the list of objects.
        filterset_class (FilterSet): The filterset class used to filter the list of objects.

    """
    class Meta:
        model = DisasterSubType
        filterset_class = DisasterSubTypeFilter


class DisasterTypeObjectType(DjangoObjectType):
    """
    Class representing a GraphQL object type for a Disaster Type.

    This class extends the DjangoObjectType class from the graphene-django library.
    It defines the GraphQL object type for the DisasterType model in the Django ORM.

    Attributes:
        Meta (class): A nested class defining metadata options for the GraphQL object type.
            - model: The Django model associated with the GraphQL object type.
            - exclude_fields: A tuple of field names to be excluded from the GraphQL object type.

        sub_types (DjangoPaginatedListObjectField): A field representing a paginated list of sub types
            associated with the disaster type.
            - DisasterSubObjectListType: The GraphQL object type for the sub types.
            - related_name: The related name used in the Django model for the reverse relation.
            - reverse_related_name: The reverse related name used in the Django model for the forward relation.
    """
    class Meta:
        model = DisasterType
        exclude_fields = ('events', 'disaster_sub_category')

    sub_types = DjangoPaginatedListObjectField(
        DisasterSubObjectListType,
        related_name='sub_types',
        reverse_related_name='type',
    )


class DisasterTypeObjectListType(CustomDjangoListObjectType):
    """

    Class DisasterTypeObjectListType

    A type definition for a list of DisasterType objects in the Django database.

    Attributes:
    - model: The Django model class for DisasterType.
    - filterset_class: The filterset class to be used for filtering the list.

    """
    class Meta:
        model = DisasterType
        filterset_class = DisasterTypeFilter


class DisasterSubCategoryType(DjangoObjectType):
    """
    Class: DisasterSubCategoryType

    This class is used to define the GraphQL ObjectType for the DisasterSubCategory model.

    Attributes:
        - model (Model): The Django model used for the ObjectType.
        - exclude_fields (Tuple): A tuple of field names to be excluded from the ObjectType.

    Methods:
        - types (DjangoPaginatedListObjectField): A field that represents the reversed relationship between
        `DisasterSubCategoryType` and `DisasterTypeObjectListType`.

    """
    class Meta:
        model = DisasterSubCategory
        exclude_fields = ('events', 'category')

    types = DjangoPaginatedListObjectField(
        DisasterTypeObjectListType,
        related_name='types',
        reverse_related_name='disaster_sub_category',
    )


class DisasterSubCategoryListType(CustomDjangoListObjectType):
    """

    The DisasterSubCategoryListType class is a custom Django ListObjectType that is used to represent a list of
    DisasterSubCategory objects.

    Attributes:
        - model (Class): The Django model class for DisasterSubCategory.
        - filterset_class (Class): The Django filterset class for DisasterSubCategory.

    """
    class Meta:
        model = DisasterSubCategory
        filterset_class = DisasterSubCategoryFilter


class DisasterCategoryType(DjangoObjectType):
    """

    DisasterCategoryType

    Represents the GraphQL ObjectType for the DisasterCategory model.

    Attributes:
        - model (class): The Django model for the DisasterCategory.
        - exclude_fields (tuple): The fields to exclude from the DisasterCategoryType.

    """
    class Meta:
        model = DisasterCategory
        exclude_fields = ('events',)

    sub_categories = DjangoPaginatedListObjectField(
        DisasterSubCategoryListType,
        related_name='sub_categories',
        reverse_related_name='category',
    )


class DisasterCategoryListType(CustomDjangoListObjectType):
    """
    This class represents a list type for DisasterCategory objects in the Django application.

    It inherits from the CustomDjangoListObjectType class and provides a Meta inner class that specifies the model as
    DisasterCategory and the filterset_class as DisasterCategoryFilter.

    Attributes:
        - model (Django model): The model class representing the DisasterCategory object.
        - filterset_class (Django filterset): The filterset class used for filtering DisasterCategory objects.

    Usage:
        # Create an instance of the DisasterCategoryListType class
        disaster_list = DisasterCategoryListType()

        # Use the instance to access the model and filterset_class attributes
        model_class = disaster_list.model
        filterset_class = disaster_list.filterset_class
    """
    class Meta:
        model = DisasterCategory
        filterset_class = DisasterCategoryFilter


class EventReviewCountType(graphene.ObjectType):
    """
    Class for representing the review count type for an event.

    Attributes:
        review_not_started_count (int): The count of reviews that haven't started yet.
        review_in_progress_count (int): The count of reviews that are in progress.
        review_re_request_count (int): The count of reviews that have been requested again.
        review_approved_count (int): The count of reviews that have been approved.
        total_count (int): The total count of all reviews.
        progress (float): The overall progress of the event's reviews.

    """
    review_not_started_count = graphene.Int(required=False)
    review_in_progress_count = graphene.Int(required=False)
    review_re_request_count = graphene.Int(required=False)
    review_approved_count = graphene.Int(required=False)
    total_count = graphene.Int(required=False)
    progress = graphene.Float(required=False)


class OsvSubObjectType(DjangoObjectType):
    """

    The OsvSubObjectType class is a subclass of DjangoObjectType. It represents the GraphQL object type for the
    OsvSubType model.

    Attributes:
        model (Model): The Django model that this object type represents.
        filterset_class (FilterSet): The filterset class used for filtering objects of this type.

    """
    class Meta:
        model = OsvSubType
        filterset_class = OsvSubTypeFilter


class OsvSubTypeList(CustomDjangoListObjectType):
    """
    Class OsvSubTypeList

    This class is a custom Django list object type for OsvSubType.

    Attributes:
    - model (class): The model class for OsvSubType.
    - filterset_class (class): The filterset class for OsvSubType.

    """
    class Meta:
        model = OsvSubType
        filterset_class = OsvSubTypeFilter


class OtherSubTypeObjectType(DjangoObjectType):
    """
    Represents a GraphQL type for the OtherSubType model in the Django database.

    Attributes:
        Meta: A Meta class that specifies the model and filterset class for the OtherSubTypeObjectType.

    Example usage:
        # Define the GraphQL type for OtherSubType model
        class OtherSubTypeObjectType(DjangoObjectType):
            class Meta:
                model = OtherSubType
                filterset_class = OtherSubTypeFilter
    """
    class Meta:
        model = OtherSubType
        filterset_class = OtherSubTypeFilter


class OtherSubTypeList(CustomDjangoListObjectType):
    """

    """
    class Meta:
        model = OtherSubType
        filterset_class = OtherSubTypeFilter


class EventCodeType(DjangoObjectType):
    """
    A class representing the GraphQL object type for EventCodeType.

    Attributes:
        event_code_type (graphene.Field): A field representing the GraphQL enum type for event code type.
        event_code_display (EnumDescription): A description field for event code type display.

    Meta:
        model (EventCode): The model used for the EventCodeType object type.
        fields (tuple): A tuple of field names to be included in the EventCodeType object type.
    """
    event_code_type = graphene.Field(EventCodeTypeGrapheneEnum)
    event_code_display = EnumDescription(source='get_event_code_type_display')

    class Meta:
        model = EventCode
        fields = ('id', 'uuid', 'event_code', 'event_code_type', 'country')


class EventType(DjangoObjectType):
    """
    Class representing an event type.

    Attributes:
    - model: The Django model that this class is based on.
    - exclude_fields: List of fields to exclude from the model.

    Methods:
    - resolve_crisis: Resolve the crisis associated with the event.
    - resolve_event_codes: Resolve the event codes associated with the event.
    - resolve_entry_count: Resolve the count of entries associated with the event.
    - resolve_event_typology: Resolve the typology of the event.
    - resolve_figure_typology: Resolve the typology of the figures associated with the event.
    - resolve_total_stock_idp_figures: Resolve the total stock IDP figures associated with the event.
    - resolve_stock_idp_figures_max_end_date: Resolve the maximum end date for the stock IDP figures associated with the
    event.
    - resolve_total_flow_nd_figures: Resolve the total flow ND figures associated with the event.
    - resolve_review_count: Resolve the count of reviews associated with the event.
    """
    class Meta:
        model = Event
        exclude_fields = ('figures', 'gidd_events', 'glide_numbers')

    event_type = graphene.Field(CrisisTypeGrapheneEnum)
    event_type_display = EnumDescription(source='get_event_type_display')
    other_sub_type = graphene.Field(OtherSubTypeObjectType)
    violence = graphene.Field(ViolenceType)
    violence_sub_type = graphene.Field(ViolenceSubObjectType)
    actor = graphene.Field(ActorType)
    total_stock_idp_figures = graphene.Field(graphene.Int)
    stock_idp_figures_max_end_date = graphene.Field(graphene.Date, required=False)
    total_flow_nd_figures = graphene.Field(graphene.Int)
    start_date_accuracy = graphene.Field(DateAccuracyGrapheneEnum)
    start_date_accuracy_display = EnumDescription(source='get_start_date_accuracy_display')
    end_date_accuracy = graphene.Field(DateAccuracyGrapheneEnum)
    end_date_accuracy_display = EnumDescription(source='get_end_date_accuracy_display')
    entry_count = graphene.Field(graphene.Int)
    osv_sub_type = graphene.Field(OsvSubObjectType)
    qa_rule_type = graphene.Field(QaRecommendedFigureEnum)
    qs_rule_type_display = EnumDescription(source='get_qs_rule_type_display')
    event_typology = graphene.String()
    figure_typology = graphene.List(graphene.String)
    review_status = graphene.Field(EventReviewStatusEnum)
    review_status_display = EnumDescription(source='get_review_status_display')
    review_count = graphene.Field(EventReviewCountType)
    event_codes = graphene.List(graphene.NonNull(EventCodeType))
    crisis = graphene.Field('apps.crisis.schema.CrisisType')
    crisis_id = graphene.ID(required=True, source='crisis_id')

    def resolve_crisis(root, info, **kwargs):
        return info.context.event_crisis_loader.load(root.id)

    def resolve_event_codes(root, info, **kwargs):
        return info.context.event_code_loader.load(root.id)

    def resolve_entry_count(root, info, **kwargs):
        return info.context.event_entry_count_dataloader.load(root.id)

    def resolve_event_typology(root, info, **kwargs):
        return info.context.event_typology_dataloader.load(root.id)

    def resolve_figure_typology(root, info, **kwargs):
        return info.context.event_figure_typology_dataloader.load(root.id)

    def resolve_total_stock_idp_figures(root, info, **kwargs):
        NULL = 'null'
        value = getattr(
            root,
            Event.IDP_FIGURES_ANNOTATE,
            NULL
        )
        if value != NULL:
            return value
        return info.context.event_event_total_stock_idp_figures.load(root.id)

    def resolve_stock_idp_figures_max_end_date(root, info, **kwargs):
        NULL = 'null'
        value = getattr(
            root,
            Event.IDP_FIGURES_REFERENCE_DATE_ANNOTATE,
            NULL
        )
        if value != NULL:
            return value
        return info.context.event_stock_idp_figures_max_end_date.load(root.id)

    def resolve_total_flow_nd_figures(root, info, **kwargs):
        NULL = 'null'
        value = getattr(
            root,
            Event.ND_FIGURES_ANNOTATE,
            NULL
        )
        if value != NULL:
            return value
        return info.context.event_event_total_flow_nd_figures.load(root.id)

    def resolve_review_count(root, info, **kwargs):
        return info.context.event_review_count_dataloader.load(root.id)


class EventListType(CustomDjangoListObjectType):
    """
    A class representing a custom Django list object type for events.

    Attributes:
        Meta (class): A nested class specifying the meta options for the EventListType.

    Usage:
        To create a new instance of EventListType:

            event_list = EventListType()

    """
    class Meta:
        model = Event
        filterset_class = EventFilter


class ContextOfViolenceType(DjangoObjectType):
    """
    Django Object Type representing the ContextOfViolence model.

    This class is responsible for defining the GraphQL type for the ContextOfViolence model, allowing it to be queried
    and manipulated through GraphQL.

    Attributes:
        - model (Model): The Django model used for the ContextOfViolence type.
        - filterset_class (FilterSet): The Django FilterSet used for filtering ContextOfViolence objects.

    """
    class Meta:
        model = ContextOfViolence
        filterset_class = ContextOfViolenceFilter


class ContextOfViolenceListType(CustomDjangoListObjectType):
    """
    A class representing a list of ContextOfViolence objects.

    Parameters:
        CustomDjangoListObjectType (class): A class inheriting from CustomDjangoListObjectType.

    Attributes:
        model (class): The model class associated with the list.
        filterset_class (class): The filterset class associated with the list.

    """
    class Meta:
        model = ContextOfViolence
        filterset_class = ContextOfViolenceFilter


class Query:
    """

    Class Query

    This class represents a query object used in a Django application.

    Attributes:
    - violence_list: A DjangoPaginatedListObjectField representing a list of ViolenceListType objects.
    - actor: A DjangoObjectField representing an ActorType object.
    - actor_list: A DjangoPaginatedListObjectField representing a list of ActorListType objects with pagination.
    - disaster_category_list: A DjangoPaginatedListObjectField representing a list of DisasterCategoryListType objects.
    - disaster_sub_category_list: A DjangoPaginatedListObjectField representing a list of DisasterSubCategoryListType
    objects.
    - disaster_type_list: A DjangoPaginatedListObjectField representing a list of DisasterTypeObjectListType objects.
    - disaster_sub_type_list: A DjangoPaginatedListObjectField representing a list of DisasterSubObjectListType objects.
    - event: A DjangoObjectField representing an EventType object.
    - event_list: A DjangoPaginatedListObjectField representing a list of EventListType objects with pagination.
    - osv_sub_type_list: A DjangoPaginatedListObjectField representing a list of OsvSubTypeList objects.
    - context_of_violence: A DjangoObjectField representing a ContextOfViolenceType object.
    - context_of_violence_list: A DjangoPaginatedListObjectField representing a list of ContextOfViolenceListType
    objects.
    - other_sub_type_list: A DjangoPaginatedListObjectField representing a list of OtherSub"""
    violence_list = DjangoPaginatedListObjectField(ViolenceListType)
    actor = DjangoObjectField(ActorType)
    actor_list = DjangoPaginatedListObjectField(ActorListType,
                                                pagination=PageGraphqlPaginationWithoutCount(
                                                    page_size_query_param='pageSize'
                                                ))
    disaster_category_list = DjangoPaginatedListObjectField(DisasterCategoryListType)
    disaster_sub_category_list = DjangoPaginatedListObjectField(DisasterSubCategoryListType)
    disaster_type_list = DjangoPaginatedListObjectField(DisasterTypeObjectListType)
    disaster_sub_type_list = DjangoPaginatedListObjectField(DisasterSubObjectListType)

    event = DjangoObjectField(EventType)
    event_list = DjangoPaginatedListObjectField(EventListType,
                                                pagination=PageGraphqlPaginationWithoutCount(
                                                    page_size_query_param='pageSize'
                                                ))
    osv_sub_type_list = DjangoPaginatedListObjectField(OsvSubTypeList)
    context_of_violence = DjangoObjectField(ContextOfViolenceType)
    context_of_violence_list = DjangoPaginatedListObjectField(ContextOfViolenceListType)
    other_sub_type_list = DjangoPaginatedListObjectField(OtherSubTypeList)

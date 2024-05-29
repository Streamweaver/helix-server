import typing
from collections import OrderedDict

from django.db import models
from django.db.models.functions import Cast
from django.contrib.postgres.aggregates.general import StringAgg, ArrayAgg
from django.utils.translation import gettext_lazy as _
from django_enumfield import enum
from django.contrib.postgres.fields import ArrayField
from django.forms import model_to_dict

from utils.common import add_clone_prefix
from utils.db import Array

from apps.contrib.models import (
    MetaInformationAbstractModel,
    UUIDAbstractModel,
    MetaInformationArchiveAbstractModel,
)
from apps.crisis.models import Crisis
from apps.contrib.commons import DATE_ACCURACY
from apps.entry.models import Figure
from apps.users.models import User, USER_ROLE
from apps.common.utils import format_event_codes_as_string, EXTERNAL_ARRAY_SEPARATOR


class NameAttributedModels(models.Model):
    """
    A class representing abstract models with a name attribute.

    Attributes:
        name (str): The name of the model.

    Methods:
        __str__(): Returns a string representation of the model object.

    """
    name = models.CharField(_('Name'), max_length=256)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


# Models related to displacement caused by conflict


class Violence(NameAttributedModels):
    """
    This class represents a model for violence instances. It inherits from the NameAttributedModels class.

    Attributes:
        id (int): The unique identifier for the violence instance.
        name (str): The name of the violence instance.
        attributes (dict): A dictionary containing additional attributes of the violence instance.

    Methods:
        get_id: Returns the unique identifier of the violence instance.
        set_id: Sets the unique identifier of the violence instance.
        get_name: Returns the name of the violence instance.
        set_name: Sets the name of the violence instance.
        get_attributes: Returns the additional attributes of the violence instance.
        set_attributes: Sets the additional attributes of the violence instance.

    """


class ViolenceSubType(NameAttributedModels):
    """
    Class representing a subtype of violence.

    This class extends the NameAttributedModels class and represents a specific subtype of violence. Each subtype is associated with a parent violence instance.

    Attributes:
        violence (ForeignKey): The parent violence instance to which this subtype belongs.
        name (CharField): The name of the violence subtype.

    """
    violence = models.ForeignKey('Violence',
                                 related_name='sub_types', on_delete=models.CASCADE)


class ContextOfViolence(MetaInformationAbstractModel, NameAttributedModels):
    """

    This class represents the context of violence. It extends the MetaInformationAbstractModel and NameAttributedModels classes.

    Attributes:
        None

    Methods:
        get_excel_sheets_data(cls, user_id, filters)
            This method retrieves the excel sheets data for the given user and filters.

    """
    @classmethod
    def get_excel_sheets_data(cls, user_id, filters):
        from apps.event.filters import ContextOfViolenceFilter

        class DummyRequest:
            def __init__(self, user):
                self.user = user

        headers = OrderedDict(
            id='ID',
            created_at='Created at',
            created_by__full_name='Created by',
            name='Name',
            modified_at='Modified At',
            last_modified_by__full_name='Last Modified By',
        )
        data = ContextOfViolenceFilter(
            data=filters,
            request=DummyRequest(user=User.objects.get(id=user_id)),
        ).qs.order_by('created_at')

        return {
            'headers': headers,
            'data': data.values(*[header for header in headers.keys()]),
            'formulae': None,
            'transformer': None,
        }


class OtherSubType(MetaInformationAbstractModel, NameAttributedModels):
    """
    A class representing OtherSubType.

    This class inherits from MetaInformationAbstractModel and NameAttributedModels.

    Attributes:
    - None

    Methods:
    - None
    """


class Actor(MetaInformationAbstractModel, NameAttributedModels):
    """
    `Actor` class represents an actor in the system.

    Attributes:
        country (ForeignKey): A foreign key to the 'Country' model, representing the country of the actor.
        torg (CharField): A character field representing the Torg of the actor.

    Methods:
        get_excel_sheets_data(cls, user_id, filters):
            Retrieves data from the 'Actor' model based on the provided filters and user ID.
            Returns a dictionary containing the headers, data, formulae, and transformer for exporting to Excel.

    Usage Example:
        actor = Actor()
        data = actor.get_excel_sheets_data(user_id, filters)
    """
    country = models.ForeignKey('country.Country', verbose_name=_('Country'),
                                null=True,
                                on_delete=models.SET_NULL, related_name='actors')
    # NOTE: torg is used to map actors in the system to it's external source
    torg = models.CharField(verbose_name=_('Torg'), max_length=10, null=True)

    @classmethod
    def get_excel_sheets_data(cls, user_id, filters):
        from apps.event.filters import ActorFilter

        class DummyRequest:
            def __init__(self, user):
                self.user = user

        headers = OrderedDict(
            id='ID',
            created_at='Created at',
            created_by__full_name='Created by',
            name='Name',
            country__idmc_short_name='Country',
            country__iso3='ISO3',
            torg='TORG',
        )
        data = ActorFilter(
            data=filters,
            request=DummyRequest(user=User.objects.get(id=user_id)),
        ).qs.order_by('id')

        return {
            'headers': headers,
            'data': data.values(*[header for header in headers.keys()]),
            'formulae': None,
            'transformer': None,
        }


# Models related to displacement caused by disaster


class DisasterCategory(NameAttributedModels):
    """

    This class represents a Disaster Category.

    Attributes:
    - id (int): The unique identifier of the Disaster Category.
    - name (str): The name of the Disaster Category.

    """


class DisasterSubCategory(NameAttributedModels):
    """
    A class representing a disaster subcategory.

    Attributes:
        category (ForeignKey): The foreign key to the parent disaster category.

    """
    category = models.ForeignKey('DisasterCategory', verbose_name=_('Hazard Category'),
                                 related_name='sub_categories', on_delete=models.CASCADE)


class DisasterType(NameAttributedModels):
    """
    Initialize a new instance of DisasterType class.

    Args:
        disaster_sub_category (DisasterSubCategory): The disaster sub category related to this disaster type.
    """
    disaster_sub_category = models.ForeignKey('DisasterSubCategory',
                                              verbose_name=_('Hazard Sub Category'),
                                              related_name='types', on_delete=models.CASCADE)


class DisasterSubType(NameAttributedModels):
    """A class representing a disaster sub-type.

    This class extends the NameAttributedModels class and is used to store information about a specific sub-type of a disaster. Each sub-type belongs to a particular disaster type.

    Attributes:
        type (ForeignKey): A foreign key to the DisasterType model, representing the disaster type that this sub-type belongs to.

    """
    type = models.ForeignKey('DisasterType', verbose_name=_('Hazard Type'),
                             related_name='sub_types', on_delete=models.CASCADE)


class Event(MetaInformationArchiveAbstractModel, models.Model):
    """
    The Event class represents an event in the system.

    Attributes:
        EVENT_REVIEW_STATUS (enum.Enum): Enumerated type that represents the status of event review.
        ND_FIGURES_ANNOTATE (str): Variable that stores the annotation for total flow ND figures.
        IDP_FIGURES_ANNOTATE (str): Variable that stores the annotation for total stock IDP figures.
        IDP_FIGURES_REFERENCE_DATE_ANNOTATE (str): Variable that stores the annotation for the reference date of IDP figures.
        crisis (models.ForeignKey): ForeignKey to the Crisis model representing the crisis associated with the event.
        name (models.CharField): CharField representing the name of the event.
        event_type (enum.EnumField): EnumField representing the cause of the event.
        other_sub_type (models.ForeignKey): ForeignKey to the OtherSubType model representing the other sub type of the event.
        glide_numbers (ArrayField): ArrayField of CharFields representing the event codes of the event.
        violence (models.ForeignKey): ForeignKey to the Violence model representing the violence associated with the event.
        violence_sub_type (models.ForeignKey): ForeignKey to the ViolenceSubType model representing the violence sub type of the event.
        actor (models.ForeignKey): ForeignKey to the Actor model representing the actors associated with the event.
        disaster_category (models.ForeignKey): ForeignKey to the DisasterCategory model representing the hazard category of the event.
        disaster_sub_category (models.ForeignKey): ForeignKey to the DisasterSubCategory model representing the hazard sub category of the event.
        disaster_type (models.ForeignKey): ForeignKey to the DisasterType model representing the hazard type of the event.
        disaster_sub_type (models.ForeignKey): ForeignKey to the DisasterSubType model representing the hazard sub type of the event.
        countries (models.ManyToManyField): ManyToManyField to the Country model representing the countries associated with the event.
        start_date (models.DateField): DateField representing the start date of the event.
        start_date_accuracy (enum.EnumField): EnumField representing the accuracy of the start date.
        end_date (models.DateField): DateField representing the end date of the event.
        end_date_accuracy (enum.EnumField): EnumField representing the accuracy of the end date.
        event_narrative (models.TextField): TextField representing the narrative of the event.
        osv_sub_type (models.ForeignKey): ForeignKey to the OsvSubType model representing the OSV sub type of the event.
        ignore_qa (models.BooleanField): BooleanField indicating whether QA should be ignored for the event.
        context_of_violence (models.ManyToManyField): ManyToManyField to the ContextOfViolence model representing the context of violence associated with the event.
        assigner (models.ForeignKey): ForeignKey to the User model representing the assigner of the event.
        assignee (models.ForeignKey): ForeignKey to the User model representing the assignee of the event.
        assigned_at (models.DateTimeField): DateTimeField representing the date and time when the event was assigned.
        review_status (enum.EnumField): EnumField representing the status of the event.
        include_triangulation_in_qa (models.BooleanField): BooleanField indicating whether triangulation should be included in QA for the event.

    Methods:
        _total_figure_disaggregation_subquery(cls, figures=None, reference_date=None):
            Builds and returns a subquery for total figure disaggregation.
            Args:
                figures (QuerySet, optional): QuerySet of Figure objects. Defaults to None.
                reference_date (date, optional): The reference date for the figure disaggregation. Defaults to None.
            Returns:
                dict: Dictionary containing the subqueries for total flow ND figures, total stock IDP figures, and the reference date of IDP figures.

        annotate_review_figures_count(cls):
            Builds and returns a dictionary with the annotations for review figures count.
            Returns:
                dict: Dictionary containing annotations for the counts of figures in review.

    Note:
        This class inherits from the MetaInformationArchiveAbstractModel and models.Model classes.
    """
    class EVENT_REVIEW_STATUS(enum.Enum):
        REVIEW_NOT_STARTED = 0
        REVIEW_IN_PROGRESS = 1
        APPROVED = 2
        SIGNED_OFF = 3
        # NOTE: these two statuses should be hidden to the client
        APPROVED_BUT_CHANGED = 4
        SIGNED_OFF_BUT_CHANGED = 5

        __labels__ = {
            REVIEW_NOT_STARTED: _("Review not started"),
            REVIEW_IN_PROGRESS: _("Review in progress"),
            APPROVED: _("Approved"),
            SIGNED_OFF: _("Signed-off"),
            APPROVED_BUT_CHANGED: _("Approved but changed"),
            SIGNED_OFF_BUT_CHANGED: _("Signed-off but changed"),
        }

    # NOTE figure disaggregation variable definitions
    ND_FIGURES_ANNOTATE = 'total_flow_nd_figures'
    IDP_FIGURES_ANNOTATE = 'total_stock_idp_figures'
    IDP_FIGURES_REFERENCE_DATE_ANNOTATE = 'idp_figures_reference_date'

    crisis = models.ForeignKey('crisis.Crisis', verbose_name=_('Crisis'),
                               blank=True, null=True,
                               related_name='events', on_delete=models.CASCADE)
    name = models.CharField(verbose_name=_('Event Name'), max_length=256)
    event_type = enum.EnumField(Crisis.CRISIS_TYPE, verbose_name=_('Event Cause'))

    other_sub_type = models.ForeignKey(
        'OtherSubType', verbose_name=_('Other sub type'),
        blank=True, null=True,
        related_name='events', on_delete=models.SET_NULL)
    glide_numbers = ArrayField(
        models.CharField(
            verbose_name=_('Event Codes'), max_length=256, null=True, blank=True
        ),
        default=list,
        null=True, blank=True
    )
    violence = models.ForeignKey('Violence', verbose_name=_('Violence'),
                                 blank=False, null=True,
                                 related_name='events', on_delete=models.SET_NULL)
    violence_sub_type = models.ForeignKey('ViolenceSubType', verbose_name=_('Violence Sub Type'),
                                          blank=True, null=True,
                                          related_name='events', on_delete=models.SET_NULL)
    actor = models.ForeignKey('Actor', verbose_name=_('Actors'),
                              blank=True, null=True,
                              related_name='events', on_delete=models.SET_NULL)
    # disaster related fields
    disaster_category = models.ForeignKey('DisasterCategory', verbose_name=_('Hazard Category'),
                                          blank=True, null=True,
                                          related_name='events', on_delete=models.SET_NULL)
    disaster_sub_category = models.ForeignKey('DisasterSubCategory', verbose_name=_('Hazard Sub Category'),
                                              blank=True, null=True,
                                              related_name='events', on_delete=models.SET_NULL)
    disaster_type = models.ForeignKey('DisasterType', verbose_name=_('Hazard Type'),
                                      blank=True, null=True,
                                      related_name='events', on_delete=models.SET_NULL)
    disaster_sub_type = models.ForeignKey('DisasterSubType', verbose_name=_('Hazard Sub Type'),
                                          blank=True, null=True,
                                          related_name='events', on_delete=models.SET_NULL)

    countries = models.ManyToManyField('country.Country', verbose_name=_('Countries'),
                                       related_name='events', blank=True)
    start_date = models.DateField(verbose_name=_('Start Date'))
    start_date_accuracy = enum.EnumField(
        DATE_ACCURACY,
        verbose_name=_('Start Date Accuracy'),
        default=DATE_ACCURACY.DAY,
        blank=True,
        null=True,
    )
    end_date = models.DateField(verbose_name=_('End Date'))
    end_date_accuracy = enum.EnumField(
        DATE_ACCURACY,
        verbose_name=_('End date accuracy'),
        default=DATE_ACCURACY.DAY,
        blank=True,
        null=True,
    )
    event_narrative = models.TextField(verbose_name=_('Event Narrative'), null=True)
    osv_sub_type = models.ForeignKey(
        'OsvSubType', verbose_name=_('OSV sub type'),
        blank=True, null=True, related_name='events',
        on_delete=models.SET_NULL
    )
    ignore_qa = models.BooleanField(verbose_name=_('Ignore QA'), default=False)
    context_of_violence = models.ManyToManyField(
        'ContextOfViolence', verbose_name=_('Context of violence'), blank=True, related_name='events'
    )
    assigner = models.ForeignKey(
        'users.User', verbose_name=_('Assigner'), null=True, blank=True,
        related_name='event_assigner', on_delete=models.SET_NULL
    )
    assignee = models.ForeignKey(
        'users.User', verbose_name=_('Assignee'), null=True, blank=True,
        related_name='event_assignee', on_delete=models.SET_NULL
    )
    assigned_at = models.DateTimeField(verbose_name='Assigned at', null=True, blank=True)
    review_status = enum.EnumField(
        EVENT_REVIEW_STATUS,
        verbose_name=_('Event status'),
        default=EVENT_REVIEW_STATUS.REVIEW_NOT_STARTED,
    )
    include_triangulation_in_qa = models.BooleanField(
        verbose_name='Include triangulation in qa?', default=False,
    )

    assignee_id: typing.Optional[int]

    @classmethod
    def _total_figure_disaggregation_subquery(cls, figures=None, reference_date=None):
        if figures is None:
            figures = Figure.objects.all()

        if reference_date is None:
            reference_date_qs = models.Subquery(
                figures.filter(
                    category=Figure.FIGURE_CATEGORY_TYPES.IDPS,
                    role=Figure.ROLE.RECOMMENDED,
                    event=models.OuterRef('pk'),
                ).order_by('-end_date').values('end_date')[:1]
            )
        else:
            reference_date_qs = models.Value(reference_date)

        return {
            cls.IDP_FIGURES_REFERENCE_DATE_ANNOTATE: reference_date_qs,
            cls.ND_FIGURES_ANNOTATE: models.Subquery(
                Figure.filtered_nd_figures(
                    figures.filter(
                        event=models.OuterRef('pk'),
                        role=Figure.ROLE.RECOMMENDED,
                    ),
                    # TODO: what about date range
                    start_date=None,
                    end_date=None,
                ).order_by().values('event').annotate(
                    _total=models.Sum('total_figures')
                ).values('_total')[:1],
                output_field=models.IntegerField(),
            ),
            cls.IDP_FIGURES_ANNOTATE: models.Subquery(
                Figure.filtered_idp_figures(
                    figures.filter(
                        event=models.OuterRef('pk'),
                        role=Figure.ROLE.RECOMMENDED,
                    ),
                    start_date=None,
                    end_date=models.OuterRef(cls.IDP_FIGURES_REFERENCE_DATE_ANNOTATE),
                ).order_by().values('event').annotate(
                    _total=models.Sum('total_figures')
                ).values('_total')[:1],
                output_field=models.IntegerField(),
            ),
        }

    @classmethod
    def annotate_review_figures_count(cls):
        return {
            'review_not_started_count': models.Count(
                'figures',
                filter=models.Q(
                    figures__review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_NOT_STARTED,
                    figures__role=Figure.ROLE.RECOMMENDED,
                ) | models.Q(
                    figures__review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_NOT_STARTED,
                    include_triangulation_in_qa=True,
                )
            ),
            'review_in_progress_count': models.Count(
                'figures',
                filter=models.Q(
                    figures__review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_IN_PROGRESS,
                    figures__role=Figure.ROLE.RECOMMENDED,
                ) | models.Q(
                    figures__review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_IN_PROGRESS,
                    include_triangulation_in_qa=True,
                )

            ),
            'review_re_request_count': models.Count(
                'figures',
                filter=models.Q(
                    figures__review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_RE_REQUESTED,
                    figures__role=Figure.ROLE.RECOMMENDED,
                ) | models.Q(
                    figures__review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_RE_REQUESTED,
                    include_triangulation_in_qa=True,
                )

            ),
            'review_approved_count': models.Count(
                'figures',
                filter=models.Q(
                    figures__review_status=Figure.FIGURE_REVIEW_STATUS.APPROVED,
                    figures__role=Figure.ROLE.RECOMMENDED,
                ) | models.Q(
                    figures__review_status=Figure.FIGURE_REVIEW_STATUS.APPROVED,
                    include_triangulation_in_qa=True,
                )

            ),
            'total_count': (
                models.F('review_not_started_count') +
                models.F('review_in_progress_count') +
                models.F('review_re_request_count') +
                models.F('review_approved_count')
            ),
            'progress': models.Case(
                models.When(
                    total_count__gt=0,
                    then=models.F('review_approved_count') / models.F('total_count')
                ),
                default=models.Value(0),
                output_field=models.FloatField()
            )
        }

    # FIXME: this is wrong, this should see event and user not event and figure
    @staticmethod
    def regional_coordinators(event, actor=None):
        actor_regional_coordinators = User.objects.none()
        event_regional_coordinators = User.objects.none()

        if actor:
            actor_regional_coordinators = User.objects.filter(
                portfolios__role=USER_ROLE.REGIONAL_COORDINATOR,
                portfolios__monitoring_sub_region__in=actor.portfolios.values(
                    'monitoring_sub_region'
                )
            )

        if event.countries:
            event_regional_coordinators = User.objects.filter(
                portfolios__role=USER_ROLE.REGIONAL_COORDINATOR,
                portfolios__monitoring_sub_region__in=event.countries.values(
                    'portfolio__monitoring_sub_region'
                )
            )
        coordinators = actor_regional_coordinators | event_regional_coordinators
        return coordinators.values('id')

    @classmethod
    def get_excel_sheets_data(cls, user_id, filters):
        from apps.event.filters import EventFilter

        class DummyRequest:
            def __init__(self, user):
                self.user = user

        headers = OrderedDict(
            id='ID',
            created_at='Created at',
            created_by__full_name='Created by',
            name='Name',
            start_date='Start date',
            start_date_accuracy='Start date accuracy',
            end_date='End date',
            end_date_accuracy='End date accuracy',
            event_type='Event cause',
            disaster_category__name='Hazard category',
            disaster_sub_category__name='Hazard sub category',
            disaster_type__name='Hazard type',
            disaster_sub_type__name='Hazard sub type',
            disaster_sub_type='Hazard sub type ID',
            countries_iso3='ISO3',
            countries_name='Countries',
            regions_name='Regions',
            figures_count='Figures count',
            entries_count='Entries count',
            # Extra added fields
            old_id='Old ID',
            crisis='Crisis ID',
            crisis__name='Crisis',
            **{
                cls.IDP_FIGURES_ANNOTATE: 'IDPs figure',
                cls.ND_FIGURES_ANNOTATE: 'ND figure',
            },
            other_sub_type__name='Other event sub type',
            violence__name='Violence type',
            violence_sub_type__name='Violence sub type',
            osv_sub_type__name="OSV sub type",
            actor_id='Actor ID',
            actor__name='Actor',
            context_of_violences='Context of violences',
            event_codes='Event codes (Code:Type:ISO3)',
            event_narrative='Event description',
        )

        data = EventFilter(
            data=filters,
            request=DummyRequest(user=User.objects.get(id=user_id)),
        ).qs.annotate(
            countries_iso3=StringAgg('countries__iso3', EXTERNAL_ARRAY_SEPARATOR, distinct=True),
            countries_name=StringAgg('countries__idmc_short_name', EXTERNAL_ARRAY_SEPARATOR, distinct=True),
            regions_name=StringAgg('countries__region__name', EXTERNAL_ARRAY_SEPARATOR, distinct=True),
            figures_count=models.Count('figures', distinct=True),
            entries_count=models.Count('figures__entry', distinct=True),
            context_of_violences=StringAgg('context_of_violence__name', EXTERNAL_ARRAY_SEPARATOR, distinct=True),
            event_codes=ArrayAgg(
                Array(
                    models.F('event_code__event_code'),
                    Cast(models.F('event_code__event_code_type'), models.CharField()),
                    models.F('event_code__country__iso3'),
                    output_field=ArrayField(models.CharField()),
                ),
                distinct=True,
            ),
        ).order_by('created_at')

        def transformer(datum):
            return {
                **datum,
                **dict(
                    event_type=getattr(Crisis.CRISIS_TYPE.get(datum['event_type']), 'label', ''),
                    start_date_accuracy=getattr(DATE_ACCURACY.get(datum['start_date_accuracy']), 'label', ''),
                    end_date_accuracy=getattr(DATE_ACCURACY.get(datum['end_date_accuracy']), 'label', ''),
                    event_codes=format_event_codes_as_string(datum['event_codes']),
                )
            }

        return {
            'headers': headers,
            'data': data.values(
                *[header for header in headers.keys()]
            ),
            'formulae': None,
            'transformer': transformer,
        }

    def __str__(self):
        return self.name or str(self.id)

    class Meta:
        permissions = (
            ('assign_event', 'Can assign on event level'),
            ('self_assign_event', 'Can assign self on event level'),
            ('clear_assignee_event', 'Can clear any assignee from event'),
            ('clear_self_assignee_event', 'Can clear self assigned event'),
            ('sign_off_event', 'Can sign-off event'),
        )

    def clone_and_save_event(self, user: 'User'):
        event_data = model_to_dict(
            self,
            exclude=[
                'id', 'created_at', 'created_by', 'last_modified_by',
            ]
        )
        # Clone m2m keys fields
        countries = event_data.pop('countries')
        context_of_violence = event_data.pop('context_of_violence')
        # Clone foreigh key fields
        foreign_key_fields_dict = {
            "crisis": Crisis,
            "violence": Violence,
            "violence_sub_type": ViolenceSubType,
            "actor": Actor,
            "disaster_category": DisasterCategory,
            "disaster_sub_category": DisasterSubCategory,
            "disaster_sub_type": DisasterSubType,
            "disaster_type": DisasterType
        }
        for field, model in foreign_key_fields_dict.items():
            if event_data[field]:
                event_data[field] = model.objects.get(pk=event_data[field])

        event_data['created_by'] = user
        event_data['name'] = add_clone_prefix(event_data['name'])
        cloned_event = Event.objects.create(**event_data)
        # Add m2m contires
        cloned_event.countries.set(countries)
        cloned_event.context_of_violence.set(context_of_violence)
        return cloned_event


class EventCode(UUIDAbstractModel, models.Model):
    """
    Class to represent an event code.

    This class extends the `UUIDAbstractModel` and `models.Model` classes.

    Attributes:
        EVENT_CODE_TYPE (enum.Enum): Enumeration of event code types.
            - GLIDE_NUMBER: Represents the glide number event code type.
            - GOV_ASSIGNED_IDENTIFIER: Represents the government assigned identifier event code type.
            - IFRC_APPEAL_ID: Represents the IFRC appeal ID event code type.
            - ACLED_ID: Represents the ACLED ID event code type.
            - LOCAL_IDENTIFIER: Represents the local identifier event code type.

    Methods:
        N/A

    Attributes:
        event (models.ForeignKey): ForeignKey to the Event model.
        country (models.ForeignKey): ForeignKey to the Country model.
        event_code_type (enum.EnumField): Integer field to store the event code type.
        event_code (models.CharField): CharField to store the event code.
        event_id (int): ID of the event.

    Meta:
        ordering (list[str]): List of fields to be used to order the EventCode objects.
    """
    class EVENT_CODE_TYPE(enum.Enum):
        GLIDE_NUMBER = 1
        GOV_ASSIGNED_IDENTIFIER = 2
        IFRC_APPEAL_ID = 3
        ACLED_ID = 4
        LOCAL_IDENTIFIER = 5

        __labels__ = {
            GLIDE_NUMBER: _("Glide Number"),
            GOV_ASSIGNED_IDENTIFIER: _("Government Assigned Identifier"),
            IFRC_APPEAL_ID: _("IFRC Appeal ID"),
            ACLED_ID: _("ACLED ID"),
            LOCAL_IDENTIFIER: _("Local Identifier"),
        }

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='event_code',
        verbose_name=_('Event')
    )
    country = models.ForeignKey(
        'country.Country',
        on_delete=models.CASCADE,
        related_name='event_code_country',
        verbose_name=_('Country')
    )
    event_code_type = enum.EnumField(EVENT_CODE_TYPE)
    event_code = models.CharField(max_length=256, verbose_name=_('Event Code'))

    event_id: int

    class Meta:
        ordering = ['event_code']


class OsvSubType(NameAttributedModels):
    """
    Subtype class for operating system versions.

    This class extends the NameAttributedModels class and represents a subtype of operating system versions.

    Attributes:
        id (int): The unique identifier for the subtype.
        name (str): The name of the subtype.

    Methods:
        get_id(): Get the unique identifier of the subtype.
        set_id(id: int): Set the unique identifier of the subtype.
        get_name(): Get the name of the subtype.
        set_name(name: str): Set the name of the subtype.
    """

from collections import OrderedDict
from copy import copy
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import transaction
from django.utils.translation import gettext, gettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import CharField

from apps.contrib.serializers import (
    MetaInformationSerializerMixin,
    UpdateSerializerMixin,
    IntegerIDField,
)
from apps.entry.models import (
    Entry,
    Figure,
    OSMName,
    FigureTag,
    DisaggregatedAge,
)
from apps.country.models import Country
from utils.validations import is_child_parent_inclusion_valid, is_child_parent_dates_valid
from utils.common import round_half_up
from .utils import (
    send_figure_notifications,
    BulkUpdateFigureManager,
    get_figure_notification_type,
    get_event_notification_type,
)


class DisaggregatedAgeSerializer(serializers.ModelSerializer):
    """
    Serializer for DisaggregatedAge model.

    This serializer allows updating of DisaggregatedAge instances. It validates the provided data and returns any errors
    encountered during the validation process.

    Attributes:
        id (IntegerField): Field to allow updating of the DisaggregatedAge instance (optional).

    Methods:
        validate(attrs): Validates the provided attributes and returns any errors encountered.

    Meta:
        model (DisaggregatedAge): The model class associated with the serializer.
        fields (str or tuple): The fields to be serialized.
        extra_kwargs (dict): Additional arguments for specific fields.

    """
    # to allow updating
    id = IntegerIDField(required=False)

    def validate(self, attrs):
        errors = OrderedDict()
        age_from = attrs.get('age_from')
        age_to = attrs.get('age_to')

        if (age_from and not age_to):
            errors['age_to'] = gettext('This field is required.')
        if (age_to and not age_from):
            errors['age_from'] = gettext('This field is required.')
        return attrs

    class Meta:
        model = DisaggregatedAge
        fields = '__all__'
        extra_kwargs = {
            'uuid': {
                'validators': [],
                'required': True
            },
        }


class DisaggregatedStratumSerializer(serializers.Serializer):
    """

    Class Name: DisaggregatedStratumSerializer

    Class Description:
    This class is a serializer for the DisaggregatedStratum model. It is responsible for validating and serializing the data for a DisaggregatedStratum object.

    Attributes:
    - uuid: A UUIDField that represents the UUID of the DisaggregatedStratum object. It is required.
    - date: A DateField that represents the date of the DisaggregatedStratum object. It is required.
    - value: An IntegerField that represents the value of the DisaggregatedStratum object. It is required and must be greater than or equal to 0.

    Methods:
    - validate: A method that validates the attributes of the serializer. It converts the 'uuid' and 'date' attributes to strings before returning the validated attributes.

    """
    uuid = serializers.UUIDField(required=True)
    date = serializers.DateField(required=True)
    value = serializers.IntegerField(validators=[MinValueValidator(0, _("Minimum value is 1. "))],
                                     required=True)

    def validate(self, attrs: dict) -> dict:
        # in order to store into the JSONField
        attrs['uuid'] = str(attrs['uuid'])
        attrs['date'] = str(attrs['date'])
        return attrs


class OSMNameSerializer(serializers.ModelSerializer):
    """
    Class: OSMNameSerializer

    The OSMNameSerializer class is responsible for serializing and deserializing OSMName objects.

    Attributes:
    - id: An IntegerIDField that allows updating. It is not required.

    Methods:
    - validate(attrs: dict) -> dict:
        Validates the attributes of the object and returns the validated attributes as a dictionary.
        If the 'country' attribute is not provided, it retrieves the country from the 'country_code' attribute.
        If the country is not found, it raises a ValidationError with the message 'Country field is required'.
        Returns the validated attributes as a dictionary.

    Meta:
    - model: The OSMName model that the serializer is based on.
    - fields: A string that specifies all fields to include in the serialized output.
      The value '__all__' means all fields are included.
    - extra_kwargs: A dictionary that allows specifying extra attributes for certain fields.
      In this case, it specifies that the 'uuid' field is required and has no validators.

    Note:
    - In some cases, the osmname API does not provide the 'country' attribute.
      In this case, the country is obtained from the 'country_code' attribute.
    """
    # to allow updating
    id = IntegerIDField(required=False)
    country = CharField(required=False, allow_blank=True)

    def validate(self, attrs: dict) -> dict:
        '''
        NOTE: In some cases osmname api does not provides country,
        in this case get country from country code
        '''
        if not self.instance and not attrs.get('country'):
            country_code = attrs.get('country_code', '').upper()
            country = Country.objects.filter(iso2__iexact=country_code).first()
            if not country:
                raise serializers.ValidationError('Country field is required.')
            attrs['country'] = country
        return attrs

    class Meta:
        model = OSMName
        fields = '__all__'
        extra_kwargs = {
            'uuid': {
                'validators': [],
                'required': True
            },
        }


class CommonFigureValidationMixin:
    """
    Class: CommonFigureValidationMixin

    Mixin class for validating figure data.

    Methods:
    1. validate_disaggregation_age(self, age_groups)
       - Validates the age groups in the disaggregation data.
       - Parameters:
         - age_groups (list): List of dictionaries containing age range and sex information.
       - Returns:
         - Validated age groups.

    2. _validate_unit_and_household_size(self, instance, attrs)
       - Validates the unit and household size fields.
       - Parameters:
         - instance: Figure model instance.
         - attrs: Dictionary containing figure attributes.
       - Returns:
         - Dictionary of validation errors.

    3. _validate_figure_geo_locations(self, instance, attrs)
       - Validates the figure's geo locations.
       - Parameters:
         - instance: Figure model instance.
         - attrs: Dictionary containing figure attributes.
       - Returns:
         - Dictionary of validation errors.

    4. _validate_disaggregated_sum_against_total_figures(self, instance, attrs, fields, verbose_names)
       - Validates the sum of disaggregated figures against the total figures.
       - Parameters:
         - instance: Figure model instance.
         - attrs: Dictionary containing figure attributes.
         - fields: List of field names for disaggregated figures.
         - verbose_names: List of verbose names for the disaggregated figures.
       - Returns:
         - Dictionary of validation errors.

    5. _validate_disaggregated_json_sum_against_total_figures(self, instance, attrs, field, verbose_name)
       - Validates the sum of disaggregated JSON figures against the total figures.
       - Parameters:
         - instance: Figure model instance.
         - attrs: Dictionary containing figure attributes.
         - field: Field name for the JSON field containing disaggregated figures.
         - verbose_name: Verbose name for the disaggregated figures.
       - Returns:
         - Dictionary of validation errors.

    6. _validate_geo_locations(self, instance, attrs) -> dict
       - Validates the figure's geo locations.
       - Parameters:
         - instance: Figure model instance.
         - attrs: Dictionary containing figure attributes.
       - Returns:
         - Dictionary of validation errors.

    7. _validate_figure_country(self, instance, attrs)
       - Validates the figure's country.
       - Parameters:
         - instance: Figure model instance.
         - attrs: Dictionary containing figure attributes.
       - Returns:
         - Dictionary of validation errors.

    8. _validate_dates(self, instance, attrs)
       - Validates the figure's dates.
       - Parameters:
         - instance: Figure model instance.
         - attrs: Dictionary containing figure attributes.
       - Returns:
         - Dictionary of validation errors.

    9. _validate_idu(self, instance, attrs)
       - Validates the include_idu field and excerpt_idu field.
       - Parameters:
         - instance: Figure model instance.
         - attrs: Dictionary containing figure attributes.
       - Returns:
         - Dictionary of validation errors.

    10. _validate_figure_cause(self, instance, attrs)
        - Validates the figure's cause.
        - Parameters:
          - instance: Figure model instance.
          - attrs: Dictionary containing figure attributes.
        - Returns:
          - Dictionary of validation errors

    11. clean_total_figures(self, instance, attrs)
        - Calculates the total figures based on unit and reported values.
        - Parameters:
          - instance: Figure model instance.
          - attrs: Dictionary containing figure attributes.
        - Returns:
          - Updated dictionary of attributes.

    12. clean_term_with_displacement_occur(self, instance, attrs)
        - Cleans the term with displacement occurred field.
        - Parameters:
          - instance: Figure model instance.
          - attrs: Dictionary containing figure attributes.
        - Returns:
          - Updated dictionary of attributes.

    13. _update_parent_fields(self, attrs)
        - Updates the parent fields based on sub type fields.
        - Parameters:
          - attrs: Dictionary containing figure attributes.
        - Returns:
          - None.

    14. validate(self, attrs: dict) -> dict
        - Validates the figure attributes.
        - Parameters:
          - attrs: Dictionary containing figure attributes.
        - Returns:
          - Dictionary of validation errors.
    """
    def validate_disaggregation_age(self, age_groups):
        age_groups = age_groups or []
        values = []
        for each in age_groups:
            values.append((each.get('age_from'), each.get('age_to'), each.get('sex')))
        if len(values) != len(set(values)):
            raise serializers.ValidationError('Please provide unique age range and sex.')
        return age_groups

    def _validate_unit_and_household_size(self, instance, attrs):
        errors = OrderedDict()

        unit = attrs.get('unit', getattr(instance, 'unit', Figure.UNIT.PERSON))
        household_size = attrs.get('household_size', getattr(instance, 'household_size', 0))

        if unit == Figure.UNIT.HOUSEHOLD and not household_size:
            errors.update({
                'household_size': 'Please pass in household size for household unit.'
            })
        return errors

    def _validate_figure_geo_locations(self, instance, attrs):
        errors = OrderedDict()
        # Skip on update
        if instance and 'geo_locations' not in attrs:
            return errors
        country = attrs.get('country')
        geo_locations = attrs.get('geo_locations', None)
        if not country and instance:
            country = instance.country
        if not geo_locations:
            errors.update({
                'geo_locations': 'This field is required.'
            })
            return errors
        country_code = country.iso2
        if not country_code:
            # ignore iso2 validation if missing
            return errors
        for location in geo_locations:
            # If location is moved manually allow to save location of other coutries
            # These locations are considered as problematic border issues
            moved = location.get("moved", False)
            if country_code not in Figure.SUPPORTED_OSMNAME_COUNTRY_CODES:
                continue
            elif location.get("country_code", '').lower() != country_code.lower() and not moved:
                errors.update({
                    'geo_locations': "Location should be inside the selected figure's country"
                })
        return errors

    def _validate_disaggregated_sum_against_total_figures(self, instance, attrs, fields, verbose_names):
        def _format_message(fields, verbose_names):
            if len(fields) > 1:
                return f'Sum of {verbose_names} figures is greater than total figures.'
            return f'{verbose_names} figures is greater than total figures.'

        errors = OrderedDict()

        total_figures = attrs.get('total_figures')

        disaggregated_sum = 0
        for field in fields:
            disaggregated_sum += attrs.get(field, getattr(instance, field, 0)) or 0

        if disaggregated_sum > total_figures:
            errors.update({
                field: _format_message(fields, verbose_names)
                for field in fields
            })
        return errors

    def _validate_disaggregated_json_sum_against_total_figures(self, instance, attrs, field, verbose_name):
        errors = OrderedDict()

        total_figures = attrs.get('total_figures')

        json_field = attrs.get(field) or getattr(instance, field, None) or []
        if not isinstance(json_field, list):
            return errors
        total = sum([item['value'] for item in json_field])

        if total > total_figures:
            errors.update({
                field: f'Sum of {verbose_name} figures is greater than total figures.'
            })
        return errors

    def _validate_geo_locations(self, instance, attrs) -> dict:
        _attrs = copy(attrs)
        errors = OrderedDict()

        geo_locations = _attrs.get('geo_locations', None)

        # FIXME: why only check when creating entry
        if instance and geo_locations:
            geo_location_ids = {geo_location['id'] for geo_location in geo_locations if 'id' in geo_location}
            geo_locations_on_db = list(
                instance.geo_locations.values_list('id', flat=True)
            ) if instance.geo_locations else []
            if geo_location_ids.difference(geo_locations_on_db):
                errors['geo_locations'] = 'Some geo locations not found.'

        return errors

    def _validate_figure_country(self, instance, attrs):
        _attrs = copy(attrs)
        errors = OrderedDict()

        event = attrs.get('event', getattr(instance, 'event', None))

        if event:
            errors.update(is_child_parent_inclusion_valid(
                _attrs,
                instance,
                'country',
                'event.countries',
            ))
        return errors

    def _validate_dates(self, instance, attrs):
        errors = OrderedDict()
        event = attrs.get('event', getattr(instance, 'event', None))

        if event:
            errors.update(is_child_parent_dates_valid(
                attrs.get('start_date', getattr(instance, 'start_date', None)),
                attrs.get('end_date', getattr(instance, 'end_date', None)),
                event.start_date,
                'event',
            ))
        return errors

    def _validate_idu(self, instance, attrs):
        errors = OrderedDict()
        if attrs.get('include_idu', getattr(instance, 'include_idu', None)):
            excerpt_idu = attrs.get('excerpt_idu', getattr(instance, 'excerpt_idu', None))
            if excerpt_idu is None or not excerpt_idu.strip():
                errors['excerpt_idu'] = gettext('This field is required.')
        return errors

    def _validate_figure_cause(self, instance, attrs):
        errors = OrderedDict()

        # Skip on update if not provided
        if instance and 'figure_cause' not in attrs:
            return errors

        event = attrs.get('event', getattr(instance, 'event', None))
        figure_cause = attrs.get('figure_cause', getattr(instance, 'figure_cause', None))

        if figure_cause and event and event.event_type.value != figure_cause:
            errors.update({
                'figure_cause': f'Figure cause should be {event.event_type.label}'
            })
        return errors

    def clean_total_figures(self, instance, attrs):
        _attrs = copy(attrs)
        if instance:
            unit = _attrs.get('unit', instance.unit) or Figure.UNIT.PERSON
            reported = _attrs.get('reported', instance.reported) or 0
            household_size = _attrs.get('household_size', instance.household_size) or 0
        else:
            unit = _attrs.get('unit') or Figure.UNIT.PERSON
            reported = _attrs.get('reported') or 0
            household_size = _attrs.get('household_size') or 0

        total_figures = 0
        if unit == Figure.UNIT.HOUSEHOLD:
            total_figures = round_half_up(reported * Decimal(str(household_size)))
        else:
            total_figures = reported
        _attrs['total_figures'] = total_figures

        return _attrs

    def clean_term_with_displacement_occur(self, instance, attrs):
        _attrs = copy(attrs)

        term = _attrs.get('term', getattr(instance, 'term', None))
        if term is None or term not in Figure.displacement_occur_list():
            _attrs['displacement_occurred'] = None
        return _attrs

    def _update_parent_fields(self, attrs):
        disaster_sub_type = attrs.get('disaster_sub_type', self.instance and self.instance.disaster_sub_type)
        violence_sub_type = attrs.get('violence_sub_type', self.instance and self.instance.violence_sub_type)

        attrs['disaster_category'] = None
        attrs['disaster_type'] = None
        attrs['disaster_sub_category'] = None
        attrs['violence'] = None

        if disaster_sub_type:
            disaster_type = disaster_sub_type.type
            attrs['disaster_type'] = disaster_type
            if disaster_type:
                disaster_sub_category = disaster_type.disaster_sub_category
                attrs['disaster_sub_category'] = disaster_sub_category
                if disaster_sub_category:
                    attrs['disaster_category'] = disaster_sub_category.category

        if violence_sub_type:
            attrs['violence'] = violence_sub_type.violence

    def validate(self, attrs: dict) -> dict:
        instance = None
        if attrs.get('id'):
            instance = Figure.objects.get(id=attrs['id'])

        attrs = super().validate(attrs)

        errors = OrderedDict()

        # NOTE: calculate attributes
        attrs = self.clean_total_figures(instance, attrs)
        attrs = self.clean_term_with_displacement_occur(instance, attrs)

        errors.update(self._validate_idu(instance, attrs))
        errors.update(self._validate_unit_and_household_size(instance, attrs))
        errors.update(self._validate_geo_locations(instance, attrs))
        errors.update(self._validate_dates(instance, attrs))
        errors.update(self._validate_figure_country(instance, attrs))
        errors.update(self._validate_figure_geo_locations(instance, attrs))
        errors.update(self._validate_disaggregated_sum_against_total_figures(
            instance, attrs, ['disaggregation_location_camp', 'disaggregation_location_non_camp'], 'camp and non-camp'
        ))
        errors.update(self._validate_disaggregated_sum_against_total_figures(
            instance, attrs, ['disaggregation_displacement_urban', 'disaggregation_displacement_rural'], 'urban and rural'
        ))
        errors.update(self._validate_disaggregated_sum_against_total_figures(
            instance, attrs, ['disaggregation_disability'], 'Disability',
        ))
        errors.update(self._validate_disaggregated_sum_against_total_figures(
            instance, attrs, ['disaggregation_indigenous_people'], 'Indigenous people',
        ))
        errors.update(self._validate_disaggregated_json_sum_against_total_figures(
            instance, attrs, 'disaggregation_age', 'age',
        ))
        errors.update(self._validate_figure_cause(instance, attrs))

        self._update_parent_fields(attrs)
        if errors:
            raise ValidationError(errors)

        return attrs


class FigureTagSerializer(MetaInformationSerializerMixin, serializers.ModelSerializer):
    """

    """
    class Meta:
        model = FigureTag
        fields = '__all__'


class FigureSerializer(
    MetaInformationSerializerMixin,
    CommonFigureValidationMixin,
    serializers.ModelSerializer,
):
    """
    Define a class called `FigureSerializer` that serializes and deserializes instances of the `Figure` model.

    Attributes:
    - `id`: An `IntegerField` representing the ID of the figure (optional).
    - `disaggregation_age`: A `DisaggregatedAgeSerializer` that serializes and deserializes instances of the `DisaggregatedAge` model (many, optional, not nullable).
    - `geo_locations`: An `OSMNameSerializer` that serializes and deserializes instances of the `OSMName` model (many, optional, not nullable).
    - `Meta`: A nested class that contains metadata for the serializer, including the `model` (set to `Figure`), `fields` (a list of field names to include in serialization), and `extra_kwargs` (extra options for specific fields).

    Methods:
    - `create(self, validated_data: dict) -> Figure`: Creates a new `Figure` instance with the provided validated data. This method adds the currently authenticated user as the `created_by` field and handles related models such as `geo_locations`, `tags`, `context_of_violence`, `disaggregation_age`, and `sources`. It also sends notifications and updates the `BulkUpdateFigureManager`.
    - `_update_locations(self, instance, attr: str, data: list)`: Private method that updates the `geo_locations` field of the given `instance` with the provided `data`. It handles creating, updating, and deleting related `OSMName` instances.
    - `_update_disaggregation_age(self, instance, attr: str, data: list)`: Private method that updates the `disaggregation_age` field of the given `instance` with the provided `data`. It handles creating, updating, and deleting related `DisaggregatedAge` instances.
    - `_send_event_change_notification(self, figure, existing_event, new_event)`: Private method that sends notifications when the `event` field of the given `figure` is changed.
    - `update(self, instance: Figure, validated_data)`: Updates an existing `Figure` instance with the provided validated data. This method handles updates to the `geo_locations`, `disaggregation_age`, `tags`, `context_of_violence`, and `sources` fields. It also sends notifications, updates the `BulkUpdateFigureManager`, and updates the `Figure` status.

    Note: This documentation does not include example code."""
    id = IntegerIDField(required=False)
    disaggregation_age = DisaggregatedAgeSerializer(many=True, required=False, allow_null=False)
    geo_locations = OSMNameSerializer(many=True, required=False, allow_null=False)

    class Meta:
        model = Figure
        fields = [
            'id',
            'entry',
            'quantifier',
            'reported',
            'unit',
            'household_size',
            'category',
            'term',
            'displacement_occurred',
            'role',
            'start_date',
            'start_date_accuracy',
            'end_date',
            'end_date_accuracy',
            'include_idu',
            'excerpt_idu',
            'country',
            'is_disaggregated',
            'is_housing_destruction',
            'calculation_logic',
            'tags',
            'source_excerpt',
            'event',
            'context_of_violence',
            'figure_cause',
            'violence_sub_type',
            'disaster_sub_category',
            'disaster_sub_type',
            'other_sub_type',
            'osv_sub_type',
            'sources',
            # UUID abstract fields
            'uuid',
            # Figure disaggregation abstract fields
            'disaggregation_displacement_urban',
            'disaggregation_displacement_rural',
            'disaggregation_location_camp',
            'disaggregation_location_non_camp',
            'disaggregation_lgbtiq',
            'disaggregation_disability',
            'disaggregation_indigenous_people',
            'disaggregation_sex_male',
            'disaggregation_sex_female',
            'disaggregation_age',
            'disaggregation_conflict',
            'disaggregation_conflict_political',
            'disaggregation_conflict_criminal',
            'disaggregation_conflict_communal',
            'disaggregation_conflict_other',
            'disaggregation_age',
            'geo_locations'
        ]
        extra_kwargs = {
            'uuid': {
                'validators': [],
                'required': True
            },
            'entry': {
                'validators': [],
                'required': True
            },
        }

    def create(self, validated_data: dict) -> Figure:
        validated_data['created_by'] = self.context['request'].user
        geo_locations = validated_data.pop('geo_locations', [])
        tags = validated_data.pop('tags', [])
        context_of_violence = validated_data.pop('context_of_violence', [])
        disaggregation_ages = validated_data.pop('disaggregation_age', [])
        sources = validated_data.pop('sources', [])
        if geo_locations:
            geo_locations = OSMName.objects.bulk_create(
                [OSMName(**each) for each in geo_locations]
            )

        if disaggregation_ages:
            disaggregation_ages = DisaggregatedAge.objects.bulk_create(
                [DisaggregatedAge(**age_dict) for age_dict in disaggregation_ages]
            )
        instance = Figure.objects.create(**validated_data)
        instance.geo_locations.set(geo_locations)
        instance.tags.set(tags)
        instance.context_of_violence.set(context_of_violence)
        instance.disaggregation_age.set(disaggregation_ages)
        instance.sources.set(sources)

        # Notification create
        if notification_type := get_figure_notification_type(instance.event, is_new=True):
            send_figure_notifications(instance, self.context['request'].user, notification_type)
        bulk_manager: BulkUpdateFigureManager = self.context['bulk_manager']
        bulk_manager.add_event(instance.event_id)
        return instance

    def _update_locations(self, instance, attr: str, data: list):
        osms = []
        if data:
            getattr(instance, attr).exclude(
                id__in=[each['id'] for each in data if 'id' in each]
            ).delete()
            for each in data:
                if not each.get('id'):
                    osm_serializer = OSMNameSerializer()
                    osm_serializer._validated_data = {**each}
                else:
                    osm_serializer = OSMNameSerializer(
                        instance=getattr(instance, attr).get(id=each['id']),
                        # instance=OSMName.objects.get(id=each['id']),
                        partial=True
                    )
                    osm_serializer._validated_data = {**each}
                osm_serializer._errors = {}
                osms.append(osm_serializer.save())
        getattr(instance, attr).set(osms)

    def _update_disaggregation_age(self, instance, attr: str, data: list):
        disaggregation_age = []
        if data:
            getattr(instance, attr).exclude(
                id__in=[each['id'] for each in data if 'id' in each]
            ).delete()
            for each in data:
                if not each.get('id'):
                    age_serializer = DisaggregatedAgeSerializer()
                    age_serializer._validated_data = {**each}
                else:
                    age_serializer = DisaggregatedAgeSerializer(
                        instance=getattr(instance, attr).get(id=each['id']),
                        partial=True
                    )
                    age_serializer._validated_data = {**each}
                age_serializer._errors = {}
                disaggregation_age.append(age_serializer.save())
        getattr(instance, attr).set(disaggregation_age)

    def _send_event_change_notification(self, figure, existing_event, new_event):
        # Send notifications
        # -- Delete notification
        if notification_type := get_event_notification_type(existing_event, is_figure_deleted=True):
            send_figure_notifications(
                figure,
                self.context['request'].user,
                notification_type,
                event=existing_event,
            )
        # -- Create notification
        if notification_type := get_event_notification_type(new_event, is_figure_new=True):
            send_figure_notifications(
                figure,
                self.context['request'].user,
                notification_type,
                event=new_event,
            )

    def update(self, instance: Figure, validated_data):
        validated_data['last_modified_by'] = self.context['request'].user
        # Event change tracking
        existing_event = instance.event

        with transaction.atomic():
            if 'geo_locations' in validated_data:
                geo_locations = validated_data.pop('geo_locations')
                self._update_locations(instance=instance, attr='geo_locations', data=geo_locations)
            if 'disaggregation_age' in validated_data:
                disaggregation_age = validated_data.pop('disaggregation_age')
                self._update_disaggregation_age(
                    instance=instance,
                    attr="disaggregation_age",
                    data=disaggregation_age
                )
            if 'tags' in validated_data:
                tags = validated_data.pop('tags')
                instance.tags.set(tags)
            if 'context_of_violence' in validated_data:
                context_of_violence = validated_data.pop('context_of_violence')
                instance.context_of_violence.set(context_of_violence)
            if 'sources' in validated_data:
                sources = validated_data.pop('sources')
                instance.sources.set(sources)
            instance = super().update(instance, validated_data)

        Figure.update_figure_status(instance)

        bulk_manager: BulkUpdateFigureManager = self.context['bulk_manager']
        if existing_event != instance.event:
            bulk_manager.add_event(existing_event.pk)
            self._send_event_change_notification(instance, existing_event, instance.event)
        else:
            # NOTE: We do not send notification when figure is updated if
            # the figure's event has been updated
            if notification_type := get_figure_notification_type(instance.event):
                send_figure_notifications(instance, self.context['request'].user, notification_type)
        bulk_manager.add_event(instance.event_id)
        return instance


class EntryCreateSerializer(
    MetaInformationSerializerMixin,
    serializers.ModelSerializer,
):
    """
    Serializer class for creating a new Entry object.

    This class inherits from MetaInformationSerializerMixin
    and serializers.ModelSerializer.

    Attributes:
        Meta (class): Inner class to define model and exclude fields.
            model (class): The model class to be serialized.
            exclude (tuple): Fields to be excluded from serialization.

    Methods:
        validate_figures(figures): Validates the figures field.
        validate_calculation_logic(value): Validates the calculation_logic field.
        validate(attrs: dict) -> dict: Validates the entire serializer data.

    """
    class Meta:
        model = Entry
        exclude = (
            'review_status',
            'old_id',
            'version_id',
        )

    def validate_figures(self, figures):
        if len(figures) > Entry.FIGURES_PER_ENTRY:
            raise serializers.ValidationError(
                gettext('Too many figures. Limit is %s. Please contact the administrator.' % Entry.FIGURES_PER_ENTRY)
            )
        uuids = [figure['uuid'] for figure in figures]
        if len(uuids) != len(set(uuids)):
            raise serializers.ValidationError(gettext('Duplicate keys found. '))
        geo_uuids = [loc['uuid'] for figure in figures for loc in figure.get('geo_locations', [])]
        if len(geo_uuids) != len(set(geo_uuids)):
            raise serializers.ValidationError(gettext('Duplicate geolocation keys found. '))
        if self.instance:
            if {each['id'] for each in figures if 'id' in each}.difference(
                    list(self.instance.figures.values_list('id', flat=True))
            ):
                raise serializers.ValidationError(gettext('Some figures you are trying to update does'
                                                  'not exist.'))
        return figures

    def validate_calculation_logic(self, value):
        if not value:
            raise serializers.ValidationError(_('This field is required'))
        return value

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        errors = OrderedDict()
        errors.update(Entry.clean_url_and_document(attrs, self.instance))
        if errors:
            raise ValidationError(errors)
        return attrs


class EntryUpdateSerializer(UpdateSerializerMixin,
                            EntryCreateSerializer):
    """
    This class, EntryUpdateSerializer, is a serializer used for updating an entry.

    Attributes:
        id (IntegerField): The ID of the entry to be updated.

    """
    id = IntegerIDField(required=True)


class FigureTagCreateSerializer(MetaInformationSerializerMixin,
                                serializers.ModelSerializer):
    """
    Serializer for creating a FigureTag instance.

    This serializer extends MetaInformationSerializerMixin and ModelSerializer to provide a way to serialize and validate FigureTag data when creating a new instance.

    Attributes:
        Meta (class): Inner class that defines the metadata options for the serializer.

        model (class): Specifies the model class that the serializer is based on, which in this case is FigureTag.

        fields (str or tuple): Specifies the fields to include in the serialized output. Using '__all__' includes all fields.

    """
    class Meta:
        model = FigureTag
        fields = '__all__'


class FigureTagUpdateSerializer(UpdateSerializerMixin,
                                FigureTagCreateSerializer):
    """
    Serializer for updating a figure tag.

    Inherits from the UpdateSerializerMixin and FigureTagCreateSerializer classes.

    Attributes:
        id (integer): The ID of the figure tag to be updated.

    """
    id = IntegerIDField(required=True)


class FigureReadOnlySerializer(serializers.ModelSerializer):
    """
    Serializer for the FigureReadOnlySerializer class.

    Serializes the Figure model into a JSON representation.

    Attributes:
        country (serializers.CharField): Serializes the 'country_name' field of the Figure model.
        iso3 (serializers.CharField): Serializes the 'iso3' field of the Figure model.
        latitude (serializers.FloatField): Serializes the 'centroid_lat' field of the Figure model as a float.
        longitude (serializers.FloatField): Serializes the 'centroid_lon' field of the Figure model as a float.
        centroid (serializers.CharField): Serializes the 'centroid' field of the Figure model.
        displacement_type (serializers.CharField): Serializes the 'figure_cause' field of the Figure model.
        qualifier (serializers.CharField): Serializes the 'quantifier_label' field of the Figure model.
        figure (serializers.IntegerField): Serializes the 'total_figures' field of the Figure model as an integer.
        displacement_start_date (serializers.CharField): Serializes the 'displacement_start_date' field of the Figure model.
        displacement_end_date (serializers.CharField): Serializes the 'displacement_end_date' field of the Figure model.
        displacement_date (serializers.CharField): Serializes the 'displacement_date' field of the Figure model.
        event_name (serializers.CharField): Serializes the 'event_name' field of the Figure model.
        event_codes (serializers.CharField): Serializes the 'event_codes' field of the Figure model.
        event_code_types (serializers.CharField): Serializes the 'event_code_types' field of the Figure model.
        event_start_date (serializers.CharField): Serializes the 'event_start_date' field of the Figure model.
        event_end_date (serializers.CharField): Serializes the 'event_end_date' field of the Figure model.
        category (serializers.CharField): Serializes the 'disaster_category_name' field of the Figure model.
        subcategory (serializers.CharField): Serializes the 'disaster_sub_category_name' field of the Figure model.
        type (serializers.CharField): Serializes the 'disaster_type_name' field of the Figure model.
        subtype (serializers.CharField): Serializes the 'disaster_sub_type_name' field of the Figure model.
        year (serializers.IntegerField): Serializes the 'year' field of the Figure model as an integer.
        standard_popup_text (serializers.CharField): Serializes the 'standard_popup_text' field of the Figure model.
        standard_info_text (serializers.CharField): Serializes the 'standard_info_text' field of the Figure model.
        role (serializers.CharField): Serializes the 'role' field of the Figure model.
        sources (serializers.CharField): Serializes the 'sources_name' field of the Figure model.
        source_url (serializers.CharField): Serializes the 'entry_url_or_document_url' field of the Figure model.
        locations_name (serializers.CharField): Serializes the 'locations_name' field of the Figure model.
        locations_coordinates (serializers.CharField): Serializes the 'locations_coordinates' field of the Figure model.
        locations_accuracy (serializers.CharField): Serializes the 'locations_accuracy' field of the Figure model.
        locations_type (serializers.CharField): Serializes the 'locations_type' field of the Figure model.
        displacement_occurred (serializers.CharField): Serializes the 'displacement_occurred_transformed' field of the Figure model.

        Meta (class): Meta class for configuring the serializer.

    """
    country = serializers.CharField(source='country_name')
    iso3 = serializers.CharField()
    latitude = serializers.FloatField(source='centroid_lat')
    longitude = serializers.FloatField(source='centroid_lon')
    centroid = serializers.CharField()
    displacement_type = serializers.CharField(source='figure_cause')
    qualifier = serializers.CharField(source='quantifier_label')
    figure = serializers.IntegerField(source='total_figures')
    displacement_start_date = serializers.CharField()
    displacement_end_date = serializers.CharField()
    displacement_date = serializers.CharField()
    event_name = serializers.CharField()
    event_codes = serializers.CharField()
    event_code_types = serializers.CharField()
    event_start_date = serializers.CharField()
    event_end_date = serializers.CharField()
    category = serializers.CharField(source='disaster_category_name')
    subcategory = serializers.CharField(source='disaster_sub_category_name')
    type = serializers.CharField(source='disaster_type_name')
    subtype = serializers.CharField(source='disaster_sub_type_name')
    year = serializers.IntegerField()
    standard_popup_text = serializers.CharField()
    standard_info_text = serializers.CharField()
    role = serializers.CharField()
    sources = serializers.CharField(source='sources_name')
    source_url = serializers.CharField(source='entry_url_or_document_url')
    locations_name = serializers.CharField()
    locations_coordinates = serializers.CharField()
    locations_accuracy = serializers.CharField()
    locations_type = serializers.CharField()
    displacement_occurred = serializers.CharField(source='displacement_occurred_transformed')

    class Meta:
        model = Figure
        fields = (
            'id',
            'country',
            'iso3',
            'latitude',
            'longitude',
            'centroid',
            'role',
            'displacement_type',
            'qualifier',
            'figure',
            'displacement_date',
            'displacement_start_date',
            'displacement_end_date',
            'year',
            'event_id',
            'event_name',
            'event_codes',
            'event_code_types',
            'event_start_date',
            'event_end_date',
            'category',
            'subcategory',
            'type',
            'subtype',
            'standard_popup_text',
            'standard_info_text',
            'old_id',
            'sources',
            'source_url',
            'locations_name',
            'locations_coordinates',
            'locations_accuracy',
            'locations_type',
            'displacement_occurred',
            'created_at',
        )

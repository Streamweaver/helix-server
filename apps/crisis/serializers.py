from collections import OrderedDict

from django.db.models import Min, Max, Q
from django.utils.translation import gettext
from rest_framework import serializers

from apps.crisis.models import Crisis
from apps.contrib.serializers import UpdateSerializerMixin, IntegerIDField, MetaInformationSerializerMixin
from apps.country.models import Country
from apps.event.models import Event


class CrisisSerializer(serializers.ModelSerializer, MetaInformationSerializerMixin):
    """

    CrisisSerializer class

    Serializes Crisis model instances and validates the data.

    Methods:
    - validate_dates: Validates the start_date and end_date fields to make sure the start date is smaller than the end date. Returns a dictionary of any validation errors.
    - validate_event_dates: Validates the start_date and end_date fields by comparing them with the dates of the related events. Returns a dictionary of any validation errors.
    - validate_event_countries: Validates the countries field by comparing it with the countries of the related events. Returns a dictionary of any validation errors.
    - validate_event_types: Validates the crisis_type field by comparing it with the event_type of the related events. Returns a dictionary of any validation errors.
    - validate_empty_countries: Validates the countries field to make sure it is not empty if there are no existing countries for the crisis. Returns a dictionary of any validation errors.
    - validate: Validates the overall data by calling the above validation methods. Raises a serializers.ValidationError if there are any validation errors.
    - create: Creates a new Crisis object using the validated data. Sets the created_by field to the current user and assigns the related countries if provided.
    - update: Not implemented. Raises a NotImplementedError.

    Note:
    - This class extends the ModelSerializer and MetaInformationSerializerMixin classes.
    - The Meta class specifies the Crisis model and the fields to be serialized ('__all__').
    - The class also includes docstrings for each method to describe their purpose and return values.

    """
    class Meta:
        model = Crisis
        fields = '__all__'

    def validate_dates(self, attrs):
        errors = OrderedDict()

        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        if start_date and end_date and end_date < start_date:
            errors['start_date'] = 'Start date should be smaller than end date.'

        return errors

    def validate_event_dates(self, attrs):
        errors = OrderedDict()
        if not self.instance:
            return errors

        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        _ = Event.objects.filter(
            crisis=self.instance,
        ).aggregate(
            min_date=Min(
                'start_date',
                filter=Q(
                    start_date__isnull=False,
                )
            ),
            max_date=Max(
                'end_date',
                filter=Q(
                    end_date__isnull=False,
                )
            ),
        )
        min_event_start_date = _['min_date']
        max_event_end_date = _['max_date']

        if start_date and (min_event_start_date and min_event_start_date < start_date):
            errors['start_date'] = gettext('Earliest start date of one of the events is %s.') % min_event_start_date
        if end_date and (max_event_end_date and end_date < max_event_end_date):
            errors['end_date'] = gettext('Farthest end date of one of the events is %s.') % max_event_end_date
        return errors

    def validate_event_countries(self, attrs):
        errors = OrderedDict()
        if not self.instance:
            return errors

        countries = [each.id for each in attrs.get('countries', [])]
        if countries is None:
            return errors
        event_countries = self.instance.events.filter(countries__isnull=False).values_list('countries', flat=True)

        if not event_countries:
            return errors
        if diffs := set(event_countries).difference(countries):
            errors['countries'] = gettext(
                'The included events have following countries not mentioned in this crisis: %s'
            ) % ', '.join([item for item in Country.objects.filter(id__in=diffs).values_list('idmc_short_name', flat=True)])
        return errors

    def validate_event_types(self, attrs):
        errors = OrderedDict()
        if not self.instance:
            return errors
        crisis_type = attrs.get('crisis_type')
        if crisis_type is None:
            return errors
        if not self.instance.events.exists():
            return errors
        # all events are bound to be the same as crisis cause
        event_type = self.instance.events.first().event_type.value
        if crisis_type != event_type:
            errors['crisis_type'] = gettext(
                'There are events with different event cause: %s'
            ) % Crisis.CRISIS_TYPE.get(event_type)
        return errors

    def validate_empty_countries(self, attrs):
        errors = OrderedDict()
        countries = attrs.get('countries', [])
        if not countries and not (self.instance and self.instance.countries.exists()):
            errors.update(dict(
                countries='This field is required.'
            ))
        return errors

    def validate(self, attrs):
        errors = OrderedDict()
        errors.update(self.validate_dates(attrs))
        errors.update(self.validate_empty_countries(attrs))
        if self.instance:
            errors.update(self.validate_event_dates(attrs))
            errors.update(self.validate_event_countries(attrs))
            errors.update(self.validate_event_types(attrs))
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        validated_data["created_by"] = self.context['request'].user
        countries = validated_data.pop("countries", None)
        crisis = Crisis.objects.create(**validated_data)
        if countries:
            crisis.countries.set(countries)
        return crisis

    def udpate(self, *a, **kw):
        raise NotImplementedError('Use `CrisisUpdateSerializer` instead')


class CrisisUpdateSerializer(UpdateSerializerMixin, CrisisSerializer):
    """
    A serializer class for updating Crisis objects.

    This serializer inherits from UpdateSerializerMixin and CrisisSerializer.

    Attributes:
        id (int): The ID of the Crisis object being updated. Required.
    """
    id = IntegerIDField(required=True)

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_enumfield import enum
from django.contrib.postgres.fields import ArrayField
from apps.contrib.commons import DATE_ACCURACY
from apps.contrib.models import MetaInformationAbstractModel
from apps.crisis.models import Crisis
from apps.entry.models import Figure, Entry


class Conflict(models.Model):
    """

    This class represents a Conflict object.

    Attributes:
        country (ForeignKey): A foreign key to the Country model, related name is 'country_conflict'. Used to determine
        the country associated with the conflict.
        total_displacement (BigIntegerField): The total displacement caused by the conflict, in terms of number of
        people affected. Can be blank or null.
        new_displacement (BigIntegerField): The new displacement caused by the conflict, in terms of number of people
        affected. Can be blank or null.
        total_displacement_rounded (BigIntegerField): The rounded value of total_displacement. Used for display and
        sorting purposes only. Can be blank or null.
        new_displacement_rounded (BigIntegerField): The rounded value of new_displacement. Used for display and sorting
        purposes only. Can be blank or null.
        year (IntegerField): The year in which the conflict occurred.
        country_name (CharField): The name of the country associated with the conflict. Used for caching and snapshot
        purposes.
        iso3 (CharField): The ISO3 code of the country associated with the conflict. Used for caching and snapshot
        purposes.
        created_at (DateTimeField): The timestamp indicating when the conflict object was created.
        updated_at (DateTimeField): The timestamp indicating when the conflict object was last updated.

    Meta:
        verbose_name (str): The verbose name of the Conflict model, used in display purposes.
        verbose_name_plural (str): The plural verbose name of the Conflict model, used in display purposes.

    Methods:
        __str__(): Return a string representation of the Conflict object, which is the ID of the conflict.
    """
    country = models.ForeignKey(
        'country.Country', related_name='country_conflict', on_delete=models.PROTECT,
        verbose_name=_('Country')
    )
    total_displacement = models.BigIntegerField(blank=True, null=True)
    new_displacement = models.BigIntegerField(blank=True, null=True)

    # Don't use these rounded fields to aggregate, just used to display and sort
    total_displacement_rounded = models.BigIntegerField(blank=True, null=True)
    new_displacement_rounded = models.BigIntegerField(blank=True, null=True)

    year = models.IntegerField()

    # Cached/Snapshot values
    country_name = models.CharField(verbose_name=_('Name'), max_length=256)
    iso3 = models.CharField(verbose_name=_('ISO3'), max_length=5)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Conflict')
        verbose_name_plural = _('Conflicts')

    def __str__(self):
        return str(self.id)


class Disaster(models.Model):
    """
    A class representing a disaster event.

    Attributes:
        event (ForeignKey): A foreign key to the Event model representing the event associated with the disaster.
        year (IntegerField): The year of the disaster.
        country (ForeignKey): A foreign key to the Country model representing the country where the disaster occurred.

        start_date (DateField): The start date of the disaster.
        start_date_accuracy (TextField): The accuracy of the start date of the disaster.
        end_date (DateField): The end date of the disaster.
        end_date_accuracy (TextField): The accuracy of the end date of the disaster.

        hazard_category (ForeignKey): A foreign key to the DisasterCategory model representing the hazard category of
        the disaster.
        hazard_sub_category (ForeignKey): A foreign key to the DisasterSubCategory model representing the hazard
        subcategory of the disaster.
        hazard_type (ForeignKey): A foreign key to the DisasterType model representing the hazard type of the disaster.
        hazard_sub_type (ForeignKey): A foreign key to the DisasterSubType model representing the hazard subtype of the
        disaster.

        new_displacement (BigIntegerField): The new displacement caused by the disaster.
        total_displacement (BigIntegerField): The total displacement caused by the disaster.

        total_displacement_rounded (BigIntegerField): The rounded total displacement value used for display and sorting.
        new_displacement_rounded (BigIntegerField): The rounded new displacement value used for display and sorting.

        created_at (DateTimeField): The timestamp indicating when the disaster was created.
        updated_at (DateTimeField): The timestamp indicating when the disaster was last updated.

        event_name (CharField): The name of the event associated with the disaster.
        iso3 (CharField): The ISO3 code of the country where the disaster occurred.
        country_name (CharField): The name of the country where the disaster occurred.
        hazard_category_name (CharField): The name of the hazard category of the disaster.
        hazard_sub_category_name (CharField): The name of the hazard subcategory of the disaster.
        hazard_sub_type_name (CharField): The name of the hazard subtype of the disaster.
        hazard_type_name (CharField): The name of the hazard type of the disaster.

        displacement_occurred (ArrayField): An array field storing the displacement occurred values associated with the
        disaster.

        glide_numbers (ArrayField) - Deprecated: An array field storing the glide numbers associated with the disaster.
        event_codes (ArrayField) - Deprecated: An array field storing the event codes associated with the disaster.
        event_codes_type (ArrayField) - Deprecated: An array field storing the event code types associated with the
        disaster.

    Meta:
        verbose_name (str): The verbose name of the Disaster class.
        verbose_name_plural (str): The plural verbose name of the Disaster class.

    Methods:
        __str__(): Returns a string representation of the Disaster object.
    """
    event = models.ForeignKey(
        'event.Event', verbose_name=_('Event'),
        related_name='gidd_events', on_delete=models.SET_NULL, null=True, blank=True
    )
    year = models.IntegerField()
    country = models.ForeignKey(
        'country.Country', related_name='country_disaster', on_delete=models.PROTECT,
        verbose_name=_('Country')
    )

    # Dates
    start_date = models.DateField(blank=True, null=True)
    start_date_accuracy = models.TextField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_date_accuracy = models.TextField(blank=True, null=True)

    hazard_category = models.ForeignKey(
        'event.DisasterCategory', verbose_name=_('Hazard Category'),
        related_name='disasters', on_delete=models.PROTECT
    )
    hazard_sub_category = models.ForeignKey(
        'event.DisasterSubCategory', verbose_name=_('Hazard Sub Category'),
        related_name='disasters', on_delete=models.PROTECT
    )
    hazard_type = models.ForeignKey(
        'event.DisasterType', verbose_name=_('Hazard Type'),
        related_name='disasters', on_delete=models.PROTECT
    )
    hazard_sub_type = models.ForeignKey(
        'event.DisasterSubType', verbose_name=_('Hazard Sub Type'),
        related_name='disasters', on_delete=models.PROTECT
    )

    new_displacement = models.BigIntegerField(blank=True, null=True)
    total_displacement = models.BigIntegerField(blank=True, null=True)

    # Don't use these rounded fields to aggregate, just used to display and sort
    total_displacement_rounded = models.BigIntegerField(blank=True, null=True)
    new_displacement_rounded = models.BigIntegerField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Cached/Snapshot values
    event_name = models.CharField(verbose_name=_('Event name'), max_length=256)
    iso3 = models.CharField(verbose_name=_('ISO3'), max_length=5)
    country_name = models.CharField(verbose_name=_('Name'), max_length=256)
    hazard_category_name = models.CharField(max_length=256, blank=True)
    hazard_sub_category_name = models.CharField(max_length=256, blank=True)
    hazard_sub_type_name = models.CharField(max_length=256, blank=True)
    hazard_type_name = models.CharField(max_length=256, blank=True)

    displacement_occurred = ArrayField(
        base_field=enum.EnumField(
            Figure.DISPLACEMENT_OCCURRED,
            verbose_name=_('Displacement occurred'),
        ),
        default=list,
    )

    # Deprecated
    glide_numbers = ArrayField(
        models.CharField(
            verbose_name=_('Event Codes'), max_length=256
        ),
        default=list,
    )
    event_codes = ArrayField(
        models.CharField(
            verbose_name=_('Event Codes'), max_length=256
        ),
        default=list,
    )
    event_codes_type = ArrayField(
        models.CharField(
            verbose_name=_('Event Code Types'), max_length=256
        ),
        default=list,
    )

    class Meta:
        verbose_name = _('Disaster')
        verbose_name_plural = _('Disasters')

    def __str__(self):
        return str(self.id)


class StatusLog(models.Model):
    """
    The `StatusLog` class represents a model for tracking status logs. It contains information about the trigger,
    completion, and status of a log.

    Attributes:
        triggered_by (ForeignKey): Represents the user who triggered the log.
        triggered_at (DateTimeField): Represents the timestamp when the log was triggered.
        completed_at (DateTimeField): Represents the timestamp when the log was completed (can be null or blank).
        status (Status): Represents the status of the log, which can be one of the following: PENDING, SUCCESS, or
        FAILED.

        Status (enum.Enum): Represents an enumeration of possible log status values: PENDING, SUCCESS, FAILED.

            __labels__ (dict): A dictionary that maps the status enum values to their corresponding labels.

    Meta:
        permissions (tuple): Specifies the permissions for the `StatusLog` model.

    Methods:
        __str__(): Returns a string representation of the triggered timestamp.

        last_release_date(): Returns the formatted completion date of the last log entry, or None if no log entries
        exist.

    Note:
        This class inherits from the `models.Model` class provided by Django.

    Example usage:

    log = StatusLog.objects.create(
        triggered_by=user,
        triggered_at=datetime.now(),
        completed_at=datetime.now(),
        status=StatusLog.Status.SUCCESS
    )

    print(log.last_release_date())
    """
    class Status(enum.Enum):
        PENDING = 0
        SUCCESS = 1
        FAILED = 2

        __labels__ = {
            PENDING: _("Pending"),
            SUCCESS: _("Success"),
            FAILED: _("Failed"),
        }
    triggered_by = models.ForeignKey(
        'users.User', verbose_name=_('Triggered by'),
        related_name='gidd_data_triggered_by', on_delete=models.PROTECT
    )
    triggered_at = models.DateTimeField(verbose_name='Triggered at', auto_now_add=True)
    completed_at = models.DateTimeField(verbose_name='Completed at', null=True, blank=True)
    status = enum.EnumField(
        verbose_name=_('Status'), enum=Status, default=Status.PENDING
    )

    class Meta:
        permissions = (
            ('update_gidd_data_gidd', 'Can update GIDD data'),
        )

    def __str__(self):
        return str(self.triggered_at)

    @classmethod
    def last_release_date(cls):
        last_log = StatusLog.objects.last()
        return last_log.completed_at.strftime("%B %d, %Y") if last_log else None


class ConflictLegacy(models.Model):
    """

    A class representing a legacy conflict.

    Attributes:
        total_displacement (BigIntegerField): The total displacement caused by the conflict (optional, can be blank or
        null).
        new_displacement (BigIntegerField): The new displacement caused by the conflict (optional, can be blank or
        null).
        year (IntegerField): The year in which the conflict occurred.
        iso3 (CharField): The ISO3 code associated with the conflict.

    Timestamps:
        created_at (DateTimeField): The date and time when the object was created (automatically set).
        updated_at (DateTimeField): The date and time when the object was last updated (automatically updated).

    Meta:
        verbose_name (str): The singular name for the model in human-readable format.
        verbose_name_plural (str): The plural name for the model in human-readable format.

    Methods:
        __str__(): Returns a string representation of the conflict object.

    """
    total_displacement = models.BigIntegerField(blank=True, null=True)
    new_displacement = models.BigIntegerField(blank=True, null=True)
    year = models.IntegerField()
    iso3 = models.CharField(verbose_name=_('ISO3'), max_length=5)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Legacy conflict')
        verbose_name_plural = _('Legacy conflicts')

    def __str__(self):
        return str(self.id)


class DisasterLegacy(models.Model):
    """
    Class representing a legacy disaster event.

    Attributes:
        year (int): The year of the disaster event.
        iso3 (str): The ISO3 code of the country where the event occurred.
        event_name (str): The name of the event.

        start_date (date): The start date of the event (optional).
        start_date_accuracy (str): The accuracy of the start date (optional).
        end_date (date): The end date of the event (optional).
        end_date_accuracy (str): The accuracy of the end date (optional).

        hazard_category (event.DisasterCategory): The hazard category of the event.
        hazard_sub_category (event.DisasterSubCategory): The hazard sub category of the event.
        hazard_type (event.DisasterType): The hazard type of the event.
        hazard_sub_type (event.DisasterSubType): The hazard sub type of the event.

        new_displacement (int): The number of new displacements caused by the event (optional).

        created_at (datetime): The timestamp when the object was created.
        updated_at (datetime): The timestamp when the object was last updated.

    Methods:
        __str__(): Returns a string representation of the object.
    """
    year = models.IntegerField()
    iso3 = models.CharField(verbose_name=_('ISO3'), max_length=5)
    event_name = models.CharField(verbose_name=_('Event name'), max_length=256)

    # Dates
    start_date = models.DateField(blank=True, null=True)
    start_date_accuracy = models.TextField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_date_accuracy = models.TextField(blank=True, null=True)

    hazard_category = models.ForeignKey(
        'event.DisasterCategory', verbose_name=_('Hazard Category'),
        related_name='legacy_disasters', on_delete=models.PROTECT
    )
    hazard_sub_category = models.ForeignKey(
        'event.DisasterSubCategory', verbose_name=_('Hazard Sub Category'),
        related_name='legacy_disasters', on_delete=models.PROTECT
    )
    hazard_type = models.ForeignKey(
        'event.DisasterType', verbose_name=_('Hazard Type'),
        related_name='legacy_disasters', on_delete=models.PROTECT
    )
    hazard_sub_type = models.ForeignKey(
        'event.DisasterSubType', verbose_name=_('Hazard Sub Type'),
        related_name='legacy_disasters', on_delete=models.PROTECT
    )

    new_displacement = models.BigIntegerField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Legacy disaster')
        verbose_name_plural = _('Legacy disasters')

    def __str__(self):
        return str(self.id)


class ReleaseMetadata(models.Model):
    """
    Class: ReleaseMetadata

    This class represents the metadata for a release.

    Attributes:
    - release_year (int): The year of the release.
    - pre_release_year (int): The year of the pre-release.
    - modified_by (ForeignKey): A foreign key to the User model representing the user who modified the metadata.
    - modified_at (DateTimeField): The date and time when the metadata was last modified.

    Methods:
    - __str__() -> str: Returns a string representation of the release year.

    Nested Classes:
    - ReleaseEnvironment (Enum): Enumeration representing the release environment.

        Attributes:
        - PRE_RELEASE: Constant representing the pre-release environment.
        - RELEASE: Constant representing the release environment.

        Class Variables:
        - __labels__ (dict): A dictionary mapping the enum values to their corresponding labels.

    Meta Class:
    - permissions (tuple): A tuple defining the permissions for updating the release metadata.

    """
    class ReleaseEnvironment(enum.Enum):
        # XXX: Changing the attribute name will break external systems
        PRE_RELEASE = 0
        RELEASE = 1

        __labels__ = {
            RELEASE: _("Release"),
            PRE_RELEASE: _("Pre Release"),
        }

    release_year = models.IntegerField(verbose_name=_('Release year'))
    pre_release_year = models.IntegerField(verbose_name=_('Pre-Release year'))
    modified_by = models.ForeignKey(
        'users.User', verbose_name=_('Modified by'),
        related_name='+', on_delete=models.PROTECT
    )
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.release_year)

    class Meta:
        permissions = (
            ('update_release_meta_data_gidd', 'Can update release meta data'),
        )


class PublicFigureAnalysis(models.Model):
    """

    The PublicFigureAnalysis class is a Django model that represents the analysis of public figures in a specific crisis
    or event. It has the following fields:

    1. iso3 (CharField): Represents the ISO3 code of the country associated with the analysis.

    2. figure_cause (EnumField): Represents the cause of the figures in the analysis. It is an enumeration field that
    accepts values from the Crisis.CRISIS_TYPE enumeration.

    3. figure_category (EnumField): Represents the category of the figures in the analysis. It is an enumeration field
    that accepts values from the Figure.FIGURE_CATEGORY_TYPES enumeration.

    4. year (IntegerField): Represents the year of the analysis.

    5. figures (IntegerField): Represents the total number of figures in the analysis. This field allows null values.

    6. figures_rounded (IntegerField): Represents the rounded number of figures in the analysis. This field allows null
    values.

    7. description (TextField): Represents the description of the analysis. This field allows null values.

    8. report (ForeignKey): Represents the report associated with the analysis. It is a foreign key to the
    'report.Report' model. This field allows null values.

    """
    iso3 = models.CharField(verbose_name=_('ISO3'), max_length=5)
    figure_cause = enum.EnumField(Crisis.CRISIS_TYPE, verbose_name=_('Figure Cause'))
    figure_category = enum.EnumField(
        enum=Figure.FIGURE_CATEGORY_TYPES,
        verbose_name=_('Figure Category'),
    )
    year = models.IntegerField(verbose_name=_('Year'))
    figures = models.IntegerField(verbose_name=_('Figures'), null=True)
    figures_rounded = models.IntegerField(verbose_name=_('Figures rounded'), null=True)
    description = models.TextField(verbose_name=_('Description'), null=True)
    report = models.ForeignKey(
        'report.Report', verbose_name=_('Report'), null=True,
        related_name='+', on_delete=models.SET_NULL
    )


class DisplacementData(models.Model):
    """
    Model representing displacement data for a country.

    Attributes:
        iso3 (CharField): ISO3 code of the country.
        country_name (CharField): Name of the country.
        country (ForeignKey): Foreign key to the 'country.Country' model representing the country.
        conflict_total_displacement (BigIntegerField): Total displacement due to conflict (in IDPs).
        conflict_new_displacement (BigIntegerField): New displacement due to conflict (in IDPs).
        disaster_total_displacement (BigIntegerField): Total displacement due to disaster (in NDs).
        disaster_new_displacement (BigIntegerField): New displacement due to disaster (in NDs).
        year (IntegerField): Year of the displacement data.
        conflict_total_displacement_rounded (BigIntegerField): Rounded total displacement due to conflict (in IDPs).
        conflict_new_displacement_rounded (BigIntegerField): Rounded new displacement due to conflict (in IDPs).
        disaster_total_displacement_rounded (BigIntegerField): Rounded total displacement due to disaster (in NDs).
        disaster_new_displacement_rounded (BigIntegerField): Rounded new displacement due to disaster (in NDs).

    Methods:
        __str__(): Returns the ISO3 code of the country.
    """
    iso3 = models.CharField(verbose_name=_('ISO3'), max_length=5)
    country_name = models.CharField(verbose_name=_('Country name'), max_length=256)
    country = models.ForeignKey(
        'country.Country', related_name='displacements', on_delete=models.PROTECT,
        verbose_name=_('Country')
    )

    conflict_total_displacement = models.BigIntegerField(null=True, verbose_name=_('Conflict total idps'))
    conflict_new_displacement = models.BigIntegerField(null=True, verbose_name=_('Conflict total nd'))

    disaster_total_displacement = models.BigIntegerField(null=True, verbose_name=_('Disaster total nds'))
    disaster_new_displacement = models.BigIntegerField(null=True, verbose_name=_('Disaster total nd'))

    year = models.IntegerField(verbose_name=_('Year'))

    # Don't use these rounded fields to aggregate, just used to display and sort
    conflict_total_displacement_rounded = models.BigIntegerField(null=True, verbose_name=_('Conflict total idps'))
    conflict_new_displacement_rounded = models.BigIntegerField(null=True, verbose_name=_('Conflict total nd'))

    disaster_total_displacement_rounded = models.BigIntegerField(null=True, verbose_name=_('Disaster total nds'))
    disaster_new_displacement_rounded = models.BigIntegerField(null=True, verbose_name=_('Disaster total nd'))

    def __str__(self):
        return self.iso3


class IdpsSaddEstimate(models.Model):
    """
    A class to represent an IDPS sadd estimate.

    Attributes:
    - iso3: A string representing the ISO3 code of the country.
    - country_name: A string representing the name of the country.
    - country: A foreign key to the 'Country' model, representing the related country.
    - year: An integer representing the year of the estimate.
    - sex: A string representing the sex for which the estimate is made.
    - cause: An enumeration field representing the cause of the estimate.
    - zero_to_four: An integer representing the estimated number of IDPs aged 0-4.
    - five_to_eleven: An integer representing the estimated number of IDPs aged 5-11.
    - twelve_to_seventeen: An integer representing the estimated number of IDPs aged 12-17.
    - eighteen_to_fiftynine: An integer representing the estimated number of IDPs aged 18-59.
    - sixty_plus: An integer representing the estimated number of IDPs aged 60+.

    Methods:
    - __str__(): Returns the ISO3 code of the country as a string.

    """
    iso3 = models.CharField(verbose_name=_('ISO3'), max_length=5)
    country_name = models.CharField(verbose_name=_('Country name'), max_length=256)
    country = models.ForeignKey(
        'country.Country', related_name='ipds_sadd_estimates', on_delete=models.PROTECT,
        verbose_name=_('Country')
    )
    year = models.IntegerField()
    sex = models.CharField(verbose_name=_('Sex'), max_length=256)
    cause = enum.EnumField(Crisis.CRISIS_TYPE, verbose_name=_('Cause'))

    # This can be null
    zero_to_four = models.IntegerField(verbose_name=_('0-4'), null=True)
    five_to_eleven = models.IntegerField(verbose_name=_('5-11'), null=True)
    twelve_to_seventeen = models.IntegerField(verbose_name=_('12-17'), null=True)
    eighteen_to_fiftynine = models.IntegerField(verbose_name=_('18-59'), null=True)
    sixty_plus = models.IntegerField(verbose_name=_('60+'), null=True)

    def __str__(self):
        return self.iso3


class GiddEvent(MetaInformationAbstractModel):
    """
    Class GiddEvent

    This class represents a GiddEvent object. It inherits from the MetaInformationAbstractModel class.

    Attributes:
    - name: A CharField representing the name of the event.
    - event: A ForeignKey representing the associated Event object.
    - cause: An enum.EnumField representing the cause of the event.
    - start_date: A DateField representing the start date of the event.
    - start_date_accuracy: An enum.EnumField representing the accuracy of the start date.
    - end_date: A DateField representing the end date of the event.
    - end_date_accuracy: An enum.EnumField representing the accuracy of the end date.
    - glide_numbers: An ArrayField containing event codes.
    - event_codes: An ArrayField containing event codes.
    - event_codes_type: An ArrayField containing event code types.
    - event_codes_iso3: An ArrayField containing ISO3 codes for event codes.
    - event_codes_ids: An ArrayField containing event code IDs.
    - violence: A ForeignKey representing the associated Violence object.
    - violence_sub_type: A ForeignKey representing the associated ViolenceSubType object.
    - disaster_category: A ForeignKey representing the associated DisasterCategory object.
    - disaster_sub_category: A ForeignKey representing the associated DisasterSubCategory object.
    - disaster_type: A ForeignKey representing the associated DisasterType object.
    - disaster_sub_type: A ForeignKey representing the associated DisasterSubType object.
    - other_sub_type: A ForeignKey representing the associated OtherSubType object.
    - osv_sub_type: A ForeignKey representing the associated OsvSubType object.
    - violence_name: A CharField representing the name of the violence.
    - violence_sub_type_name: A CharField representing the name of the violence sub type.
    - disaster_category_name: A CharField representing the name of the disaster category.
    - disaster_sub_category_name: A CharField representing the name of the disaster sub category.
    - disaster_type_name: A CharField representing the name of the disaster type.
    - disaster_sub_type_name: A CharField representing the name of the disaster sub type.
    - other_sub_type_name: A CharField representing the name of the other sub type.
    - osv_sub_type_name: A CharField representing the name of the osv sub type.

    Methods:
    - __str__: Returns a string representation of the GiddEvent object.

    """
    name = models.CharField(verbose_name=_('Event Name'), max_length=256)
    event = models.ForeignKey(
        'event.Event', verbose_name=_('Event'),
        related_name='+', on_delete=models.SET_NULL, null=True, blank=True
    )
    cause = enum.EnumField(Crisis.CRISIS_TYPE, verbose_name=_('Cause'))
    # Dates
    start_date = models.DateField(blank=True, null=True)
    start_date_accuracy = enum.EnumField(
        DATE_ACCURACY,
        verbose_name=_('Start Date Accuracy'),
        default=DATE_ACCURACY.DAY,
        blank=True,
        null=True,
    )
    end_date = models.DateField(blank=True, null=True)
    end_date_accuracy = enum.EnumField(
        DATE_ACCURACY,
        verbose_name=_('End date accuracy'),
        blank=True,
        null=True,
    )

    # Deprecated
    glide_numbers = ArrayField(
        models.CharField(
            verbose_name=_('Event Codes'), max_length=256
        ),
        default=list,
    )
    event_codes = ArrayField(
        models.CharField(
            verbose_name=_('Event Codes'), max_length=256
        ),
        default=list,
    )
    event_codes_type = ArrayField(
        models.IntegerField(
            verbose_name=_('Event Code Types'),
        ),
        default=list,
    )
    event_codes_iso3 = ArrayField(
        models.CharField(
            verbose_name=_('Event Code ISO3'), max_length=256
        ),
        default=list,
    )
    event_codes_ids = ArrayField(
        models.IntegerField(
            verbose_name=_('Event Code IDs'),
        ),
        default=list,
    )
    violence = models.ForeignKey(
        'event.Violence', verbose_name=_('Violence'),
        blank=False, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    violence_sub_type = models.ForeignKey(
        'event.ViolenceSubType', verbose_name=_('Violence Sub Type'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    disaster_category = models.ForeignKey(
        'event.DisasterCategory', verbose_name=_('Hazard Category'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    disaster_sub_category = models.ForeignKey(
        'event.DisasterSubCategory', verbose_name=_('Hazard Sub Category'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    disaster_type = models.ForeignKey(
        'event.DisasterType', verbose_name=_('Hazard Type'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    disaster_sub_type = models.ForeignKey(
        'event.DisasterSubType', verbose_name=_('Hazard Sub Type'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    other_sub_type = models.ForeignKey(
        'event.OtherSubType', verbose_name=_('Other sub type'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL)
    osv_sub_type = models.ForeignKey(
        'event.OsvSubType', verbose_name=_('OSV sub type'),
        blank=True, null=True, related_name='+',
        on_delete=models.SET_NULL
    )

    violence_name = models.CharField(max_length=256, blank=True, null=True)
    violence_sub_type_name = models.CharField(max_length=256, blank=True, null=True)
    disaster_category_name = models.CharField(max_length=256, blank=True, null=True)
    disaster_sub_category_name = models.CharField(max_length=256, blank=True, null=True)
    disaster_type_name = models.CharField(max_length=256, blank=True, null=True)
    disaster_sub_type_name = models.CharField(max_length=256, blank=True, null=True)
    other_sub_type_name = models.CharField(max_length=256, blank=True, null=True)
    osv_sub_type_name = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.name


class GiddFigure(MetaInformationAbstractModel):
    """
    Class GiddFigure

    This class represents a GiddFigure, which is a model that contains various fields related to a figure in the GIDD
    system.

    Attributes:
    - iso3: CharField, represents the ISO3 code of the country where the figure belongs
    - figure: ForeignKey to Figure model, represents the related figure
    - country_name: CharField, represents the name of the country
    - country: ForeignKey to Country model, represents the related country
    - geographical_region_name: CharField, represents the name of the geographical region
    - term: EnumField (Figure.FIGURE_TERMS), represents the term of the figure
    - year: IntegerField, represents the year of the figure
    - unit: EnumField (Figure.UNIT), represents the unit of the figure
    - category: EnumField (Figure.FIGURE_CATEGORY_TYPES), represents the category of the figure
    - cause: EnumField (Crisis.CRISIS_TYPE), represents the cause of the figure
    - total_figures: PositiveIntegerField, represents the total figures
    - household_size: FloatField, represents the household size
    - quantifier: EnumField (Figure.QUANTIFIER), represents the quantifier
    - reported: PositiveIntegerField, represents the reported figures
    - role: EnumField (Figure.ROLE), represents the role of the figure
    - start_date: DateField, represents the start date of the figure
    - start_date_accuracy: EnumField (DATE_ACCURACY), represents the start date accuracy
    - end_date: DateField, represents the end date of the figure
    - end_date_accuracy: EnumField (DATE_ACCURACY), represents the end date accuracy
    - stock_date: DateField, represents the stock date of the figure
    - stock_date_accuracy: EnumField (DATE_ACCURACY), represents the stock date accuracy
    - stock_reporting_date: DateField, represents the stock reporting date of the figure
    - include_idu: BooleanField, represents whether the figure is included in IDU
    - excerpt_idu: TextField, represents the excerpt for IDU
    - is_confidential: BooleanField, represents whether the source of the figure is confidential
    - source_excerpt: TextField, represents the excerpt from the source
    - sources: ArrayField of CharField, represents the sources of the figure
    - sources_ids: ArrayField of IntegerField, represents the source IDs of the figure
    - sources_type: ArrayField of CharField, represents the source types of the figure
    - publishers_ids: ArrayField of IntegerField, represents the publisher IDs of the figure
    - publishers: ArrayField of CharField, represents the publishers of the figure
    - publishers_type: ArrayField of CharField, represents the publisher types of the figure
    - gidd_event: ForeignKey to GiddEvent model, represents the related GIDD event
    - entry: ForeignKey to Entry model, represents the related entry
    - entry_name: CharField, represents the title of the entry
    - context_of_violence: ArrayField of CharField, represents the context of violence
    - context_of_violence_ids: ArrayField of IntegerField, represents the context of violence IDs
    - calculation_logic: TextField, represents the analysis and calculation logic
    - tags: ArrayField of CharField, represents the tags of the figure
    - tags_ids: ArrayField of IntegerField, represents the tag IDs of the figure
    - is_housing_destruction: BooleanField, represents whether the figure is related to housing destruction
    - is_disaggregated: BooleanField, represents whether the figure is disaggregated
    - locations_ids: ArrayField of IntegerField, represents the location IDs of the figure
    - locations_coordinates: ArrayField of CharField, represents the location coordinates of the figure
    - locations_names: ArrayField of CharField, represents the location names of the figure
    - locations_accuracy: ArrayField of IntegerField, represents the location accuracy of the figure
    - locations_type: ArrayField of IntegerField, represents the location types of the figure
    - displacement_occurred: EnumField (Figure.DISPLACEMENT_OCCURRED), represents whether displacement occurred
    - violence: ForeignKey to Violence model, represents the related violence
    - violence_sub_type: ForeignKey to ViolenceSubType model, represents the related violence sub type
    - disaster_category: ForeignKey to DisasterCategory model, represents the related disaster category
    - disaster_sub_category: ForeignKey to DisasterSubCategory model, represents the related disaster sub category
    - disaster_type: ForeignKey to DisasterType model, represents the related disaster type
    - disaster_sub_type: ForeignKey to DisasterSubType model, represents the related disaster sub type
    - other_sub_type: ForeignKey to OtherSubType model, represents the related other sub type
    - osv_sub_type: ForeignKey to OsvSubType model, represents the related OSV sub type
    - violence_name: CharField, represents the name of the violence
    - violence_sub_type_name: CharField, represents the name of the violence sub type
    - disaster_category_name: CharField, represents the name of the disaster category
    - disaster_sub_category_name: CharField, represents the name of the disaster sub category
    - disaster_type_name: CharField, represents the name of the disaster type
    - disaster_sub_type_name: CharField, represents the name of the disaster sub type
    - other_sub_type_name: CharField, represents the name of the other sub type
    - osv_sub_type_name: CharField, represents the name of the OSV sub type

    Methods:
    - __str__: Returns the ISO3 code of the GiddFigure

    """
    iso3 = models.CharField(verbose_name=_('ISO3'), max_length=5)
    figure = models.ForeignKey(
        Figure,
        related_name='+', on_delete=models.SET_NULL, null=True, blank=True,
    )
    country_name = models.CharField(verbose_name=_('Country name'), max_length=256)
    country = models.ForeignKey(
        'country.Country', related_name='gidd_figures', on_delete=models.PROTECT,
        verbose_name=_('Country')
    )
    geographical_region_name = models.CharField(
        verbose_name=_('Geographical Region'), max_length=256, blank=True, null=True
    )
    term = enum.EnumField(
        enum=Figure.FIGURE_TERMS,
        verbose_name=_('Figure Term'),
        blank=True, null=True
    )
    year = models.IntegerField()
    unit = enum.EnumField(enum=Figure.UNIT, verbose_name=_('Unit of Figure'))
    category = enum.EnumField(
        enum=Figure.FIGURE_CATEGORY_TYPES,
        verbose_name=_('Figure Category'),
        blank=True, null=True
    )
    cause = enum.EnumField(
        enum=Crisis.CRISIS_TYPE,
        verbose_name=_('Figure Cause'),
        blank=True, null=True
    )
    total_figures = models.PositiveIntegerField(verbose_name=_('Total Figures'))
    household_size = models.FloatField(
        verbose_name=_('Household Size'),
        blank=True, null=True
    )
    quantifier = enum.EnumField(
        enum=Figure.QUANTIFIER,
        verbose_name=_('Quantifier'),
        null=True,
    )
    reported = models.PositiveIntegerField(verbose_name=_('Reported Figures'))
    role = enum.EnumField(enum=Figure.ROLE, verbose_name=_('Role'), default=Figure.ROLE.RECOMMENDED)
    # Dates
    start_date = models.DateField(blank=True, null=True)
    start_date_accuracy = enum.EnumField(
        DATE_ACCURACY,
        verbose_name=_('Start Date Accuracy'),
        default=DATE_ACCURACY.DAY,
        blank=True,
        null=True,
    )
    end_date = models.DateField(blank=True, null=True)
    end_date_accuracy = enum.EnumField(
        DATE_ACCURACY,
        verbose_name=_('End date accuracy'),
        blank=True,
        null=True,
    )
    stock_date = models.DateField(blank=True, null=True)
    stock_date_accuracy = enum.EnumField(
        DATE_ACCURACY,
        verbose_name=_('Stock date accuracy'),
        blank=True,
        null=True,
    )
    stock_reporting_date = models.DateField(blank=True, null=True)
    include_idu = models.BooleanField(
        verbose_name=_('Include in IDU'),
        null=True,
    )
    excerpt_idu = models.TextField(
        verbose_name=_('Excerpt for IDU'),
        blank=True,
        null=True
    )
    is_confidential = models.BooleanField(
        verbose_name=_('Confidential Source'),
        default=False,
    )
    source_excerpt = models.TextField(
        verbose_name=_('Excerpt from Source'),
        blank=True,
        null=True
    )
    sources = ArrayField(
        models.CharField(
            verbose_name=_('Sources'), max_length=256
        ),
        default=list,
    )
    sources_ids = ArrayField(
        models.IntegerField(
            verbose_name=_('Sources IDs'),
        ),
        default=list,
    )
    sources_type = ArrayField(
        models.CharField(
            verbose_name=_('Sources Type'), max_length=256
        ),
        default=list,
    )
    publishers_ids = ArrayField(
        models.IntegerField(
            verbose_name=_('Publishers IDs'),
        ),
        default=list,
    )
    publishers = ArrayField(
        models.CharField(
            verbose_name=_('Publishers'), max_length=256
        ),
        default=list,
    )
    publishers_type = ArrayField(
        models.CharField(
            verbose_name=_('Publishers Type'), max_length=256
        ),
        default=list,
    )

    gidd_event = models.ForeignKey(
        'gidd.GiddEvent', verbose_name=_('GIDD Event'),
        related_name='gidd_figures', on_delete=models.PROTECT
    )
    entry = models.ForeignKey(
        Entry,
        verbose_name=_('Entry'),
        related_name='gidd_figures',
        on_delete=models.SET_NULL,
        null=True,
    )
    entry_name = models.CharField(
        max_length=512,
        verbose_name=_('Entry Title'),
        blank=True,
        null=True
    )
    context_of_violence = ArrayField(
        models.CharField(
            verbose_name=_('Context of Violences'), max_length=256
        ),
        default=list,
    )
    context_of_violence_ids = ArrayField(
        models.IntegerField(
            verbose_name=_('Context of Violence IDs'),
        ),
        default=list,
    )
    calculation_logic = models.TextField(
        verbose_name=_('Analysis and Calculation Logic'),
        blank=True,
        null=True
    )
    tags = ArrayField(
        models.CharField(
            verbose_name=_('Tags'), max_length=256
        ),
        default=list,
    )
    tags_ids = ArrayField(
        models.IntegerField(
            verbose_name=_('Tags IDs'),
        ),
        default=list,
    )
    is_housing_destruction = models.BooleanField(
        verbose_name=_('Is Housing Destruction'),
        default=False,
        null=True,
        blank=True,
    )
    is_disaggregated = models.BooleanField(
        verbose_name=_('Is disaggregated'),
        default=False
    )

    locations_ids = ArrayField(
        models.IntegerField(
            verbose_name=_('Location IDs'),
        ),
        default=list,
    )

    locations_coordinates = ArrayField(
        models.CharField(
            verbose_name=_('Location Coordinates'), max_length=256
        ),
        default=list,
    )
    locations_names = ArrayField(
        models.CharField(
            verbose_name=_('Location Names'), max_length=256
        ),
        default=list,
    )
    locations_accuracy = ArrayField(
        models.IntegerField(
            verbose_name=_('Location Accuracy'),
        ),
        default=list,
    )
    locations_type = ArrayField(
        models.IntegerField(
            verbose_name=_('Location Type'),
        ),
        default=list,
    )
    displacement_occurred = enum.EnumField(
        enum=Figure.DISPLACEMENT_OCCURRED,
        verbose_name=_('Displacement Occurred'),
        blank=True, null=True
    )
    violence = models.ForeignKey(
        'event.Violence', verbose_name=_('Figure Violence'),
        blank=False, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    violence_sub_type = models.ForeignKey(
        'event.ViolenceSubType', verbose_name=_('Figure Violence Sub Type'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    disaster_category = models.ForeignKey(
        'event.DisasterCategory', verbose_name=_('Figure Hazard Category'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    disaster_sub_category = models.ForeignKey(
        'event.DisasterSubCategory', verbose_name=_('Figure Hazard Sub Category'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    disaster_type = models.ForeignKey(
        'event.DisasterType', verbose_name=_('Figure Hazard Type'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    disaster_sub_type = models.ForeignKey(
        'event.DisasterSubType', verbose_name=_('Figure Hazard Sub Type'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL
    )
    other_sub_type = models.ForeignKey(
        'event.OtherSubType', verbose_name=_('Other sub type'),
        blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL)
    osv_sub_type = models.ForeignKey(
        'event.OsvSubType', verbose_name=_('Figure OSV sub type'),
        blank=True, null=True, related_name='+',
        on_delete=models.SET_NULL
    )

    violence_name = models.CharField(max_length=256, blank=True, null=True)
    violence_sub_type_name = models.CharField(max_length=256, blank=True, null=True)
    disaster_category_name = models.CharField(max_length=256, blank=True, null=True)
    disaster_sub_category_name = models.CharField(max_length=256, blank=True, null=True)
    disaster_type_name = models.CharField(max_length=256, blank=True, null=True)
    disaster_sub_type_name = models.CharField(max_length=256, blank=True, null=True)
    other_sub_type_name = models.CharField(max_length=256, blank=True, null=True)
    osv_sub_type_name = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.iso3

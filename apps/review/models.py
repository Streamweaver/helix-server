from django.db import models
from django.utils.translation import gettext_lazy as _
from django_enumfield import enum
from apps.contrib.models import MetaInformationArchiveAbstractModel


class UnifiedReviewComment(MetaInformationArchiveAbstractModel, models.Model):
    """

    Class: UnifiedReviewComment

    This class represents a review comment for an event, geo location, or figure in the system. It extends the MetaInformationArchiveAbstractModel and models.Model classes.

    Attributes:
    - event (ForeignKey): A foreign key to the Event model representing the event related to the review comment. It is nullable and blankable.
    - geo_location (ForeignKey): A foreign key to the OSMname model representing the geo location related to the review comment. It is nullable and blankable.
    - figure (ForeignKey): A foreign key to the Figure model representing the figure related to the review comment. It is nullable and blankable.
    - field (EnumField): An enum field representing the type of review field. It is nullable and blankable.
    - comment_type (EnumField): An enum field representing the type of review comment. Default value is REVIEW_COMMENT_TYPE.GREY.
    - geo_location (ForeignKey): A foreign key to the OSMName model representing the geolocation/OSM related to the review comment. It is nullable and blankable.
    - comment (TextField): A text field representing the comment for the review.
    - is_edited (BooleanField): A boolean field indicating if the review comment has been edited. Default value is False.
    - is_deleted (BooleanField): A boolean field indicating if the review comment has been deleted. Default value is False.

    """
    class REVIEW_COMMENT_TYPE(enum.Enum):
        RED = 0
        GREEN = 1
        GREY = 2

        __labels__ = {
            RED: _("Red"),
            GREEN: _("Green"),
            GREY: _("Grey"),
        }

    class REVIEW_FIELD_TYPE(enum.Enum):
        # Figure fields
        FIGURE_SOURCE_EXCERPT = 0
        FIGURE_ANALYSIS_CAVEATS_AND_CALCULATION_LOGIC = 1
        FIGURE_SOURCES = 2
        FIGURE_ROLE = 3
        FIGURE_DISPLACEMENT_OCCURRED = 4
        FIGURE_TERM = 5
        FIGURE_REPORTED_FIGURE = 6
        FIGURE_CATEGORY = 7
        FIGURE_START_DATE = 8
        FIGURE_END_DATE = 9
        FIGURE_STOCK_DATE = 10
        FIGURE_STOCK_REPORTING_DATE = 11
        FIGURE_MAIN_TRIGGER_OF_REPORTED_FIGURE = 12
        FIGURE_COUNTRY = 13
        FIGURE_UNIT = 14

        # Location fields
        LOCATION_TYPE = 100
        LOCATION_ACCURACY = 101

        __labels__ = {
            FIGURE_SOURCE_EXCERPT: 'Source Excerpt',
            FIGURE_ANALYSIS_CAVEATS_AND_CALCULATION_LOGIC: 'Analysis, Caveats And Calculation Logic',
            FIGURE_SOURCES: 'Sources',
            FIGURE_ROLE: 'Role',
            FIGURE_DISPLACEMENT_OCCURRED: 'Displacement Occurred',
            FIGURE_TERM: 'Term',
            FIGURE_REPORTED_FIGURE: 'Reported Figure',
            FIGURE_CATEGORY: 'Category',
            FIGURE_START_DATE: 'Start Date',
            FIGURE_END_DATE: 'End Date',
            FIGURE_STOCK_DATE: 'Stock Date',
            FIGURE_STOCK_REPORTING_DATE: 'Stock Reporting Date',
            FIGURE_MAIN_TRIGGER_OF_REPORTED_FIGURE: 'Main Trigger Of Reported Figure',
            FIGURE_COUNTRY: 'Country',
            LOCATION_TYPE: 'Location type',
            LOCATION_ACCURACY: 'Location accuracy',
            FIGURE_UNIT: 'Figure Unit',
        }

    # TODO: Make event non nullable field after review data migration
    event = models.ForeignKey(
        'event.Event', verbose_name=_('Event'),
        related_name='event_reviews', on_delete=models.CASCADE, null=True, blank=True
    )
    geo_location = models.ForeignKey(
        'entry.OSMname', verbose_name=_('Geo location'), null=True, blank=True,
        related_name='geo_location_reviews', on_delete=models.CASCADE
    )
    figure = models.ForeignKey(
        'entry.Figure', verbose_name=_('Figure'),
        blank=True, null=True,
        related_name='figure_review_comments', on_delete=models.CASCADE
    )
    field = enum.EnumField(enum=REVIEW_FIELD_TYPE, null=True, blank=True)
    comment_type = enum.EnumField(enum=REVIEW_COMMENT_TYPE, default=REVIEW_COMMENT_TYPE.GREY.value)
    geo_location = models.ForeignKey(
        'entry.OSMName', verbose_name=_('Geolocation/OSM'),
        null=True, blank=True,
        related_name='geo_location_review_comments', on_delete=models.SET_NULL
    )
    comment = models.TextField(
        verbose_name=_('Comment'),
        blank=True, null=True,
    )
    is_edited = models.BooleanField(verbose_name=_('Is edited?'), default=False)
    is_deleted = models.BooleanField(verbose_name=_('Is deleted?'), default=False)


class Review(MetaInformationArchiveAbstractModel, models.Model):
    """
    Review

    This class represents a review for an entry figure.

    Inherits From:
        MetaInformationArchiveAbstractModel
        models.Model

    Attributes:
        UNIQUE_TOGETHER_FIELDS (set): A set of fields that must be unique together in a review entry.
        UNIQUE_TOGETHER_WITHOUT_ENTRY_FIELDS (set): A set of fields that must be unique together in a review entry, excluding the 'entry' field.

    Nested Classes:
        ENTRY_REVIEW_STATUS: An enumeration class representing the review status of an entry.
            - RED: Represents a red status.
            - GREEN: Represents a green status.
            - GREY: Represents a grey status.

            __labels__ (dict): A dictionary mapping each status value to its corresponding label.

    Fields:
        entry (ForeignKey): A foreign key reference to an Entry object.
        figure (ForeignKey): A foreign key reference to a Figure object. Can be blank or null.
        field (CharField): A string field representing the field being reviewed.
        value (EnumField): An enum field representing the review status. Defaults to ENTRY_REVIEW_STATUS.GREY.
        age (CharField): A string field representing the age of the review. Can be blank or null.
        geo_location (ForeignKey): A foreign key reference to an OSMName object. Can be blank or null.
        comment (ForeignKey): A foreign key reference to a ReviewComment object. Can be blank or null.
    """
    UNIQUE_TOGETHER_FIELDS = {'entry', 'figure', 'field', 'age', 'geo_location'}
    UNIQUE_TOGETHER_WITHOUT_ENTRY_FIELDS = UNIQUE_TOGETHER_FIELDS - {'entry'}

    class ENTRY_REVIEW_STATUS(enum.Enum):
        RED = 0
        GREEN = 1
        GREY = 2

        __labels__ = {
            RED: _("Red"),
            GREEN: _("Green"),
            GREY: _("Grey"),
        }

    entry = models.ForeignKey('entry.Entry', verbose_name=_('Entry'),
                              related_name='figure_reviews', on_delete=models.CASCADE)
    figure = models.ForeignKey('entry.Figure', verbose_name=_('Figure'),
                               blank=True, null=True,
                               related_name='figure_reviews', on_delete=models.SET_NULL)
    field = models.CharField(verbose_name=_('Field'), max_length=256)
    value = enum.EnumField(enum=ENTRY_REVIEW_STATUS, default=ENTRY_REVIEW_STATUS.GREY.value)
    age = models.CharField(verbose_name=_('Age'), max_length=256,
                           null=True, blank=True)
    geo_location = models.ForeignKey('entry.OSMName', verbose_name=_('Geolocation/OSM'),
                                     null=True, blank=True,
                                     related_name='figure_reviews', on_delete=models.SET_NULL)
    comment = models.ForeignKey('review.ReviewComment', verbose_name=_('Comment'),
                                blank=True, null=True,
                                related_name='figure_reviews', on_delete=models.CASCADE)


class ReviewComment(MetaInformationArchiveAbstractModel, models.Model):
    """
    Class: ReviewComment

    ReviewComment is a class that represents a comment on a review.

    Attributes:
    - body: A TextField representing the body of the comment.
    - entry: A ForeignKey pointing to the related entry.

    Inherits from:
    - MetaInformationArchiveAbstractModel
    - models.Model
    """
    body = models.TextField(verbose_name=_('Body'), null=True)
    entry = models.ForeignKey('entry.Entry', verbose_name=_('Entry'),
                              related_name='review_comments', on_delete=models.CASCADE)

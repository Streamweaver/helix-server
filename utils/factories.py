import factory
from datetime import date
from dateutil.utils import today
from factory.django import DjangoModelFactory

from apps.contact.models import Contact
from apps.crisis.models import Crisis
from apps.entry.models import Figure, OSMName
from apps.event.models import Event, EventCode
from apps.common.enums import GENDER_TYPE


class UserFactory(DjangoModelFactory):
    """
    UserFactory is a factory class that is used to create User objects for testing purposes.

    Args:
        DjangoModelFactory: Meta class for defining the model to be used for creating the User objects.

    Attributes:
        model (str): The name of the model to be used for creating User objects.

        email (str): The email address of the User. It is generated using a lambda function that appends a sequence number to the base email 'admin'.

        username (str): The username of the User. It is generated using a lambda function that appends a sequence number to the base username 'username'.
    """
    class Meta:
        model = 'users.User'

    email = factory.Sequence(lambda n: f'admin{n}@email.com')
    username = factory.Sequence(lambda n: f'username{n}')


class GeographicalGroupFactory(DjangoModelFactory):
    """

    Class: GeographicalGroupFactory

    This class is a factory for creating instances of the GeographicalGroup model in the 'country' app.

    Attributes:
    - name: This attribute represents the name of the geographical group and is generated using the Faker library.

    """
    class Meta:
        model = 'country.GeographicalGroup'

    name = factory.Faker('first_name')


class CountrySubRegionFactory(DjangoModelFactory):
    """
    Factory class for creating instances of the model 'country.CountrySubRegion'.
    """
    class Meta:
        model = 'country.CountrySubRegion'

    name = factory.Faker('first_name')


class MonitoringSubRegionFactory(DjangoModelFactory):
    """"""
    class Meta:
        model = 'country.MonitoringSubRegion'

    name = factory.Faker('first_name')


class CountryRegionFactory(DjangoModelFactory):
    """

    Class CountryRegionFactory

    This class is a factory for creating instances of the CountryRegion model in the Django application.

    Attributes:
        name: A factory attribute that generates a fake first name for the name field of the CountryRegion model.

    """
    class Meta:
        model = 'country.CountryRegion'

    name = factory.Faker('first_name')


class CountryFactory(DjangoModelFactory):
    """
    Class CountryFactory creates instances of the Country model for testing purposes.

    Attributes:
        name (str): The name of the country.
        region (CountryRegionFactory): The region to which the country belongs.
        monitoring_sub_region (MonitoringSubRegionFactory): The monitoring sub-region to which the country belongs.

    Example usage:
        factory = CountryFactory()
        country = factory.create()

        name = country.name
        region = country.region
        monitoring_sub_region = country.monitoring_sub_region
    """
    class Meta:
        model = 'country.Country'

    name = factory.Faker('first_name')
    region = factory.SubFactory(CountryRegionFactory)
    monitoring_sub_region = factory.SubFactory(MonitoringSubRegionFactory)


class ContextualAnalysisFactory(DjangoModelFactory):
    """
    Factory class for creating instances of ContextualAnalysis model.

    Attributes:
        update (str): A randomly generated paragraph for the update field.
        country (Country): A subfactory to create a related Country object.

    Meta:
        model (str): The name of the model that this factory creates instances of.
    """
    class Meta:
        model = 'country.ContextualAnalysis'

    update = factory.Faker('paragraph')
    country = factory.SubFactory(CountryFactory)


class SummaryFactory(DjangoModelFactory):
    """
    SummaryFactory class

    This class is a factory for creating instances of the 'country.Summary' model. It extends the DjangoModelFactory class.

    Attributes:
        summary (str): A string representing a summary. It is generated using the factory.Faker('paragraph') method.
        country (CountryFactory): An instance of the CountryFactory class, used as a foreign key for the created Summary instance.

    Example usage:
        factory = SummaryFactory(summary='Lorem ipsum dolor sit amet', country=country_instance)
        summary = factory.create()

    Note:
        This class requires the DjangoModelFactory and CountryFactory classes to be imported in order to use it.
    """
    class Meta:
        model = 'country.Summary'

    summary = factory.Faker('paragraph')
    country = factory.SubFactory(CountryFactory)


class OrganizationKindFactory(DjangoModelFactory):
    """
    A factory class for creating instances of the OrganizationKind model.

    This factory class is used to generate instances of the OrganizationKind model, which represents different kinds of organizations.

    Attributes:
        name (str): The name of the organization kind.

    Examples:
        To create an instance of the OrganizationKind model using the factory:

        >>> factory = OrganizationKindFactory()
        >>> organization_kind = factory.create()

    Note:
        This factory class requires the DjangoModelFactory class from the factory_boy library to be installed.
    """
    class Meta:
        model = 'organization.OrganizationKind'

    name = factory.Faker('company_suffix')


class OrganizationFactory(DjangoModelFactory):
    """
    A factory class for creating instances of the `Organization` model.

    Attributes:
        short_name (str): The short name of the organization.
    """
    class Meta:
        model = 'organization.Organization'

    short_name = factory.Sequence(lambda n: 'shortname %d' % n)


class ContactFactory(DjangoModelFactory):
    """
    Class ContactFactory
    This class is used to create instances of the Contact model using Factory Boy library.

    Attributes:
    - designation: A factory.Iterator object that generates the designation field value from the list of options in the Contact.DESIGNATION.
    - first_name: A factory.Faker object that generates a random first name.
    - last_name: A factory.Faker object that generates a random last name.
    - gender: A factory.Iterator object that generates the gender field value from the list of options in the GENDER_TYPE.
    - job_title: A factory.Faker object that generates a random job title.
    - organization: A factory.SubFactory object that creates a related OrganizationFactory object.

    Usage example:
    contact = ContactFactory()

    Note: This class extends DjangoModelFactory and has Meta class to define the model it is associated with.
    """
    class Meta:
        model = 'contact.Contact'

    designation = factory.Iterator(Contact.DESIGNATION)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    gender = factory.Iterator(GENDER_TYPE)
    job_title = factory.Faker('job')
    organization = factory.SubFactory(OrganizationFactory)


class CommunicationMediumFactory(DjangoModelFactory):
    """
    A factory class for creating instances of the CommunicationMedium model.

    Attributes:
        Meta: A nested class containing the metadata for the factory. It specifies the model used for creating instances.
        name: A string representing the name of the communication medium.

    Example usage:
        medium_factory = CommunicationMediumFactory(name='Email')
        medium = medium_factory.create()
    """
    class Meta:
        model = 'contact.CommunicationMedium'

    name = factory.Sequence(lambda n: f'Medium{n}')


class CommunicationFactory(DjangoModelFactory):
    """
    CommunicationFactory class is a factory class used to generate instances of the Communication model in the contact module.

    Attributes:
        contact (ContactFactory): A factory for generating instances of the Contact model.
        title (str): The title of the communication.
        subject (str): The subject of the communication.
        content (str): The content of the communication.
        date_time (datetime): The date and time of the communication.
        medium (CommunicationMediumFactory): A factory for generating instances of the CommunicationMedium model.

    """
    class Meta:
        model = 'contact.Communication'

    contact = factory.SubFactory(ContactFactory)
    title = factory.Faker('sentence')
    subject = factory.Faker('sentence')
    content = factory.Faker('paragraph')
    date_time = factory.Faker('date_time_this_month')
    medium = factory.SubFactory(CommunicationMediumFactory)


class DisasterCategoryFactory(DjangoModelFactory):
    """
    The `DisasterCategoryFactory` class is a factory class used to create instances of the `DisasterCategory` model for testing purposes.

    Usage:
        Use the factory's methods to conveniently create `DisasterCategory` instances for testing.

    Attributes:
        - model : str
            Specifies the model that the factory is associated with, which is 'event.DisasterCategory'.

    Methods:
        None

    Example:
        from event.models import DisasterCategory
        from .factories import DisasterCategoryFactory

        # Create a `DisasterCategory` instance using the factory
        category = DisasterCategoryFactory()

        # The `category` variable now contains a newly created `DisasterCategory` instance
    """
    class Meta:
        model = 'event.DisasterCategory'


class DisasterSubCategoryFactory(DjangoModelFactory):
    """
    A factory class for creating instances of DisasterSubCategory model.

    Attributes:
        category (DisasterCategory): The sub factory for creating an instance of DisasterCategory model.

    """
    class Meta:
        model = 'event.DisasterSubCategory'

    category = factory.SubFactory(DisasterCategoryFactory)


class DisasterTypeFactory(DjangoModelFactory):
    """
    A factory class for creating instances of the DisasterType model.

    Example usage:
        disaster_type_factory = DisasterTypeFactory()
        disaster_type = disaster_type_factory.create()

    Attributes:
        disaster_sub_category (:class:`~.DisasterSubCategoryFactory`): A factory instance for creating instances
            of the DisasterSubCategory model.

    """
    class Meta:
        model = 'event.DisasterType'

    disaster_sub_category = factory.SubFactory(DisasterSubCategoryFactory)


class DisasterSubTypeFactory(DjangoModelFactory):
    """
    Factory class for creating instances of the DisasterSubType model.

    Usage:
        Create an instance of this factory to create a new DisasterSubType object.

    Example:
        factory = DisasterSubTypeFactory()

    Attributes:
        type (DisasterType): A sub-factory for creating the related DisasterType object.

    """
    class Meta:
        model = 'event.DisasterSubType'

    type = factory.SubFactory(DisasterTypeFactory)


class ViolenceFactory(DjangoModelFactory):
    """
    A factory class for creating instances of the Violence model.

    Attributes:
        Meta (class): A nested Meta class that specifies the model to be used.

    Raises:
        None.

    """
    class Meta:
        model = 'event.Violence'


class ViolenceSubTypeFactory(DjangoModelFactory):
    """
    Class representing a factory for creating instances of the ViolenceSubType model.

    This factory is a sub-factory of the DjangoModelFactory class and is used to create instances of the ViolenceSubType model. It provides a convenient way to create instances with pre-defined attributes or generate random data for testing or other purposes.

    Attributes:
        violence: A sub-factory of the ViolenceFactory class used to create an instance of the Violence model.

    Methods:
        - create(**kwargs): Creates and saves an instance of the ViolenceSubType model with the given attributes.
        - build(**kwargs): Creates an instance of the ViolenceSubType model but does not save it to the database.
        - generate(**kwargs): Generates random data for the attributes of the ViolenceSubType model and creates an instance.

    Example usage:

        # Creating an instance with pre-defined attributes
        violence_subtype = ViolenceSubTypeFactory.create(name='Assault', description='Physical attack')

        # Generating random data for the attributes
        violence_subtype = ViolenceSubTypeFactory.generate()

    Note: This factory requires the DjangoModelFactory library to be installed.
    """
    class Meta:
        model = 'event.ViolenceSubType'

    violence = factory.SubFactory(ViolenceFactory)


class CrisisFactory(DjangoModelFactory):
    """
    A factory class for creating Crisis instances.

    Attributes:
        crisis_type (str): The type of crisis.

    """
    class Meta:
        model = 'crisis.Crisis'

    crisis_type = factory.Iterator(Crisis.CRISIS_TYPE)


class ActorFactory(DjangoModelFactory):
    """

    ActorFactory

    This class is a factory for creating instances of the 'Actor' model in the 'event' application.

    """
    class Meta:
        model = 'event.Actor'

    country = factory.SubFactory(CountryFactory)


class ContextOfViolenceFactory(DjangoModelFactory):
    """
    Class: ContextOfViolenceFactory

    This class is a factory class for creating instances of the model "ContextOfViolence" in Django.

    Attributes:
    - model (str): The name of the model to be used.

    Methods:
    No specific methods are defined in this class.

    """
    class Meta:
        model = 'event.ContextOfViolence'


class EventFactory(DjangoModelFactory):
    """
    EventFactory

    This class is responsible for creating instances of the Event model using the DjangoModelFactory class.

    Attributes:
        crisis (CrisisFactory): A subfactory used to create the crisis attribute of the Event instance.
        event_type (Iterator): An iterator used to assign a valid crisis type to the event_type attribute of the Event instance.
        start_date (LazyFunction): A lazy function that returns a date object representing the start date of the event. The default value is January 1, 2010.
        end_date (LazyFunction): A lazy function that returns a date object representing the end date of the event. The default value is today's date.
        violence (ViolenceFactory): A subfactory used to create the violence attribute of the Event instance.
        violence_sub_type (ViolenceSubTypeFactory): A subfactory used to create the violence_sub_type attribute of the Event instance.
        actor (ActorFactory): A subfactory used to create the actor attribute of the Event instance.
        disaster_category (DisasterCategoryFactory): A subfactory used to create the disaster_category attribute of the Event instance.
        disaster_sub_category (DisasterSubCategoryFactory): A subfactory used to create the disaster_sub_category attribute of the Event instance.
        disaster_type (DisasterTypeFactory): A subfactory used to create the disaster_type attribute of the Event instance.
        disaster_sub_type (DisasterSubTypeFactory): A subfactory used to create the disaster_sub_type attribute of the Event instance.

    Methods:
        countries(self, create, extracted, **kwargs)
            This method is a post-generation hook provided by the DjangoModelFactory class. It is used to assign a set of countries to the countries attribute of the Event instance.

    Parameters:
        create (bool): A flag indicating whether the event instance should be created or not.
        extracted (list): A list of countries to be assigned to the countries attribute.

    Returns:
        None

    Example:
        # Create an Event instance without assigning any countries
        event_factory = EventFactory()

        # Create an Event instance and assign a list of countries
        countries = [country1, country2, country3]
        event_factory = EventFactory.create(countries=countries)
    """
    class Meta:
        model = Event

    crisis = factory.SubFactory(CrisisFactory)
    event_type = factory.Iterator(Crisis.CRISIS_TYPE)
    start_date = factory.LazyFunction(lambda: date(2010, 1, 1))
    end_date = factory.LazyFunction(today().date)
    violence = factory.SubFactory(ViolenceFactory)
    violence_sub_type = factory.SubFactory(ViolenceSubTypeFactory)
    actor = factory.SubFactory(ActorFactory)
    disaster_category = factory.SubFactory(DisasterCategoryFactory)
    disaster_sub_category = factory.SubFactory(DisasterSubCategoryFactory)
    disaster_type = factory.SubFactory(DisasterTypeFactory)
    disaster_sub_type = factory.SubFactory(DisasterSubTypeFactory)

    @factory.post_generation
    def countries(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for country in extracted:
                self.countries.add(country)


class EventCodeFactory(DjangoModelFactory):
    """
    Factory class for creating EventCode objects.
    """
    class Meta:
        model = 'event.EventCode'

    event = factory.SubFactory(EventFactory)
    country = factory.SubFactory(CountryFactory)
    event_code_type = factory.Iterator(EventCode.EVENT_CODE_TYPE)
    event_code = factory.Sequence(lambda n: f'Code-{n}')


class EntryFactory(DjangoModelFactory):
    """
    A factory class for generating instances of the 'Entry' model.

    Class:
        EntryFactory

    Inherits from:
        DjangoModelFactory

    Attributes:
        - article_title (str): The title of the article. A sequence is generated using a lambda function.
        - url (str): The URL of the article.
        - publish_date (datetime): The date when the article was published. A lazy function is used to get the current date.

    """
    class Meta:
        model = 'entry.Entry'

    article_title = factory.Sequence(lambda n: f'long title {n}')
    url = 'https://www.example.com'
    publish_date = factory.LazyFunction(today().date)


class FigureFactory(DjangoModelFactory):
    """

    FigureFactory class is a factory class used to create instances of the Figure model in the 'entry' module.

    Usage:
    To create a new Figure object, simply call the FigureFactory class.

    Example:
    figure = FigureFactory()

    Attributes:
    - entry: Represents the entry associated with the Figure object. (Factory: EntryFactory)
    - country: Represents the country associated with the Figure object. (Factory: CountryFactory)
    - quantifier: Represents the quantifier of the Figure object. (Factory: Iterator)
    - reported: Represents the reported value of the Figure object. (Factory: Sequence)
    - unit: Represents the unit of measurement for the Figure object. (Factory: Iterator)
    - household_size: Represents the household size of the Figure object. (default: 2)
    - role: Represents the role of the Figure object. (Factory: Iterator)
    - start_date: Represents the start date of the Figure object. (Factory: LazyFunction)
    - include_idu: Indicates whether to include IDU in the Figure object. (default: False)
    - term: Represents the term of the Figure object. (Factory: Iterator)
    - category: Represents the category of the Figure object. (Factory: Iterator)
    - figure_cause: Represents the cause of the Figure object. (Factory: Iterator)
    - geo_locations: Represents the geo locations associated with the Figure object. (Factory: Post Generation)

    Methods:
    - geo_locations: Post generation method to add GeoLocation objects to the Figure object.

    Note: This class extends the DjangoModelFactory class.
    """
    class Meta:
        model = 'entry.Figure'

    entry = factory.SubFactory(EntryFactory)
    country = factory.SubFactory(CountryFactory)
    quantifier = factory.Iterator(Figure.QUANTIFIER)
    reported = factory.Sequence(lambda n: n + 2)
    unit = factory.Iterator(Figure.UNIT)
    household_size = 2  # validation based on unit in the serializer
    role = factory.Iterator(Figure.ROLE)
    start_date = factory.LazyFunction(today().date)
    include_idu = False
    term = factory.Iterator(Figure.FIGURE_TERMS)
    category = factory.Iterator(Figure.FIGURE_CATEGORY_TYPES)
    figure_cause = factory.Iterator(Crisis.CRISIS_TYPE)

    @factory.post_generation
    def geo_locations(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for geo_location in extracted:
                self.geo_locations.add(geo_location)


class ResourceGroupFactory(DjangoModelFactory):
    """
    Factory class for creating instances of ResourceGroup model.

    Attributes:
        Meta: Defines the model that this factory is associated with.
        name: A string representing the name of the resource group.

    """
    class Meta:
        model = 'resource.ResourceGroup'

    name = factory.Sequence(lambda n: f'resource{n}')


class ResourceFactory(DjangoModelFactory):
    """
    ResourceFactory class is a factory class that is used to create instances of the Resource model.

    Attributes:
        name (str): The name of the resource. It is a unique identifier for the resource.
        group (ResourceGroup): The group to which the resource belongs.

    """
    class Meta:
        model = 'resource.Resource'

    name = factory.Sequence(lambda n: f'resource{n}')
    group = factory.SubFactory(ResourceGroupFactory)


class UnifiedReviewCommentFactory(DjangoModelFactory):
    """

    """
    class Meta:
        model = 'review.UnifiedReviewComment'


class TagFactory(DjangoModelFactory):
    """
    A factory class to create instances of the 'FigureTag' model from the Django app 'entry'.

    """
    class Meta:
        model = 'entry.FigureTag'


class ParkingLotFactory(DjangoModelFactory):
    """

    This class represents a factory for creating instances of the `ParkedItem` model in Django.

    Attributes:
        country (Country): A sub-factory for generating an instance of the `Country` model.

    """
    class Meta:
        model = 'parking_lot.ParkedItem'

    country = factory.SubFactory(CountryFactory)


class ReportFactory(DjangoModelFactory):
    """

    This class represents a factory for generating instances of the `Report` model.

    """
    class Meta:
        model = 'report.Report'


class ReportCommentFactory(DjangoModelFactory):
    """
    ReportCommentFactory class

    A factory class for creating instances of ReportComment.

    Attributes:
        Meta: A nested class specifying the meta options for the factory class.

    Methods:
        None

    """
    class Meta:
        model = 'report.ReportComment'

    report = factory.SubFactory(ReportFactory)


class OtherSubtypeFactory(DjangoModelFactory):
    """
    This class represents a factory for creating instances of the 'OtherSubtype' model in the Django application. It is a subclass of 'DjangoModelFactory' and has a Meta class that specifies the model it is associated with.

    Usage:
        factory = OtherSubtypeFactory()

    Attributes:
        Meta (class): A nested class that specifies the associated model.

    Example:
        factory = OtherSubtypeFactory()

    """
    class Meta:
        model = 'event.otherSubType'


class ClientFactory(DjangoModelFactory):
    """
    Class: ClientFactory

    A factory class for creating instances of the Django 'Contrib.Client' model.

    Inherits from: DjangoModelFactory

    Attributes:
        - model (str): The name of the Django model ('contrib.Client') to be used by the factory.

    Example usage:
        To create a new 'Contrib.Client' instance using the factory:
        factory = ClientFactory()
        client = factory.create()

        This will create a new instance of 'Contrib.Client' and return it.

    Note: Make sure to have the 'django_model_factory' package installed to use this class.
    """
    class Meta:
        model = 'contrib.Client'


class ClientTrackInfoFactory(DjangoModelFactory):
    """
    A factory class for creating instances of the ClientTrackInfo model.

    This class provides a convenient way to create instances of the ClientTrackInfo model
    with pre-defined attributes for testing and seeding the database.

    Attributes:
        Meta (class): A nested class that specifies the metadata for the factory.

    Usage:
        Use the factory to create instances of the ClientTrackInfo model with predefined attributes.

        Example:
            client_track_info = ClientTrackInfoFactory()
    """
    class Meta:
        model = 'contrib.ClientTrackInfo'


class NotificationFactory(DjangoModelFactory):
    """

    """
    class Meta:
        model = 'notification.Notification'


class ExtractionQueryFactory(DjangoModelFactory):
    """

    Class: ExtractionQueryFactory

    This class is a factory for creating instances of the 'extraction.ExtractionQuery' model in Django.

    Attributes:
    - model (str): The name of the model class this factory is associated with.

    Methods:
    - create(**kwargs): Creates and saves an instance of 'extraction.ExtractionQuery' with the given keyword arguments.
    - build(**kwargs): Creates an instance of 'extraction.ExtractionQuery' with the given keyword arguments but does not save it.

    Usage:

    # Import the class
    from factories import ExtractionQueryFactory

    # Create an instance of ExtractionQueryFactory
    factory = ExtractionQueryFactory

    # Create a new ExtractionQuery instance and save it to the database
    extraction_query = factory.create(attribute1=value1, attribute2=value2)

    # Create a new ExtractionQuery instance without saving it
    extraction_query = factory.build(attribute1=value1, attribute2=value2)

    """
    class Meta:
        model = 'extraction.ExtractionQuery'


class OSMNameFactory(DjangoModelFactory):
    """
    Class: OSMNameFactory

    A factory class for generating OSMName objects for testing purposes.

    Attributes:
        display_name (factory.Sequence): A factory attribute that generates a sequence of display names
            in the format 'osm-name-n', where n is a unique identifier.
        lat (factory.Faker('pyint', min_value=100, max_value=200)): A factory attribute that generates a
            random latitude value between 100 and 200.
        lon (factory.Faker('pyint', min_value=100, max_value=200)): A factory attribute that generates a
            random longitude value between 100 and 200.
        identifier (factory.Iterator): A factory attribute that iterates over the list of OSMName.IDENTIFIER
            values to generate unique identifiers.
        accuracy (factory.Iterator): A factory attribute that iterates over the list of OSMName.OSM_ACCURACY
            values to generate unique accuracies.

    Meta:
        model: 'entry.OSMName'
            The Meta inner class specifies the model that this factory class is associated with.

    """
    display_name = factory.Sequence(lambda n: f'osm-name-{n}')
    lat = factory.Faker('pyint', min_value=100, max_value=200)
    lon = factory.Faker('pyint', min_value=100, max_value=200)
    identifier = factory.Iterator(OSMName.IDENTIFIER)
    accuracy = factory.Iterator(OSMName.OSM_ACCURACY)

    class Meta:
        model = 'entry.OSMName'


class HouseholdSizeFactory(DjangoModelFactory):
    """

    HouseholdSizeFactory class

    This class is a factory for creating instances of HouseholdSize model from the 'country' app.

    Attributes:
        Meta (class): A nested class that defines the metadata for the factory.

    """
    class Meta:
        model = 'country.HouseholdSize'

from copy import copy
import json
from uuid import uuid4

from apps.entry.models import (
    Figure,
    OSMName,
    Entry,
    EntryReviewer,
    CANNOT_UPDATE_MESSAGE,
)
from apps.entry.models import DisaggregatedAgeCategory
from apps.users.enums import USER_ROLE
from utils.factories import (
    EventFactory,
    EntryFactory,
    FigureFactory,
    OrganizationFactory,
    CountryFactory,
    TagFactory,
    ContextOfViolenceFactory,
)
from utils.permissions import PERMISSION_DENIED_MESSAGE
from utils.tests import HelixGraphQLTestCase, create_user_with_role
from apps.crisis.models import Crisis


class TestEntryQuery(HelixGraphQLTestCase):
    def setUp(self) -> None:
        self.country = CountryFactory.create()
        self.country_id = str(self.country.id)
        self.editor = create_user_with_role(USER_ROLE.MONITORING_EXPERT.name)
        self.entry = EntryFactory.create(
            created_by=self.editor
        )
        self.entry_query = '''
        query MyQuery($id: ID!) {
          entry(id: $id) {
            totalStockIdpFigures
            totalFlowNdFigures
          }
        }
        '''
        guest = create_user_with_role(USER_ROLE.GUEST.name)
        self.force_login(guest)

    # def test_figure_count_filtered_resolvers(self):
    #     self.stock_fig_cat = Figure.FIGURE_CATEGORY_TYPES.IDPS
    #     self.random_fig_cat2 = Figure.FIGURE_CATEGORY_TYPES.CROSS_BORDER_FLIGHT
    #     self.flow_fig_cat3 = Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT
    #     self.event = EventFactory.create(
    #         event_type=Crisis.CRISIS_TYPE.OTHER.value,
    #     )
    #     self.event.countries.add(self.country)
    #     figure1 = FigureFactory.create(entry=self.entry,
    #                                    event=self.event,
    #                                    category=self.stock_fig_cat.value,
    #                                    reported=101,
    #                                    role=Figure.ROLE.RECOMMENDED,
    #                                    unit=Figure.UNIT.PERSON)
    #     FigureFactory.create(entry=self.entry,
    #                          category=self.stock_fig_cat.value,
    #                          event=self.event,
    #                          reported=102,
    #                          role=Figure.ROLE.TRIANGULATION,
    #                          unit=Figure.UNIT.PERSON)
    #     figure3 = FigureFactory.create(entry=self.entry,
    #                                    category=self.stock_fig_cat.value,
    #                                    reported=103,
    #                                    role=Figure.ROLE.RECOMMENDED,
    #                                    unit=Figure.UNIT.PERSON,
    #                                    event=self.event)
    #     FigureFactory.create(entry=self.entry,
    #                          event=self.event,
    #                          category=self.random_fig_cat2,
    #                          reported=50,
    #                          role=Figure.ROLE.RECOMMENDED,
    #                          unit=Figure.UNIT.PERSON)
    #     figure5 = FigureFactory.create(entry=self.entry,
    #                                    event=self.event,
    #                                    category=self.flow_fig_cat3,
    #                                    reported=70,
    #                                    role=Figure.ROLE.RECOMMENDED,
    #                                    unit=Figure.UNIT.PERSON)
    #     response = self.query(
    #         self.entry_query,
    #         variables=dict(
    #             id=str(self.entry.id),
    #         )
    #     )
    #     content = json.loads(response.content)
    #     self.assertResponseNoErrors(response)
    #     self.assertEqual(
    #         content['data']['entry']['totalStockIdpFigures'],
    #         figure1.total_figures + figure3.total_figures
    #     )
    #     self.assertEqual(
    #         content['data']['entry']['totalFlowNdFigures'],
    #         figure5.total_figures
    #     )
        # category based filter for entry stock/flow figures will not be used,
        # since it is directly filtered by IDP or NEW DISPLACEMENT


class TestEntryCreation(HelixGraphQLTestCase):
    def setUp(self) -> None:
        DisaggregatedAgeCategory.objects.create(name='one')
        DisaggregatedAgeCategory.objects.create(name='two')
        DisaggregatedAgeCategory.objects.create(name='three')
        self.country = CountryFactory.create(iso2='lo', iso3='lol')
        self.country_id = str(self.country.id)
        self.event = EventFactory.create(event_type=Crisis.CRISIS_TYPE.CONFLICT.value)
        self.event.countries.add(self.country)
        self.fig_cat = Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT
        self.editor = create_user_with_role(USER_ROLE.MONITORING_EXPERT.name)
        self.mutation = """
            mutation CreateEntry($input: EntryCreateInputType!) {
                createEntry(data: $input) {
                    ok
                    errors
                    result {
                        id
                        figures {
                            id
                            createdBy{
                                id
                                fullName
                            }
                        }
                        reviewers {
                            results {
                                id
                            }
                        }
                        createdBy{
                            id
                            fullName
                        }
                    }
                }
            }
        """
        self.input = {
            "url": "https://yoko-onos-blog.com",
            "articleTitle": "title 1",
            "publishers": [str(OrganizationFactory.create().id)],
            "publishDate": "2020-09-09",
            "idmcAnalysis": "analysis one",
            "isConfidential": True,
            "reviewers": [],
        }
        self.force_login(self.editor)
        self.tag1 = TagFactory.create()
        self.tag2 = TagFactory.create()
        self.tag3 = TagFactory.create()
        self.context_of_violence = ContextOfViolenceFactory.create()

    def test_valid_create_entry_without_figures(self):
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['createEntry']['ok'], content)
        self.assertIsNone(content['data']['createEntry']['errors'], content)
        self.assertIsNotNone(content['data']['createEntry']['result']['id'])

    def test_valid_nested_figures_create(self):
        source1 = dict(
            uuid=str(uuid4()),
            rank=101,
            country=str(self.country.name),
            countryCode=self.country.iso2,
            osmId='ted',
            osmType='okay',
            displayName='okay',
            lat=68.88,
            lon=46.66,
            name='name',
            accuracy=OSMName.OSM_ACCURACY.ADM0.name,
            identifier=OSMName.IDENTIFIER.ORIGIN.name,
        )
        source2 = copy(source1)
        source2['lat'] = 67.5
        source2['uuid'] = str(uuid4())
        figures = [
            {
                "uuid": str(uuid4()),
                "country": self.country_id,
                "quantifier": Figure.QUANTIFIER.MORE_THAN.name,
                "reported": 10,
                "unit": Figure.UNIT.PERSON.name,
                "term": Figure.FIGURE_TERMS.EVACUATED.name,
                "category": self.fig_cat.name,
                "role": Figure.ROLE.RECOMMENDED.name,
                "startDate": "2020-10-10",
                "includeIdu": True,
                "excerptIdu": "excerpt abc",
                "geoLocations": [source1],
                "tags": [self.tag1.id, self.tag2.id, self.tag3.id],
                'calculationLogic': 'test logics',
                'sourceExcerpt': 'source excerpt',
                'event': self.event.id,
                "contextOfViolence": [self.context_of_violence.id],
                "figureCause": Crisis.CRISIS_TYPE.CONFLICT.name,
            },
            {
                "uuid": str(uuid4()),
                "country": self.country_id,
                "quantifier": Figure.QUANTIFIER.MORE_THAN.name,
                "reported": 10,
                "unit": Figure.UNIT.PERSON.name,
                "term": Figure.FIGURE_TERMS.EVACUATED.name,
                "category": self.fig_cat.name,
                "role": Figure.ROLE.RECOMMENDED.name,
                "startDate": "2020-10-10",
                "includeIdu": True,
                "excerptIdu": "excerpt abc",
                "geoLocations": [source2],
                "tags": [self.tag1.id, self.tag2.id, self.tag3.id],
                'calculationLogic': 'test logics',
                'sourceExcerpt': 'source excerpt',
                'event': self.event.id,
                "contextOfViolence": [self.context_of_violence.id],
                "figureCause": Crisis.CRISIS_TYPE.CONFLICT.name,
            }
        ]

        self.input.update({
            'figures': figures
        })
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['createEntry']['ok'], content)
        self.assertIsNone(content['data']['createEntry']['errors'], content)
        self.assertIsNotNone(content['data']['createEntry']['result']['id'])
        self.assertEqual(len(content['data']['createEntry']['result']['figures']),
                         len(figures))
        self.assertIsNotNone(content['data']['createEntry']['result']['figures'][0]['id'])
        self.assertEqual(
            content['data']['createEntry']['result']['createdBy']['fullName'],
            self.editor.full_name
        )
        self.assertTrue(
            content['data']['createEntry']['result']['figures'][0]['createdBy']
        )
        self.assertTrue(
            content['data']['createEntry']['result']['figures'][1]['createdBy']
        )

    def test_assert_nested_figures_errors(self):
        uuid = str(uuid4())
        uuid_error = str(uuid4())
        source1 = dict(
            uuid=str(uuid4()),
            rank=101,
            country=str(self.country.name),
            countryCode=self.country.iso2,
            osmId='ted',
            osmType='okay',
            displayName='okay',
            lat=68.88,
            lon=46.66,
            name='name',
            accuracy=OSMName.OSM_ACCURACY.ADM0.name,
            identifier=OSMName.IDENTIFIER.ORIGIN.name,
        )
        source2 = copy(source1)
        source2['lat'] = 67.5
        source2['uuid'] = str(uuid4())

        figures = [
            # valid data
            {
                "uuid": uuid,
                "country": self.country_id,
                "quantifier": Figure.QUANTIFIER.MORE_THAN.name,
                "reported": 10,
                "unit": Figure.UNIT.PERSON.name,
                "term": Figure.FIGURE_TERMS.EVACUATED.name,
                "category": self.fig_cat.name,
                "role": Figure.ROLE.RECOMMENDED.name,
                "startDate": "2020-10-10",
                "includeIdu": True,
                "excerptIdu": "excerpt abc",
                "geoLocations": [source1],
                "event": self.event.id,
                "figureCause": Crisis.CRISIS_TYPE.CONFLICT.name,
            },
            # invalid now
            {
                "uuid": uuid_error,
                "country": self.country_id,
                "reported": -1,  # this cannot be negative
                "quantifier": Figure.QUANTIFIER.MORE_THAN.name,
                "unit": Figure.UNIT.PERSON.name,
                "term": Figure.FIGURE_TERMS.EVACUATED.name,
                "category": self.fig_cat.name,
                "role": Figure.ROLE.RECOMMENDED.name,
                "startDate": "2020-10-10",
                "includeIdu": True,
                "excerptIdu": "excerpt abc",
                "geoLocations": [source2],
                "event": self.event.id,
                "figureCause": Crisis.CRISIS_TYPE.CONFLICT.name,
            }
        ]
        self.input.update({
            'figures': figures
        })
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertFalse(content['data']['createEntry']['ok'], content)
        self.assertIsNotNone(content['data']['createEntry']['errors'], content)
        self.assertEqual(uuid_error,
                         content['data']['createEntry']['errors'][0]['arrayErrors'][0]['key'],
                         content['data']['createEntry'])
        self.assertEqual('reported',
                         content['data']['createEntry']['errors'][0]['arrayErrors'][0]['objectErrors'][0]['field'])

    def test_add_reviewers_while_create_entry(self):
        r1 = create_user_with_role(role=USER_ROLE.MONITORING_EXPERT.name)
        r2 = create_user_with_role(role=USER_ROLE.MONITORING_EXPERT.name)
        r3 = create_user_with_role(role=USER_ROLE.MONITORING_EXPERT.name)
        self.input.update(dict(reviewers=[str(r1.id), str(r2.id), str(r3.id)]))

        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = response.json()

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['createEntry']['ok'], content)
        self.assertIsNone(content['data']['createEntry']['errors'], content)
        entry = Entry.objects.get(id=content['data']['createEntry']['result']['id'])
        self.assertEqual(entry.reviewers.count(), len(self.input['reviewers']))
        self.assertEqual(len(content['data']['createEntry']['result']['reviewers']
                             ['results']), len(self.input['reviewers']), content)

    def test_invalid_guest_entry_create(self):
        guest = create_user_with_role(role=USER_ROLE.GUEST.name)
        self.force_login(guest)
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)
        self.assertIn(PERMISSION_DENIED_MESSAGE, content['errors'][0]['message'])

    def test_invalid_figures_age_data(self):
        figures = [
            {
                "uuid": str(uuid4()),
                "country": self.country_id,
                "quantifier": Figure.QUANTIFIER.MORE_THAN.name,
                "reported": 10,
                "unit": Figure.UNIT.PERSON.name,
                "householdSize": 1,
                "term": Figure.FIGURE_TERMS.EVACUATED.name,
                "category": self.fig_cat.name,
                "role": Figure.ROLE.RECOMMENDED.name,
                "startDate": "2020-10-10",
                "includeIdu": True,
                "excerptIdu": "excerpt abc",
                "disaggregationAge": [
                    # invalid: category and sex is duplicated
                    {
                        "uuid": "e4857d07-736c-4ff3-a21f-51170f0551c9",
                        "category": DisaggregatedAgeCategory.objects.first().id,
                        "sex": "MALE",
                        "value": 5
                    },
                    {
                        "uuid": "4c3dd257-30b1-4f62-8f3a-e90e8ac57bce",
                        "category": DisaggregatedAgeCategory.objects.first().id,
                        "sex": "FEMALE",
                        "value": 6
                    }
                ],
                "event": self.event.id,
                "figureCause": Crisis.CRISIS_TYPE.CONFLICT.name,
            }
        ]
        self.input.update({
            'figures': figures
        })
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertFalse(content['data']['createEntry']['ok'], content)
        self.assertIn('disaggregationAge', json.dumps(content['data']['createEntry']['errors']))

    def test_invalid_figures_household_size(self):
        figures = [
            {
                "uuid": str(uuid4()),
                "country": self.country_id,
                "quantifier": Figure.QUANTIFIER.MORE_THAN.name,
                "reported": 10,
                "unit": Figure.UNIT.HOUSEHOLD.name,  # missing household_size
                "term": Figure.FIGURE_TERMS.EVACUATED.name,
                "category": self.fig_cat.name,
                "role": Figure.ROLE.RECOMMENDED.name,
                "startDate": "2020-10-10",
                "includeIdu": True,
                "excerptIdu": "excerpt abc",
                "event": self.event.id,
                "figureCause": Crisis.CRISIS_TYPE.CONFLICT.name,
            }
        ]
        self.input.update({
            'figures': figures
        })
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertFalse(content['data']['createEntry']['ok'], content)
        self.assertIn('householdSize', json.dumps(content['data']['createEntry']['errors']))


class TestEntryUpdate(HelixGraphQLTestCase):
    def setUp(self) -> None:
        self.country = CountryFactory.create(iso2='np')
        self.country_id = str(self.country.id)
        self.fig_cat = Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT
        self.editor = create_user_with_role(USER_ROLE.MONITORING_EXPERT)
        self.admin = create_user_with_role(USER_ROLE.ADMIN.name)
        self.event = EventFactory.create(name='myevent', event_type=Crisis.CRISIS_TYPE.CONFLICT.value)
        self.event.countries.add(self.country)
        DisaggregatedAgeCategory.objects.create(name='one')
        DisaggregatedAgeCategory.objects.create(name='two')
        DisaggregatedAgeCategory.objects.create(name='three')
        self.entry = EntryFactory.create(
            created_by=self.editor,
        )
        self.mutation = """
        mutation MyMutation($input: EntryUpdateInputType!) {
          updateEntry(data: $input) {
            ok
            errors
            result {
              id
              figures {
                id
                createdAt
                disaggregationAge {
                 results {
                      uuid
                      category {
                        id
                        name
                      }
                  }
                }
                createdBy {
                  id
                  fullName
                }
              }
              createdAt
              articleTitle
              createdBy {
                  id
                  fullName
              }
            }
          }
        }
        """
        self.input = {
            "id": self.entry.id,
            "articleTitle": "updated-bla",
        }

    def test_valid_update_entry(self):
        self.force_login(self.admin)
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['updateEntry']['ok'], content)

    def test_valid_entry_update_by_admins(self):
        self.force_login(self.admin)
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['updateEntry']['ok'], content)

    def test_valid_update_entry_with_figures(self):
        assert DisaggregatedAgeCategory.objects.count() > 1
        figure = FigureFactory.create(
            entry=self.entry,
            country=self.country,
            event=self.event,
        )
        # this figure will be deleted
        deleted_figure = FigureFactory.create(entry=self.entry, event=self.event)
        source1 = dict(
            uuid=str(uuid4()),
            rank=101,
            country=str(self.country.name),
            countryCode=self.country.iso2,
            osmId='ted',
            osmType='okay',
            displayName='okay',
            lat=68.88,
            lon=46.66,
            name='name',
            accuracy=OSMName.OSM_ACCURACY.ADM0.name,
            identifier=OSMName.IDENTIFIER.ORIGIN.name,
        )
        source2 = copy(source1)
        source2['lat'] = 67.5
        source2['uuid'] = str(uuid4())
        figures = [
            {
                "uuid": "1cd00034-037e-4c5f-b196-fa05b6bed803",
                "country": self.country_id,
                "quantifier": Figure.QUANTIFIER.MORE_THAN.name,
                "reported": 10,
                "unit": Figure.UNIT.PERSON.name,
                "term": Figure.FIGURE_TERMS.EVACUATED.name,
                "category": self.fig_cat.name,
                "role": Figure.ROLE.RECOMMENDED.name,
                "startDate": "2020-09-09",
                "includeIdu": False,
                "disaggregationAge": [
                    {
                        "uuid": "e4857d07-736c-4ff3-a21f-51170f0551c9",
                        "category": DisaggregatedAgeCategory.objects.first().id,
                        "value": 3,
                        "sex": "MALE",
                    },
                    {
                        "uuid": "4c3dd257-30b1-4f62-8f3a-e90e8ac57bce",
                        "category": DisaggregatedAgeCategory.objects.last().id,
                        "value": 3,
                        "sex": "FEMALE",
                    }
                ],
                "disaggregationStrataJson": [
                    {"date": "2020-10-10", "value": 2, "uuid": "132acc8b-b7f7-4535-8c80-f6eb35bf9003"},
                    {"date": "2020-10-12", "value": 2, "uuid": "bf2b1415-2fc5-42b7-9180-a5b440e5f6d1"}
                ],
                "geoLocations": [source1],
                "event": self.event.id,
                "figureCause": Crisis.CRISIS_TYPE.CONFLICT.name,
            },
            {
                "id": figure.id,
                "uuid": str(figure.uuid),
                "country": self.country_id,
                "quantifier": Figure.QUANTIFIER.MORE_THAN.name,
                "reported": 10,
                "unit": Figure.UNIT.PERSON.name,
                "term": Figure.FIGURE_TERMS.EVACUATED.name,
                "category": self.fig_cat.name,
                "role": Figure.ROLE.RECOMMENDED.name,
                "startDate": "2020-09-09",
                "includeIdu": False,
                "disaggregationAge": [
                    {
                        "uuid": "e4857d07-736c-4ff3-a21f-51170f0551c9",
                        "category": DisaggregatedAgeCategory.objects.first().id,
                        "value": 3,
                        "sex": "MALE",
                    },
                    {
                        "uuid": "4c3dd257-30b1-4f62-8f3a-e90e8ac57bce",
                        "category": DisaggregatedAgeCategory.objects.last().id,
                        "value": 3,
                        "sex": "FEMALE",
                    }
                ],
                "disaggregationStrataJson": [
                    {"date": "2020-10-10", "value": 2, "uuid": "132acc8b-b7f7-4535-8c80-f6eb35bf9003"},
                    {"date": "2020-10-12", "value": 2, "uuid": "bf2b1415-2fc5-42b7-9180-a5b440e5f6d1"}
                ],
                "geoLocations": [source2],
                "event": self.event.id,
                "figureCause": Crisis.CRISIS_TYPE.CONFLICT.name,
            },
        ]
        old_figures_count = self.entry.figures.count()
        self.force_login(self.admin)
        self.input['figures'] = figures
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['updateEntry']['ok'], content)
        self.entry.refresh_from_db()
        self.assertNotIn(deleted_figure, self.entry.figures.all())
        self.assertEqual(self.entry.figures.count(), old_figures_count)
        self.assertEqual(
            content['data']['updateEntry']['result']['createdBy']['fullName'],
            self.editor.full_name
        )
        self.assertEqual(
            content['data']['updateEntry']['result']['figures'][0]['createdBy'], None
        )
        self.assertTrue(
            content['data']['updateEntry']['result']['figures'][1]['createdBy']
        )

    def test_invalid_figures_household_size(self):
        figures = [
            {
                "uuid": str(uuid4()),
                "country": self.country_id,
                "quantifier": Figure.QUANTIFIER.MORE_THAN.name,
                "reported": 10,
                "unit": Figure.UNIT.HOUSEHOLD.name,  # missing household_size
                "term": Figure.FIGURE_TERMS.EVACUATED.name,
                "category": self.fig_cat.name,
                "role": Figure.ROLE.RECOMMENDED.name,
                "startDate": "2020-10-10",
                "includeIdu": True,
                "excerptIdu": "excerpt abc",
                "event": self.event.id,
                "figureCause": Crisis.CRISIS_TYPE.CONFLICT.name,
            }
        ]
        self.input.update({
            'figures': figures
        })
        admin = create_user_with_role(USER_ROLE.ADMIN.name)
        self.force_login(admin)
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertFalse(content['data']['updateEntry']['ok'], content)
        self.assertIn('householdSize', json.dumps(content['data']['updateEntry']['errors']))

    def test_figure_cause_should_be_same_as_event_type(self):
        event_1 = EventFactory.create(event_type=Crisis.CRISIS_TYPE.CONFLICT)
        event_2 = EventFactory.create(event_type=Crisis.CRISIS_TYPE.DISASTER)
        event_3 = EventFactory.create(event_type=Crisis.CRISIS_TYPE.OTHER)
        # Pass incorrect figure cause
        figures = [
            {
                'figureCause': Crisis.CRISIS_TYPE.OTHER.name,
                'event': event_1.id,
            },
            {
                'figureCause': Crisis.CRISIS_TYPE.DISASTER.name,
                'event': event_2.id,
            }
        ]
        self.input.update({
            'figures': figures
        })
        admin = create_user_with_role(USER_ROLE.ADMIN.name)
        self.force_login(admin)
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertFalse(content['data']['updateEntry']['ok'], content)
        self.assertIn('figureCause', json.dumps(content['data']['updateEntry']['errors']))

        # Pass correct figure cause
        self.input['figures'] = [
            {
                'figureCause': Crisis.CRISIS_TYPE.CONFLICT.name,
                'event': event_1.id,
            },
            {
                'figureCause': Crisis.CRISIS_TYPE.DISASTER.name,
                'event': event_2.id,
            },
            {
                'figureCause': Crisis.CRISIS_TYPE.OTHER.name,
                'event': event_3.id,
            }
        ]
        response = self.query(
            self.mutation,
            input_data=self.input
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertFalse(content['data']['updateEntry']['ok'], content)
        self.assertNotIn('figureCause', json.dumps(content['data']['updateEntry']['errors']))


class TestEntryDelete(HelixGraphQLTestCase):
    def setUp(self) -> None:
        self.editor = create_user_with_role(USER_ROLE.MONITORING_EXPERT.name)
        self.entry = EntryFactory.create(
            created_by=self.editor
        )
        self.mutation = """
            mutation DeleteEntry($id: ID!) {
                deleteEntry(id: $id) {
                    ok
                    errors
                    result {
                        id
                        url
                        createdAt
                    }
                }
            }
        """
        self.variables = {
            "id": self.entry.id,
        }

    def test_valid_delete_entry(self):
        self.force_login(self.editor)
        response = self.query(
            self.mutation,
            variables=self.variables
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['deleteEntry']['ok'], content)
        self.assertEqual(content['data']['deleteEntry']['result']['url'],
                         self.entry.url)

    def test_valid_entry_delete_by_admins(self):
        admin = create_user_with_role(USER_ROLE.ADMIN.name)
        self.force_login(admin)
        response = self.query(
            self.mutation,
            variables=self.variables
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['deleteEntry']['ok'], content)
        self.assertEqual(content['data']['deleteEntry']['result']['url'],
                         self.entry.url)


class TestEntryReviewUpdate(HelixGraphQLTestCase):
    def setUp(self) -> None:
        self.entry = EntryFactory.create()
        self.r1 = create_user_with_role(USER_ROLE.MONITORING_EXPERT.name)
        self.r2 = create_user_with_role(USER_ROLE.MONITORING_EXPERT.name)
        self.r3 = create_user_with_role(USER_ROLE.MONITORING_EXPERT.name)
        self.it = create_user_with_role(USER_ROLE.ADMIN.name)
        self.entry.reviewers.set([self.r1, self.r2, self.r3, self.it])
        self.q = '''
        mutation MyMutation ($input: EntryReviewStatusInputType!){
          updateEntryReview(data: $input) {
            errors
            ok
          }
        }
        '''

    def test_update_review_status(self):
        input = dict(
            entry=str(self.entry.id),
            status=EntryReviewer.REVIEW_STATUS.UNDER_REVIEW.name
        )
        self.force_login(self.r1)
        response = self.query(
            self.q,
            input_data=input
        )
        content = response.json()

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['updateEntryReview']['ok'], content)

        # trying to signoff should fail
        input['status'] = EntryReviewer.REVIEW_STATUS.SIGNED_OFF.name
        response = self.query(
            self.q,
            input_data=input
        )
        content = response.json()

        self.assertResponseNoErrors(response)
        self.assertFalse(content['data']['updateEntryReview']['ok'], content)
        self.assertIn(str(CANNOT_UPDATE_MESSAGE),
                      content['data']['updateEntryReview']['errors'][0]['messages'])

        # signoff by it head should succeed
        self.force_login(self.it)
        input['status'] = EntryReviewer.REVIEW_STATUS.SIGNED_OFF.name
        response = self.query(
            self.q,
            input_data=input
        )
        content = response.json()

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['updateEntryReview']['ok'], content)


class TestExportEntry(HelixGraphQLTestCase):
    def setUp(self) -> None:
        self.editor = create_user_with_role(USER_ROLE.MONITORING_EXPERT.name)
        for i in range(3):
            EntryFactory.create(created_by=self.editor)
        self.mutation = """
        mutation ExportEntries($filterFigureStartAfter: Date, $filterFigureEndBefore: Date){
            exportEntries(
                filterFigureStartAfter: $filterFigureStartAfter
                filterFigureEndBefore: $filterFigureEndBefore
          ){
            errors
            ok
          }
        }

        """
        self.variables = {
            "filterFigureStartAfter": "2018-08-25",
            "filterFigureEndBefore": "2021-08-25",
        }

    def test_export_entry(self):
        self.force_login(self.editor)
        response = self.query(
            self.mutation,
            variables=self.variables
        )
        self.assertResponseNoErrors(response)


class TestFigureDelete(HelixGraphQLTestCase):
    def setUp(self) -> None:
        self.country = CountryFactory.create()
        self.country_id = str(self.country.id)
        self.editor = create_user_with_role(USER_ROLE.MONITORING_EXPERT.name)
        self.entry = EntryFactory.create(
            created_by=self.editor
        )
        self.event = EventFactory.create(
            event_type=Crisis.CRISIS_TYPE.OTHER.value,
        )
        self.event.countries.add(self.country)
        self.figure = FigureFactory.create(
            entry=self.entry,
            reported=101,
            role=Figure.ROLE.RECOMMENDED,
            unit=Figure.UNIT.PERSON,
            event=self.event,
        )
        self.mutation = """
            mutation DeleteFigure($id: ID!) {
                deleteFigure(id: $id) {
                    ok
                    errors
                    result {
                        id
                    }
                }
            }
        """
        self.variables = {
            "id": self.figure.id,
        }

    def test_can_delete_figure(self):
        self.force_login(self.editor)
        response = self.query(
            self.mutation,
            variables=self.variables
        )
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertTrue(content['data']['deleteFigure']['ok'], content)

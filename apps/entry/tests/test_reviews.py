import json
from uuid import uuid4
from apps.users.enums import USER_ROLE
from apps.crisis.models import Crisis
from apps.entry.models import Figure, OSMName
from apps.event.models import Event
from utils.factories import (
    EventFactory,
    FigureFactory,
    EntryFactory,
    UnifiedReviewCommentFactory,
    CountryFactory,
)
from utils.tests import HelixGraphQLTestCase, create_user_with_role


class TestEventReviewGraphQLTestCase(HelixGraphQLTestCase):
    def setUp(self) -> None:
        self.event = EventFactory.create()
        self.regional_coordinator = create_user_with_role(USER_ROLE.REGIONAL_COORDINATOR.name)
        self.monitoring_expert = create_user_with_role(USER_ROLE.MONITORING_EXPERT.name)
        self.admin = create_user_with_role(USER_ROLE.ADMIN.name)
        self.guest = create_user_with_role(USER_ROLE.GUEST.name)
        self.approve_figure = '''
        mutation approveFigure($id: ID!) {
            approveFigure(id: $id) {
               errors
                ok
                result {
                  id
                  reviewStatus
                }
            }
        }
        '''
        self.unapprove_figure = '''
        mutation unapproveFigure($id: ID!) {
            unapproveFigure(id: $id) {
               errors
                ok
                result {
                  id
                  reviewStatus
                }
            }
        }
        '''
        self.re_request_review_figure = '''
        mutation reRequestReviewFigure($id: ID!) {
            reRequestReviewFigure(id: $id) {
               errors
                ok
                result {
                  id
                  reviewStatus
                }
            }
        }
        '''
        self.update_event = '''
        mutation UpdateEvent($input: EventUpdateInputType!) {
            updateEvent(data: $input) {
                errors
                result {
                    id
                    reviewStatus
                    includeTriangulationInQa
                }
                ok
            }
        }'''
        self.update_figure = """
        mutation BulkUpdateFigures($items: [FigureUpdateInputType!], $delete_ids: [ID!]) {
            bulkUpdateFigures(items: $items, deleteIds: $delete_ids) {
                errors
                result {
                  id
                  reviewStatus
                }
            }
        }
        """
        self.event = EventFactory.create(assigner=self.regional_coordinator, assignee=self.monitoring_expert)
        self.country = CountryFactory.create()

    def test_all_users_can_approve_figure_except_guest(self) -> None:
        users = [self.admin, self.monitoring_expert, self.regional_coordinator]
        for user in users:
            figure = FigureFactory.create(
                event=self.event,
                review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_NOT_STARTED,
            )

            self.force_login(user)
            input = {'id': figure.id}
            response = self.query(
                self.approve_figure,
                variables=input,
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertTrue(content['data']['approveFigure']['ok'], content)
            self.assertIsNone(content['data']['approveFigure']['errors'], content)

            self.assertEqual(content['data']['approveFigure']['result']['id'], str(figure.id))
            self.assertEqual(
                content['data']['approveFigure']['result']['reviewStatus'],
                Figure.FIGURE_REVIEW_STATUS.APPROVED.name
            )

    def test_all_users_can_unapprove_figure_except_guest(self) -> None:
        users = [self.admin, self.monitoring_expert, self.regional_coordinator]
        for user in users:
            figure = FigureFactory.create(
                event=self.event,
                review_status=Figure.FIGURE_REVIEW_STATUS.APPROVED,
            )

            self.force_login(user)
            input = {'id': figure.id}
            response = self.query(
                self.unapprove_figure,
                variables=input,
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertTrue(content['data']['unapproveFigure']['ok'], content)
            self.assertIsNone(content['data']['unapproveFigure']['errors'], content)

            self.assertEqual(content['data']['unapproveFigure']['result']['id'], str(figure.id))
            self.assertEqual(
                content['data']['unapproveFigure']['result']['reviewStatus'],
                Figure.FIGURE_REVIEW_STATUS.REVIEW_NOT_STARTED.name
            )

    def test_all_users_can_re_request_review_figure_except_guest(self) -> None:
        users = [self.admin, self.monitoring_expert, self.regional_coordinator]
        for user in users:
            figure = FigureFactory.create(
                event=self.event,
                review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_IN_PROGRESS,
            )

            self.force_login(user)
            input = {'id': figure.id}
            response = self.query(
                self.re_request_review_figure,
                variables=input,
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertTrue(content['data']['reRequestReviewFigure']['ok'], content)
            self.assertIsNone(content['data']['reRequestReviewFigure']['errors'], content)

            self.assertEqual(content['data']['reRequestReviewFigure']['result']['id'], str(figure.id))
            self.assertEqual(
                content['data']['reRequestReviewFigure']['result']['reviewStatus'],
                Figure.FIGURE_REVIEW_STATUS.REVIEW_RE_REQUESTED.name
            )

    def test_review_status_should_be_review_in_progress_if_figure_has_review_comments_during_unapprove(self) -> None:
        users = [self.admin, self.monitoring_expert, self.regional_coordinator]
        for user in users:
            figure = FigureFactory.create(
                event=self.event,
                review_status=Figure.FIGURE_REVIEW_STATUS.APPROVED,
            )
            UnifiedReviewCommentFactory.create(figure=figure, event=self.event)

            self.force_login(user)
            input = {'id': figure.id}
            response = self.query(
                self.unapprove_figure,
                variables=input,
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertTrue(content['data']['unapproveFigure']['ok'], content)
            self.assertIsNone(content['data']['unapproveFigure']['errors'], content)
            self.assertEqual(content['data']['unapproveFigure']['result']['id'], str(figure.id))
            self.assertEqual(
                content['data']['unapproveFigure']['result']['reviewStatus'],
                Figure.FIGURE_REVIEW_STATUS.REVIEW_IN_PROGRESS.name
            )

    def test_event_status_should_be_changed_if_figure_status_updated(self) -> None:
        self.force_login(self.admin)

        event = EventFactory.create(include_triangulation_in_qa=True)
        f1, f2, f3 = FigureFactory.create_batch(
            3,
            event=event,
            role=Figure.ROLE.RECOMMENDED,
            review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_NOT_STARTED,
        )
        f4 = FigureFactory.create(
            event=event,
            role=Figure.ROLE.TRIANGULATION,
            review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_NOT_STARTED,
        )

        # Initially event type should be REVIEW_NOT_STARTED
        self.assertEqual(event.review_status, event.EVENT_REVIEW_STATUS.REVIEW_NOT_STARTED)

        # If any figure one of many event figures is approved review status should be REVIEW_IN_PROGRESS
        response = self.query(
            self.approve_figure,
            variables={'id': f1.id}
        )
        self.assertResponseNoErrors(response)
        event.refresh_from_db()
        self.assertEqual(event.review_status, event.EVENT_REVIEW_STATUS.REVIEW_IN_PROGRESS)

        # After all figures approved event should be also approved
        for figure in [f2, f3, f4]:
            response = self.query(
                self.approve_figure,
                variables={'id': figure.id}
            )
            self.assertResponseNoErrors(response)
        event.refresh_from_db()
        self.assertEqual(event.review_status, event.EVENT_REVIEW_STATUS.APPROVED)

        # If figure is un-approved event status should be changes to REVIEW_IN_PROGRESS
        response = self.query(
            self.unapprove_figure,
            variables={'id': f1.id}
        )
        self.assertResponseNoErrors(response)

        event.refresh_from_db()
        self.assertEqual(event.review_status, event.EVENT_REVIEW_STATUS.APPROVED_BUT_CHANGED)

    def test_event_status_should_be_calculated_if_include_triangulation_in_qa_is_changed(self):
        event = EventFactory.create(include_triangulation_in_qa=False, review_status=Event.EVENT_REVIEW_STATUS.APPROVED)
        FigureFactory.create(event=event, role=Figure.ROLE.TRIANGULATION)
        self.assertEqual(event.review_status, event.EVENT_REVIEW_STATUS.APPROVED)

        self.force_login(self.regional_coordinator)
        response = self.query(
            self.update_event,
            input_data={'id': event.id, 'includeTriangulationInQa': True}
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['updateEvent']['ok'], content)

        event.refresh_from_db()
        self.assertEqual(event.review_status, event.EVENT_REVIEW_STATUS.APPROVED_BUT_CHANGED)

    def test_should_change_figure_status_in_progress_if_figure_is_saved(self):
        entry = EntryFactory.create()
        event = EventFactory.create(
            assigner=self.regional_coordinator,
            assignee=self.monitoring_expert,
            review_status=Event.EVENT_REVIEW_STATUS.REVIEW_IN_PROGRESS,
            countries=[self.country],
        )
        figure = FigureFactory.create(
            entry=entry,
            review_status=Figure.FIGURE_REVIEW_STATUS.REVIEW_RE_REQUESTED,
            event=event,
            country=self.country,
        )
        source = dict(
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
            identifier=OSMName.IDENTIFIER.ORIGIN.name
        )
        figures = [
            {
                "uuid": str(uuid4()),
                "quantifier": Figure.QUANTIFIER.MORE_THAN_OR_EQUAL.name,
                "reported": 10,
                "unit": Figure.UNIT.HOUSEHOLD.name,  # missing household_size
                "term": Figure.FIGURE_TERMS.EVACUATED.name,
                "category": Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT.name,
                "role": Figure.ROLE.RECOMMENDED.name,
                "startDate": "2020-10-10",
                "includeIdu": True,
                "excerptIdu": "excerpt abc",
                "figureCause": Crisis.CRISIS_TYPE.CONFLICT.name,
                "geoLocations": [source],
                "event": event.id,
                "country": self.country.id,
                "id": figure.id,
                "householdSize": 20,
                "tags": [],
                "contextOfViolence": [],
                "sources": [],
                "entry": entry.id,
            },
        ]

        # Review status should not change if review requested figure is edited by non-assignee
        self.force_login(self.regional_coordinator)
        response = self.query(
            self.update_figure,
            variables={
                "items": figures,
                "delete_ids": []
            },
        )
        figure.refresh_from_db()
        content = json.loads(response.content)
        content_data = content['data']['bulkUpdateFigures']
        first_figure = content_data['result'][0]
        self.assertEqual(first_figure['id'], str(figure.id))
        self.assertEqual(first_figure['reviewStatus'], Figure.FIGURE_REVIEW_STATUS.REVIEW_RE_REQUESTED.name)

        # Review status should not change if review requested figure is edited by assignee
        self.force_login(self.monitoring_expert)
        response = self.query(
            self.update_figure,
            variables={
                "items": figures,
                "delete_ids": []
            },
        )
        figure.refresh_from_db()
        content = json.loads(response.content)
        content_data = content['data']['bulkUpdateFigures']
        first_figure = content_data['result'][0]
        self.assertEqual(first_figure['id'], str(figure.id))
        self.assertEqual(first_figure['reviewStatus'], Figure.FIGURE_REVIEW_STATUS.REVIEW_RE_REQUESTED.name)

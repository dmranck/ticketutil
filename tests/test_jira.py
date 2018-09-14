import logging
from collections import namedtuple
from unittest import main, TestCase
from unittest.mock import patch, Mock

import requests
from ticketutil.ticket import TicketException
import ticketutil.jira as jira

logging.disable(logging.CRITICAL)

URL = 'jira.com'
PROJECT = 'PROJECT'
TICKET_ID = 'PROJECT-007'
SUMMARY = 'Some irrelevant project'
DESCRIPTION = 'This project is a total failure'
TYPE = 'Task'
FIELDS = {'assignee': 'me'}
TICKET_URL = "{0}/browse/{1}".format(URL, TICKET_ID)

ERROR_MESSAGE = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
RETURN_RESULT = namedtuple('Result', ['status', 'error_message', 'url', 'ticket_content', 'watchers'])
SUCCESS_RESULT = RETURN_RESULT('Success', None, None, None, None)
FAILURE_RESULT = RETURN_RESULT('Failure', ERROR_MESSAGE, None, None, None)

MOCK_RESULT = {'errorMessages': ["No project could be found with key \'{0}\'.".format(PROJECT)]}
TICKET_CONTENT = {'key': 'TICKET_ID', 'errors': {'ResponseError': 'No internet connection'}}
STATUS = {'transitions': [{'to': {'name': 'To Do'}, 'id': 11}, {'to': {'name': 'Abandoned'}, 'id': 51}]}
WATCHERS = {'watchers': [{'name': 'me'}, {'name': 'you'}]}


class FakeSession(object):
    """
    Mocks Requests session behavior.
    """

    def __init__(self, status_code=666):
        self.status_code = status_code

    def get(self, url):
        if 'transitions' in url:
            return FakeResponseGetStatus(status_code=self.status_code)
        elif 'watchers' in url:
            return FakeResponseGetWatchers(status_code=self.status_code)
        else:
            return FakeResponse(status_code=self.status_code)

    def post(self, url, **kwargs):
        return FakeResponseManageTicket(status_code=self.status_code)

    def put(self, url, **kwargs):
        return FakeResponseManageTicket(status_code=self.status_code)

    def delete(self, url):
        return FakeResponse(status_code=self.status_code)


class FakeResponse(object):
    """
    Mock response coming from server via Requests.
    """

    def __init__(self, status_code=666):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 666:
            raise requests.RequestException

    def json(self):
        """
        Returns json-like mock result of the Jira REST API query when verifying project and ticket id.
        """
        return MOCK_RESULT


class FakeResponseManageTicket(FakeResponse):
    """
    Response when posting a request for creating ticket or editing already existing ticket.
    """

    def json(self):
        return TICKET_CONTENT


class FakeResponseGetStatus(FakeResponse):
    """
    Response when trying to get ticket status id.
    """

    def json(self):
        return STATUS


class FakeResponseGetWatchers(FakeResponse):
    """
    Response when trying to get a list of watchers.
    """

    def json(self):
        return WATCHERS


class TestJiraTicket(TestCase):
    """
    JiraTicket unit tests
    Depending on REST API request following objects are being called and used:
    _create_requests_session->FakeSession->FakeResponse
    _create_requests_session->FakeSession->FakeResponseManageTicket
    _create_requests_session->FakeSession->FakeResponseGetStatus
    _create_requests_session->FakeSession->FakeResponseGetWatchers
    """

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_generate_ticket_url(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertEqual(TICKET_URL, ticket._generate_ticket_url())
        self.assertEqual(ticket.request_result, SUCCESS_RESULT._replace(url=TICKET_URL, ticket_content=MOCK_RESULT))

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_generate_ticket_url_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        self.assertEqual(None, ticket._generate_ticket_url())
        self.assertEqual(ticket.request_result, SUCCESS_RESULT)

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_verify_project(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        self.assertTrue(ticket._verify_project(PROJECT))

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_verify_project_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        with self.assertRaises(TicketException):
            ticket = jira.JiraTicket(URL, PROJECT)
            self.assertFalse(ticket._verify_project(PROJECT))

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_get_ticket_content(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.get_ticket_content(ticket_id=TICKET_ID)
        self.assertEqual(ticket.ticket_content, MOCK_RESULT)
        self.assertEqual(t, SUCCESS_RESULT._replace(ticket_content=MOCK_RESULT, url=TICKET_URL))

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_get_ticket_content_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        error_message = "Error getting ticket content"
        with self.assertRaises(TicketException):
            ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
            t = ticket._verify_ticket_id(ticket_id=TICKET_ID)
            self.assertEqual(t, FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(jira.JiraTicket, '_create_ticket_parameters')
    @patch.object(jira.JiraTicket, '_create_ticket_request')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_create(self, mock_session, mock_request, mock_parameters):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        ticket.create(SUMMARY, DESCRIPTION, TYPE)
        mock_parameters.assert_called_once_with(SUMMARY, DESCRIPTION, TYPE, {})
        mock_request.assert_called_once_with(mock_parameters.return_value)

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_create_no_summary(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        t = ticket.create(None, DESCRIPTION, TYPE)
        error_message = 'summary is a necessary parameter for ticket creation'
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(jira, '_prepare_ticket_fields')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_create_ticket_parameters(self, mock_session, mock_fields):
        mock_fields.return_value = FIELDS
        ticket = jira.JiraTicket(URL, PROJECT)
        params = ticket._create_ticket_parameters(SUMMARY, DESCRIPTION, TYPE, FIELDS)
        expected_params = {'fields': {'project': {'key': PROJECT},
                                      'summary': SUMMARY,
                                      'description': DESCRIPTION,
                                      'issuetype': {'name': TYPE},
                                      'assignee': 'me'}}
        self.assertEqual(params, expected_params)

    @patch.object(jira.JiraTicket, 'get_ticket_content')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_create_ticket_request(self, mock_session, mock_url, mock_content):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        mock_url.return_value = 'TICKET_URL'
        request_result = ticket._create_ticket_request(FIELDS)
        self.assertEqual(ticket.ticket_id, 'TICKET_ID')
        self.assertEqual(ticket.ticket_url, 'TICKET_URL')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(jira.JiraTicket, '_create_requests_session')
    @patch.object(jira.JiraTicket, '_verify_project')
    def test_create_ticket_request_unexpected_response(self, mock_verify, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT)
        request_result = ticket._create_ticket_request(FIELDS)
        error_message = "Error creating ticket - No internet connection"
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(jira.JiraTicket, 'get_ticket_content')
    @patch.object(jira, '_prepare_ticket_fields')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_edit(self, mock_session, mock_url, mock_fields, mock_content):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.edit(summary='Edited summary')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(jira, '_prepare_ticket_fields')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_edit_no_ticket_id(self, mock_session, mock_fields):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        request_result = ticket.edit(summary='Edited summary')
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch.object(jira.JiraTicket, '_verify_ticket_id')
    @patch.object(jira.JiraTicket, '_verify_project')
    @patch.object(jira, '_prepare_ticket_fields')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_edit_unexpected_response(self, mock_session, mock_url, mock_fields, mock_verify_project,
                                      mock_verify_ticket_id):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.edit(summary='Edited summary')
        error_message = "Error editing ticket - No internet connection"
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, mock_url.return_value, None, None))

    @patch.object(jira.JiraTicket, 'get_ticket_content')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_comment(self, mock_session, mock_url, mock_content):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_comment('Status update: ...')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_comment_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        request_result = ticket.add_comment('Status update: ...')
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch.object(jira.JiraTicket, '_verify_ticket_id')
    @patch.object(jira.JiraTicket, '_verify_project')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_comment_unexpected_response(self, mock_session, mock_url, mock_verify_project, mock_verify_ticket_id):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_comment('Status update: ...')
        error_message = "Error adding comment to ticket - No internet connection"
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, mock_url.return_value, None, None))

    @patch.object(jira.JiraTicket, 'get_ticket_content')
    @patch.object(jira.JiraTicket, '_get_status_id')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_change_status(self, mock_session, mock_url, mock_get_id, mock_content):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        mock_get_id.return_value = 'STATUS_ID'
        request_result = ticket.change_status('Done')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_change_status_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        request_result = ticket.change_status('Done')
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch.object(jira.JiraTicket, '_get_status_id')
    @patch.object(jira.JiraTicket, '_verify_ticket_id')
    @patch.object(jira.JiraTicket, '_verify_project')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_change_status_unexpected_response(self, mock_session, mock_url, mock_verify_project,
                                               mock_verify_ticket_id, mock_get_id):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.change_status('Done')
        error_message = "Error changing status of ticket"
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, mock_url.return_value, None, None))

    @patch.object(jira.JiraTicket, 'get_ticket_content')
    @patch.object(jira.JiraTicket, '_get_watchers_list')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_remove_all_watchers(self, mock_session, mock_url, mock_get_list, mock_content):
        mock_session.return_value = FakeSession()
        mock_content.return_value = SUCCESS_RESULT
        watchers = ['me', 'you']
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        mock_get_list.return_value = watchers
        request_result = ticket.remove_all_watchers()
        self.assertEqual(request_result, SUCCESS_RESULT._replace(watchers=watchers))

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_remove_all_watchers_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        request_result = ticket.remove_all_watchers()
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch.object(jira.JiraTicket, '_get_watchers_list')
    @patch.object(jira.JiraTicket, '_verify_ticket_id')
    @patch.object(jira.JiraTicket, '_verify_project')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_remove_all_watchers_unexpected_response(self, mock_session, mock_url, mock_verify_project,
                                                     mock_verify_ticket_id, mock_get_list):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        mock_get_list.return_value = ['me', 'you']
        request_result = ticket.remove_all_watchers()
        error_message = "Error removing 2 watchers from ticket"
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, mock_url.return_value, None, None))

    @patch.object(jira.JiraTicket, 'get_ticket_content')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_remove_watcher(self, mock_session, mock_url, mock_content):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.remove_watcher('me')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_remove_watcher_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        request_result = ticket.remove_watcher('me')
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch.object(jira.JiraTicket, '_verify_ticket_id')
    @patch.object(jira.JiraTicket, '_verify_project')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_remove_watcher_unexpected_response(self, mock_session, mock_url, mock_verify_project,
                                                mock_verify_ticket_id):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.remove_watcher('me')
        error_message = "Error removing watcher me from ticket"
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, mock_url.return_value, None, None))

    @patch.object(jira.JiraTicket, 'get_ticket_content')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_watcher(self, mock_session, mock_url, mock_content):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_watcher('me')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_watcher_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        request_result = ticket.add_watcher('me')
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch.object(jira.JiraTicket, '_verify_ticket_id')
    @patch.object(jira.JiraTicket, '_verify_project')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_watcher_unexpected_response(self, mock_session, mock_url, mock_verify_project,
                                             mock_verify_ticket_id):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_watcher('me')
        error_message = 'Error adding "me" as a watcher to ticket'
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, mock_url.return_value, None, None))

    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_watcher_empty(self, mock_session, mock_url):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_watcher('')
        error_message = 'Error adding  as a watcher to ticket'
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, mock_url.return_value, MOCK_RESULT,
                                                       None))

    @patch.object(jira.JiraTicket, 'get_ticket_content')
    @patch('builtins.open')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_attachment(self, mock_session, mock_url, mock_open, mock_content):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_attachment_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch('builtins.open')
    @patch.object(jira.JiraTicket, '_verify_ticket_id')
    @patch.object(jira.JiraTicket, '_verify_project')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_attachment_unexpected_response(self, mock_session, mock_url, mock_verify_project,
                                                mock_verify_ticket_id, mock_open):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_attachment('file_name')
        error_message = "Error attaching file file_name"
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, mock_url.return_value, None, None))

    @patch.object(jira.JiraTicket, '_verify_ticket_id')
    @patch.object(jira.JiraTicket, '_verify_project')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_add_attachment_ioerror(self, mock_session, mock_url, mock_verify_project,
                                    mock_verify_ticket_id):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_attachment('file_name')
        error_message = "File file_name not found"
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, mock_url.return_value, None, None))

    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_get_status_id(self, mock_session, mock_url):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket._get_status_id('Abandoned')
        self.assertEqual(request_result, 51)
        request_result = ticket._get_status_id('Blocked')
        self.assertEqual(request_result, None)

    @patch.object(jira.JiraTicket, '_verify_ticket_id')
    @patch.object(jira.JiraTicket, '_verify_project')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_get_status_id_unexpected_response(self, mock_session, mock_url, mock_verify_project,
                                               mock_verify_ticket_id):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket._get_status_id('Abandoned')
        self.assertEqual(request_result, None)

    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_get_watchers_list(self, mock_session, mock_url):
        mock_session.return_value = FakeSession()
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket._get_watchers_list()
        self.assertEqual(request_result, ['me', 'you'])

    @patch.object(jira.JiraTicket, '_verify_ticket_id')
    @patch.object(jira.JiraTicket, '_verify_project')
    @patch.object(jira.JiraTicket, '_generate_ticket_url')
    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_get_watchers_list_unexpected_response(self, mock_session, mock_url, mock_verify_project,
                                                   mock_verify_ticket_id):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket._get_watchers_list()
        self.assertEqual(request_result, None)

    def test_prepare_ticket_fields(self):
        fields = {'type': 'Sub-task', 'priority': 'High', 'assignee': 'me', 'reporter': 'me', 'parent': 'Task007',
                  'duedate': '2017-01-13'}
        expected_fields = {'issuetype': {'name': 'Sub-task'},
                           'priority': {'name': 'High'},
                           'assignee': {'name': 'me'},
                           'reporter': {'name': 'me'},
                           'parent': {'key': 'Task007'},
                           'duedate': '2017-01-13'}
        prepared_fields = jira._prepare_ticket_fields(fields)
        self.assertEqual(prepared_fields, expected_fields)

    def test_prepare_ticket_fields_no_parent(self):
        fields = {'type': 'Sub-task'}
        with self.assertRaises(KeyError):
            jira._prepare_ticket_fields(fields)

    def test_prepare_ticket_fields_components(self):
        fields = {'components': ["c1", "c2"]}
        expected_fields = {
            'components': [
                {"name": "c1"},
                {"name": "c2"}
            ]
        }
        prepared_fields = jira._prepare_ticket_fields(fields)
        self.assertEqual(prepared_fields, expected_fields)

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_comment_errors(self, mock_session_factoy):
        """
        Test if error responses are handled correctly when adding comments.
        """
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.RequestException()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "errorMessages": [],
            "errors": {
                "comment": "Comment body can not be empty!"
            }
        }

        mock_session = Mock()
        mock_session.post = Mock(return_value=mock_response)

        mock_session_factoy.return_value = mock_session

        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)

        # This should not raise `IndexError: list index out of range` when
        # handling error
        ticket.add_comment('foobar')

    @patch.object(jira.JiraTicket, '_create_requests_session')
    def test_comment_error_messages(self, mock_session_factoy):
        """
        Test if error responses are handled correctly when adding comments.
        """
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.RequestException()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "errorMessages": [
                "You do not have the permission to comment on this issue."
            ],
            "errors": {}
        }

        mock_session = Mock()
        mock_session.post.return_value = mock_response

        mock_session_factoy.return_value = mock_session

        ticket = jira.JiraTicket(URL, PROJECT, ticket_id=TICKET_ID)

        # This should not raise `IndexError: list index out of range` when
        # handling error
        ticket.add_comment('foobar')


if __name__ == '__main__':
    main()

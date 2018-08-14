import logging
from collections import namedtuple
from unittest import main, TestCase
from unittest.mock import patch

import requests
import ticketutil.ticket
import ticketutil.bugzilla as bugzilla

logging.disable(logging.CRITICAL)

URL = 'bugzilla.com'
PROJECT = 'PROJECT'
TICKET_ID = 'PROJECT-007'
TICKET_ID2 = 'PROJECT-008'
TEXT = "There is no bug."
SUMMARY = 'The ticket summary'
DESCRIPTION = 'The ticket description'
COMPONENT = 'The ticket component'
VERSION = 'The ticket version'
TICKET_URL = "{0}/show_bug.cgi?id={1}".format(URL, TICKET_ID)
ERROR_MESSAGE = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"

RETURN_RESULT = namedtuple('Result', ['status', 'error_message', 'url', 'ticket_content'])
SUCCESS_RESULT = RETURN_RESULT('Success', None, None, None)
FAILURE_RESULT = RETURN_RESULT('Failure', None, None, None)
MOCK200 = {}
MOCK401 = {'error': True, 'message': 'There is some error.'}
MOCK402 = {'bugs': {0: {'changes': {}}}}


class FakeSession(object):
    """
    Mocks Requests session behavior.
    """

    def __init__(self, status_code=200, params=None, text=TEXT):
        self.status_code = status_code
        self.params = params
        self.text = text

    def get(self, url):
        if '/rest/product/' in url:
            return FakeResponseProject(status_code=self.status_code, text=self.text)
        else:
            return FakeResponse(status_code=self.status_code, text=self.text)

    def post(self, url, json, headers='headers'):
        if self.status_code == 204:
            return FakeResponseID(status_code=self.status_code, text=self.text)
        else:
            return FakeResponse(status_code=self.status_code, text=self.text)

    def put(self, url, json):
        return FakeResponse(status_code=self.status_code, text=self.text)

    def close(self):
        return


class FakeResponse(object):
    """
    Mock response coming from server via Requests.
    """

    def __init__(self, status_code=200, text=TEXT):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code not in [200, 204, 401, 402]:
            raise requests.RequestException

    def json(self):
        if self.status_code == 200:
            return MOCK200
        elif self.status_code == 401:
            return MOCK401
        elif self.status_code == 402:
            return MOCK402


class FakeResponseProject(FakeResponse):

    def json(self):
        if self.status_code == 204:
            return {"products": []}
        elif self.status_code == 200:
            return MOCK200


class FakeResponseID(FakeResponse):

    def json(self):
        if self.status_code == 204:
            return {'id': TICKET_ID2}


class TestBugzillaTicket(TestCase):

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_generate_ticket_url(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertEqual(TICKET_URL, ticket._generate_ticket_url())
        self.assertEqual(ticket.request_result, SUCCESS_RESULT._replace(url=TICKET_URL, ticket_content=MOCK200))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_generate_ticket_url_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        self.assertEqual(None, ticket._generate_ticket_url())
        self.assertEqual(ticket.request_result, SUCCESS_RESULT)

    @patch.object(ticketutil.ticket.Ticket, '_create_requests_session')
    def test_create_requests_session_kerberos_auth(self, mock_session):
        mock_session.return_value = FakeSession()
        with patch.object(bugzilla.BugzillaTicket, '_create_requests_session'):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket._create_requests_session()
        mock_session.assert_called_once()
        self.assertEqual(t, mock_session.return_value)

    @patch('ticketutil.bugzilla.requests.Session')
    def test_create_requests_session_tuple_auth(self, mock_session):
        mock_session.return_value = FakeSession(params={})
        expected_params = {'login': 'username', 'password': 'password'}
        with patch.object(bugzilla.BugzillaTicket, '_create_requests_session'):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT, auth=('username', 'password'))
        t = ticket._create_requests_session()
        self.assertDictEqual(t.params, expected_params)
        self.assertEqual(t.verify, False)

    @patch('ticketutil.bugzilla.requests.Session')
    def test_create_requests_session_api_auth(self, mock_session):
        mock_session.return_value = FakeSession(params={})
        auth = {'api_key': 'key'}
        with patch.object(bugzilla.BugzillaTicket, '_create_requests_session'):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT, auth=auth)
        t = ticket._create_requests_session()
        self.assertDictEqual(t.params, auth)
        self.assertEqual(t.verify, False)

    @patch('ticketutil.bugzilla.requests.Session')
    def test_create_requests_session_json_error(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401, params={})
        auth = {'api_key': 'key'}
        with patch.object(bugzilla.BugzillaTicket, '_create_requests_session'):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT, auth=auth)
        t = ticket._create_requests_session()
        self.assertIsNone(t)

    @patch('ticketutil.bugzilla.requests.Session')
    def test_create_requests_session_failed_request(self, mock_session):
        mock_session.return_value = FakeSession(status_code=400, params={})
        auth = {'api_key': 'key'}
        with patch.object(bugzilla.BugzillaTicket, '_create_requests_session'):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT, auth=auth)
        t = ticket._create_requests_session()
        self.assertIsNone(t)

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_verify_project(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        self.assertTrue(ticket._verify_project(PROJECT))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_verify_project_not_valid(self, mock_session):
        mock_session.return_value = FakeSession(status_code=204)
        with patch.object(bugzilla.BugzillaTicket, '_verify_project'):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        self.assertFalse(ticket._verify_project(PROJECT))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_verify_project_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=400)
        with self.assertRaises(ticketutil.ticket.TicketException):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT)
            self.assertFalse(ticket._verify_project(PROJECT))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_get_ticket_content(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, TICKET_ID)
        t = ticket.get_ticket_content(TICKET_ID)
        self.assertEqual(ticket.ticket_content, {})
        self.assertEqual(t, SUCCESS_RESULT._replace(ticket_content={}))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_get_ticket_content_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        error_message = "No ticket ID associated with ticket object. " \
                        "Set ticket ID with set_ticket_id(<ticket_id>)"
        with patch.object(bugzilla.BugzillaTicket, '_verify_ticket_id'):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        self.assertEqual(ticket.get_ticket_content(), FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_get_ticket_content_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=400)
        error_message = "Error getting ticket content"
        with self.assertRaises(ticketutil.ticket.TicketException):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT, TICKET_ID)
            self.assertEquals(ticket.get_ticket_content(), FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(bugzilla.BugzillaTicket, 'get_ticket_content')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_verify_ticket_success(self, mock_session, mock_content):
        mock_session.return_value = FakeSession()
        mock_content.return_value = SUCCESS_RESULT
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, TICKET_ID)
        self.assertTrue(ticket._verify_ticket_id(TICKET_ID))

    @patch.object(bugzilla.BugzillaTicket, 'get_ticket_content')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_verify_ticket_failure(self, mock_session, mock_content):
        mock_session.return_value = FakeSession(status_code=400)
        mock_content.return_value = FAILURE_RESULT
        with self.assertRaises(ticketutil.ticket.TicketException):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT, TICKET_ID)
            self.assertFalse(ticket._verify_ticket_id(TICKET_ID))

    @patch.object(bugzilla.BugzillaTicket, '_create_ticket_request')
    @patch.object(bugzilla.BugzillaTicket, '_create_ticket_parameters')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create(self, mock_session, mock_parameters, mock_request):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket.create(SUMMARY, DESCRIPTION, COMPONENT, VERSION, assignee='me')
        mock_parameters.assert_called_with(SUMMARY, DESCRIPTION, COMPONENT, VERSION, {'assignee': 'me'})
        self.assertEqual(t, mock_request.return_value)

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create_no_summary(self, mock_session):
        mock_session.return_value = FakeSession()
        error_message = "summary is a necessary parameter for ticket creation"
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket.create(None, DESCRIPTION, COMPONENT, VERSION, assignee='me')
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(bugzilla, '_prepare_ticket_fields')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create_ticket_parameters(self, mock_session, mock_fields):
        mock_session.return_value = FakeSession()
        FIELDS = {'assignee': 'me'}
        mock_fields.return_value = FIELDS
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket._create_ticket_parameters(SUMMARY, DESCRIPTION, COMPONENT, VERSION, FIELDS)
        expected_params = {"product": PROJECT,
                           "summary": SUMMARY,
                           "description": DESCRIPTION,
                           "component": COMPONENT,
                           "version": VERSION,
                           'assignee': 'me'}
        self.assertDictEqual(t, expected_params)

    @patch.object(bugzilla.BugzillaTicket, 'get_ticket_content')
    @patch.object(bugzilla.BugzillaTicket, '_verify_project')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create_ticket_request_id(self, mock_session, mock_project, mock_content):
        mock_session.return_value = FakeSession(status_code=204)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        with patch.object(bugzilla.BugzillaTicket, '_generate_ticket_url') as mock_url:
            t = ticket._create_ticket_request({})
        self.assertEqual(ticket.ticket_id, TICKET_ID2)
        self.assertEqual(ticket.ticket_url, mock_url.return_value)
        self.assertEqual(t, mock_content.return_value)

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create_ticket_request_error(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        error_message = 'There is some error.'
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket._create_ticket_request({})
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create_ticket_request_else(self, mock_session):
        mock_session.return_value = FakeSession()
        error_message = 'Error creating ticket'
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket._create_ticket_request({})
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(bugzilla.BugzillaTicket, '_verify_project')
    @patch.object(bugzilla.BugzillaTicket, '_verify_ticket_id')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create_ticket_request_unexpected_response(self, mock_session, mock_id, mock_project):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket._create_ticket_request({})
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=''))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_edit_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket.edit()
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=ERROR_MESSAGE))

    @patch.object(bugzilla, '_prepare_ticket_fields')
    @patch.object(bugzilla.BugzillaTicket, '_verify_project')
    @patch.object(bugzilla.BugzillaTicket, '_verify_ticket_id')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_edit_unexpected_response(self, mock_session, mock_id, mock_project, mock_fields):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.edit()
        self.assertEqual(t, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(bugzilla, '_prepare_ticket_fields')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_edit_bugs(self, mock_session, mock_fields):
        mock_session.return_value = FakeSession(status_code=402)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.edit()
        self.assertEqual(t, SUCCESS_RESULT._replace(url=TICKET_URL, ticket_content=MOCK402))

    @patch.object(bugzilla, '_prepare_ticket_fields')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_edit_error(self, mock_session, mock_fields):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.edit()
        self.assertEqual(t, RETURN_RESULT('Failure', 'There is some error.', TICKET_URL, MOCK401))

    @patch.object(bugzilla.BugzillaTicket, 'get_ticket_content')
    @patch.object(bugzilla, '_prepare_ticket_fields')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_edit(self, mock_session, mock_fields, mock_content):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.edit()
        self.assertEqual(t, mock_content.return_value)

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_comment_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket.add_comment('')
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=ERROR_MESSAGE))

    @patch.object(bugzilla.BugzillaTicket, '_verify_project')
    @patch.object(bugzilla.BugzillaTicket, '_verify_ticket_id')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_comment_unexpected_response(self, mock_session, mock_id, mock_project):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_comment('')
        self.assertEqual(t, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(bugzilla, '_prepare_ticket_fields')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_comment_error(self, mock_session, mock_fields):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_comment('')
        self.assertEqual(t, RETURN_RESULT('Failure', 'There is some error.', TICKET_URL, MOCK401))

    @patch.object(bugzilla.BugzillaTicket, 'get_ticket_content')
    @patch.object(bugzilla, '_prepare_ticket_fields')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_comment(self, mock_session, mock_fields, mock_content):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_comment('')
        self.assertEqual(t, mock_content.return_value)

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_attachment_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket.add_attachment('file_name', 'data', 'summary')
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=ERROR_MESSAGE))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_attachment_ioerror(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_attachment('file_name', 'data', 'summary')
        self.assertEqual(t, RETURN_RESULT('Failure', 'File file_name not found', TICKET_URL, MOCK200))

    @patch('ticketutil.bugzilla.base64.standard_b64encode')
    @patch('ticketutil.bugzilla.mimetypes.guess_type')
    @patch('builtins.open')
    @patch.object(bugzilla.BugzillaTicket, '_verify_project')
    @patch.object(bugzilla.BugzillaTicket, '_verify_ticket_id')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_attachment_unexpected_response(self, mock_session, mock_id, mock_project, mock_open, mock_guess_type,
                                                mock_encode):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_attachment('file_name', 'data', 'summary')
        self.assertEqual(t, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch('ticketutil.bugzilla.base64.standard_b64encode')
    @patch('ticketutil.bugzilla.mimetypes.guess_type')
    @patch('builtins.open')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_attachment_error(self, mock_session, mock_open, mock_guess_type, mock_encode):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_attachment('file_name', 'data', 'summary')
        self.assertEqual(t, RETURN_RESULT('Failure', 'There is some error.', TICKET_URL, MOCK401))

    @patch.object(bugzilla.BugzillaTicket, 'get_ticket_content')
    @patch('ticketutil.bugzilla.base64.standard_b64encode')
    @patch('ticketutil.bugzilla.mimetypes.guess_type')
    @patch('builtins.open')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_attachment(self, mock_session, mock_open, mock_guess_type, mock_encode, mock_content):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_attachment('file_name', 'data', 'summary')
        self.assertEqual(t, mock_content.return_value)

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_change_status_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket.change_status('')
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=ERROR_MESSAGE))

    @patch.object(bugzilla.BugzillaTicket, '_verify_project')
    @patch.object(bugzilla.BugzillaTicket, '_verify_ticket_id')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_change_status_unexpected_response(self, mock_session, mock_id, mock_project):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.change_status('')
        self.assertEqual(t, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(bugzilla, '_prepare_ticket_fields')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_change_status_error(self, mock_session, mock_fields):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.change_status('')
        self.assertEqual(t, RETURN_RESULT('Failure', 'There is some error.', TICKET_URL, MOCK401))

    @patch.object(bugzilla.BugzillaTicket, 'get_ticket_content')
    @patch.object(bugzilla, '_prepare_ticket_fields')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_change_status(self, mock_session, mock_fields, mock_content):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.change_status('')
        self.assertEqual(t, mock_content.return_value)

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_cc_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket.add_cc('')
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=ERROR_MESSAGE))

    @patch.object(bugzilla.BugzillaTicket, '_verify_project')
    @patch.object(bugzilla.BugzillaTicket, '_verify_ticket_id')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_cc_unexpected_response(self, mock_session, mock_id, mock_project):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_cc('')
        self.assertEqual(t, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_cc_bugs(self, mock_session):
        mock_session.return_value = FakeSession(status_code=402)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_cc('')
        self.assertEqual(t, SUCCESS_RESULT._replace(url=TICKET_URL, ticket_content=MOCK402))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_cc_error(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_cc('')
        self.assertEqual(t, RETURN_RESULT('Failure', 'There is some error.', TICKET_URL, MOCK401))

    @patch.object(bugzilla.BugzillaTicket, 'get_ticket_content')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_add_cc(self, mock_session, mock_content):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.add_cc('')
        self.assertEqual(t, mock_content.return_value)

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_remove_cc_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket.remove_cc('')
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=ERROR_MESSAGE))

    @patch.object(bugzilla.BugzillaTicket, '_verify_project')
    @patch.object(bugzilla.BugzillaTicket, '_verify_ticket_id')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_remove_cc_unexpected_response(self, mock_session, mock_id, mock_project):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.remove_cc('')
        self.assertEqual(t, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_remove_cc_bugs(self, mock_session):
        mock_session.return_value = FakeSession(status_code=402)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.remove_cc('')
        self.assertEqual(t, SUCCESS_RESULT._replace(url=TICKET_URL, ticket_content=MOCK402))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_remove_cc_error(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.remove_cc('')
        self.assertEqual(t, RETURN_RESULT('Failure', 'There is some error.', TICKET_URL, MOCK401))

    @patch.object(bugzilla.BugzillaTicket, 'get_ticket_content')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_remove_cc(self, mock_session, mock_content):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        t = ticket.remove_cc('')
        self.assertEqual(t, mock_content.return_value)

    def test_prepare_ticket_fields(self):
        fields = {'groups': ['group1', 'group2'], 'assignee': 'me'}
        expected_fields = {'groups': {'add': ['group1', 'group2']}, 'assigned_to': 'me'}
        self.assertEqual(bugzilla._prepare_ticket_fields('edit', fields), expected_fields)


if __name__ == '__main__':
    main()

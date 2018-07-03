import logging
import os
import sys
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

RETURN_RESULT = namedtuple('Result', ['status', 'error_message', 'url', 'ticket_content'])
SUCCESS_RESULT = RETURN_RESULT('Success', None, None, None)
FAILURE_RESULT = RETURN_RESULT('Failure', None, None, None)


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

    def post(self, url, json):
        if '/comment' in url:
            pass
        elif '/attachment' in url:
            pass
        elif self.status_code == 204:
            return FakeResponseID(status_code=self.status_code, text=self.text)
        else:
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
        if self.status_code not in [200, 204, 401]:
            raise requests.RequestException

    def json(self):
        if self.status_code == 200:
            return {}
        elif self.status_code == 401:
            return {'error': True, 'message': 'There is some error.'}


class FakeResponseProject(FakeResponse):

    def json(self):
        if self.status_code == 204:
            return {"products": []}
        elif self.status_code == 200:
            return {}

class FakeResponseID(FakeResponse):

    def json(self):
        if self.status_code == 204:
            return {'id': TICKET_ID2}


class TestBugzillaTicket(TestCase):

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_generate_ticket_url(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT, ticket_id=TICKET_ID)
        TICKET_URL = "{0}/show_bug.cgi?id={1}".format(URL, TICKET_ID)
        self.assertEqual(TICKET_URL, ticket._generate_ticket_url())
        self.assertEqual(ticket.request_result, SUCCESS_RESULT._replace(url=TICKET_URL))

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
            ticket = bugzilla.BugzillaTicket(URL, PROJECT, auth='kerberos')
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
    def test_verify_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        self.assertTrue(ticket._verify_ticket_id(TICKET_ID))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_verify_ticket_id_not_valid(self, mock_session):
        mock_session.return_value = FakeSession(text="Bug #{0} does not exist.".format(TICKET_ID))
        with patch.object(bugzilla.BugzillaTicket, '_verify_ticket_id'):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        self.assertFalse(ticket._verify_ticket_id(TICKET_ID))

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_verify_ticket_id_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=400)
        with self.assertRaises(ticketutil.ticket.TicketException):
            ticket = bugzilla.BugzillaTicket(URL, PROJECT)
            self.assertFalse(ticket._verify_ticket_id(TICKET_ID))

    @patch.object(bugzilla.BugzillaTicket, '_create_ticket_request')
    @patch.object(bugzilla.BugzillaTicket, '_create_ticket_parameters')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create(self, mock_session, mock_parameters, mock_request):
        mock_session.return_value = FakeSession()
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket.create(SUMMARY, DESCRIPTION, assignee='me')
        mock_parameters.assert_called_with(SUMMARY, DESCRIPTION, {'assignee':'me'})
        self.assertEqual(t, mock_request.return_value)

    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create_no_summary(self, mock_session):
        mock_session.return_value = FakeSession()
        error_message = "summary is a necessary parameter for ticket creation"
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket.create(None, DESCRIPTION, assignee='me')
        self.assertEqual(t, FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(bugzilla, '_prepare_ticket_fields')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create_ticket_parameters(self, mock_session, mock_fields):
        mock_session.return_value = FakeSession()
        FIELDS = {'assignee': 'me'}
        mock_fields.return_value = FIELDS
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        t = ticket._create_ticket_parameters(SUMMARY, DESCRIPTION, FIELDS)
        expected_params = {"product": PROJECT,
                           "summary": SUMMARY,
                           "description": DESCRIPTION,
                           'assignee': 'me'}
        self.assertDictEqual(t, expected_params)

    @patch.object(bugzilla.BugzillaTicket, '_verify_project')
    @patch.object(bugzilla.BugzillaTicket, '_create_requests_session')
    def test_create_ticket_request_id(self, mock_session, mock_project):
        mock_session.return_value = FakeSession(status_code=204)
        ticket = bugzilla.BugzillaTicket(URL, PROJECT)
        with patch.object(bugzilla.BugzillaTicket, '_generate_ticket_url') as mock_url:
            t = ticket._create_ticket_request({})
        self.assertEqual(ticket.ticket_id, TICKET_ID2)
        self.assertEqual(ticket.ticket_url, mock_url.return_value)
        self.assertEqual(t, SUCCESS_RESULT)

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

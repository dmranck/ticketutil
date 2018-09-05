import logging
from collections import namedtuple
from unittest import main, TestCase
from unittest.mock import patch

import requests
import ticketutil.ticket as ticket

logging.disable(logging.CRITICAL)

PROJECT = 'PROJECT'
TICKET_ID = 'PROJECT-007'
TICKET_ID2 = 'PROJECT-008'
URL = 'service.com'
TICKET_URL = '{0}/browse/{1}'.format(URL, TICKET_ID)
RETURN_RESULT = namedtuple('Result', ['status', 'error_message', 'url', 'ticket_content'])


class FakeSession(object):
    """
    Mocks Requests session behavior.
    """

    def __init__(self, status_code=666):
        self.status_code = status_code

    def get(self, url):
        return FakeResponse(status_code=self.status_code)

    def close(self):
        return


class FakeResponse(object):
    """
    Mock response coming from server via Requests.
    """

    def __init__(self, status_code=666):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 666:
            raise requests.RequestException


class ChildTicket(ticket.Ticket):
    """
    Mock children class from Ticket necessary for initialization of attributes the parent class does not have.
    """

    def __init__(self, project, ticket_id, auth=None, principal=None):
        self.url = URL
        self.principal = principal
        self.ticketing_tool = 'Child'
        if isinstance(auth, tuple):
            self.auth = auth
            self.auth_url = self.url
        else:
            self.auth = 'kerberos'
            self.auth_url = '{0}/step-auth-gss'.format(self.url)

        super(ChildTicket, self).__init__(project, ticket_id)

    def _verify_project(self, project):
        return True

    def get_ticket_content(ticket_id):
        if 'PROJECT-00' in ticket_id:
            return {'status': 'Success'}
        else:
            return {'status': 'Failure'}

    def _verify_ticket_id(self, ticket_id):
        if 'PROJECT-00' in ticket_id:
            return True
        else:
            return False

    def _generate_ticket_url(self):
        return TICKET_URL


class FakeCredentials(object):
    """
    Mock gssapi.Credentials object.
    """

    def __init__(self, name):
        self.name = name


class TestTicket(TestCase):

    @patch.object(ticket.Ticket, '_create_requests_session')
    def test_verify_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        t = ChildTicket(PROJECT, TICKET_ID)
        self.assertTrue(t._verify_ticket_id(TICKET_ID))

    @patch.object(ticket.Ticket, '_create_requests_session')
    def test_verify_ticket_id_non_valid(self, mock_session):
        mock_session.return_value = FakeSession()
        t = ChildTicket(PROJECT, TICKET_ID)
        self.assertFalse(t._verify_ticket_id('PROJECT-010'))

    @patch.object(ticket.Ticket, '_create_requests_session')
    def test_set_ticket_id(self, mock_session):
        t = ChildTicket(PROJECT, TICKET_ID)
        t.set_ticket_id(TICKET_ID2)
        self.assertEqual(t.ticket_id, TICKET_ID2)
        self.assertEqual(t.ticket_url, TICKET_URL)
        self.assertEqual(t.request_result, RETURN_RESULT('Success', None, None, None))

    @patch.object(ticket.Ticket, '_create_requests_session')
    def test_set_ticket_id_failure(self, mock_session):
        t = ChildTicket(PROJECT, TICKET_ID)
        request_result = t.set_ticket_id('PROJECT-010')
        error_message = "Ticket ID not valid"
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, None, None))

    @patch.object(ticket.Ticket, '_create_requests_session')
    def test_get_ticket_id(self, mock_session):
        t = ChildTicket(PROJECT, TICKET_ID)
        self.assertEqual(t.get_ticket_id(), TICKET_ID)

    @patch.object(ticket.Ticket, '_create_requests_session')
    def test_get_ticket_url(self, mock_session):
        t = ChildTicket(PROJECT, TICKET_ID)
        self.assertEqual(t.get_ticket_url(), TICKET_URL)

    @patch('ticketutil.ticket.HTTPKerberosAuth')
    @patch('ticketutil.ticket.requests.Session')
    @patch.object(ticket, '_get_kerberos_principal')
    def test_create_request_session_kerberos_auth(self, mock_principal, mock_session, mock_auth):
        mock_session.return_value = FakeSession()
        with patch.object(ticket.Ticket, '_create_requests_session'):
            t = ChildTicket(PROJECT, TICKET_ID)
        s = t._create_requests_session()
        self.assertEqual(t.principal, mock_principal.return_value)
        self.assertEqual(s.auth, mock_auth.return_value)

    @patch('ticketutil.ticket.requests.Session')
    def test_create_request_session_tuple_auth(self, mock_session):
        mock_session.return_value = FakeSession()
        auth = ('username', 'password')
        with patch.object(ticket.Ticket, '_create_requests_session'):
            t = ChildTicket(PROJECT, TICKET_ID, auth=auth)
        s = t._create_requests_session()
        self.assertEqual(t.principal, None)
        self.assertEqual(s.auth, auth)

    @patch('ticketutil.ticket.requests.Session')
    def test_create_request_session_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        auth = ('username', 'password')
        with patch.object(ticket.Ticket, '_create_requests_session'):
            t = ChildTicket(PROJECT, TICKET_ID, auth=auth)
        s = t._create_requests_session()
        self.assertEqual(s, None)

    @patch('ticketutil.ticket.requests.Session')
    def test_close_requests_session(self, mock_session):
        mock_session.return_value = FakeSession()
        t = ChildTicket(PROJECT, TICKET_ID)
        request_result = t.close_requests_session()
        self.assertEqual(request_result, RETURN_RESULT('Success', None, None, None))

    @patch('ticketutil.ticket.gssapi.Credentials')
    def test_get_kerberos_principal(self, mock_credentials):
        mock_credentials.return_value = FakeCredentials(u'me@REDHAT.COM')
        ticket._get_kerberos_principal()
        self.assertEqual(ticket._get_kerberos_principal(), 'me@redhat.com')


if __name__ == '__main__':
    main()

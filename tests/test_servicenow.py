import os
import sys
import logging
import requests

from unittest import main, TestCase
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), '../ticketutil/'))

import servicenow

logging.disable(logging.CRITICAL)

TICKET_ID = 'PNT9999999'
TEST_URL = 'servicenow.com'
TABLE = 'x_table'

STATE = {'new': '0',
         'open': '1',
         'work in progress': '2',
         'pending': '-6',
         'pending approval': '-9',
         'pending customer': '-1',
         'pending change': '-4',
         'pending vendor': '-5',
         'resolved': '5',
         'closed completed': '3',
         'closed cancelled': '8'}

DESCRIPTION = 'full-length ticket description'
SHORT_DESCRIPTION = 'short description'
CATEGORY = 'category'
ITEM = 'item'

MOCK_RESULT = {'number': TICKET_ID,
               'state': STATE['new'],
               'watch_list': 'pzubaty@redhat.com',
               'comments': '',
               'sys_id': '#34346',
               'description': DESCRIPTION,
               'short_description': SHORT_DESCRIPTION,
               'u_category': CATEGORY,
               'u_item': ITEM}


class FakeResponse(object):
    """Mock response coming from server via Requests
    """

    def __init__(self, status_code=666):
        self.status_code = status_code
        self.content = "ABC"
        self.text = self.content

    def raise_for_status(self):
        if self.status_code != 666:
            raise requests.RequestException

    def json(self, data=None):
        """Returns json-like mock result of the ServiceNow REST API query
        :param data: append extra data to simulate expected result
        """
        result = MOCK_RESULT
        if data:
            result.update(data)
        return {'result': result}


class FakeResponseQuery(FakeResponse):
    """Response on search query,
    eg. '<REST_URL>?sysparm_query=GOTOnumber%3D<TICKET_ID>'
    """

    def json(self):
        return {'result': [MOCK_RESULT]}


class FakeSession(object):
    """Mocks Requests session behavior
    """

    def __init__(self, status_code=666):
        self.status_code = status_code
        self.headers = {'Content-Type': 'application/json', }

    def get(self, url):
        return FakeResponse(status_code=self.status_code)

    def post(self, url, data):
        return FakeResponse(status_code=self.status_code)

    def put(self, url, data):
        return FakeResponse(status_code=self.status_code)


class FakeSessionQuery(FakeSession):
    """Mocks Requests session behavior for search query
    """

    def get(self, url):
        return FakeResponseQuery(status_code=self.status_code)


def mock_get_ticket_content(self, ticket_id):
    return MOCK_RESULT


def mock_verify_project(self, project):
    return project == TABLE


class TestServiceNowTicket(TestCase):
    """ServiceNowTicket unit tests
    Depending on REST API request following objects are being called and used:
    _create_requests_session->FakeSession->FakeResponse
    _create_requests_session->FakeSessionQuery->FakeResponseQuery
    """

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    def test_get_ticket_content(self, mock_session):
        mock_session.return_value = FakeSessionQuery()
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE)
        result = ticket.get_ticket_content(ticket_id=TICKET_ID)
        self.assertEqual(result, MOCK_RESULT)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    def test_get_ticket_content_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSessionQuery(status_code=404)
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE)
        result = ticket.get_ticket_content(ticket_id=TICKET_ID)
        self.assertEqual(result, False)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    def test_create(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE)
        ticket.create(DESCRIPTION, SHORT_DESCRIPTION, CATEGORY, ITEM)
        self.assertEqual(ticket.ticket_content, MOCK_RESULT)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    def test_create_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=404)
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE)
        ticket.create(DESCRIPTION, SHORT_DESCRIPTION, CATEGORY, ITEM)
        self.assertEqual(ticket.ticket_content, None)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_change_status(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        ticket.change_status('Pending')
        expected_result = MOCK_RESULT
        expected_result.update({'state': STATE['pending']})
        self.assertEqual(ticket.ticket_content, expected_result)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_change_status_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=404)
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        result = ticket.change_status('Pending')
        self.assertEqual(result, False)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_edit(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        ticket.edit(priority='2', impact='2')
        expected_result = MOCK_RESULT
        expected_result.update({'priority': '2', 'impact': '2'})
        self.assertEqual(ticket.ticket_content, expected_result)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_edit_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=404)
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        result = ticket.edit(priority='2', impact='2')
        self.assertEqual(result, False)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_add_comment(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        ticket.add_comment('New comment')
        expected_result = MOCK_RESULT
        expected_result.update({'comments': 'New comment'})
        self.assertEqual(ticket.ticket_content, expected_result)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_add_comment_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=404)
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        result = ticket.add_comment('New comment')
        self.assertEqual(result, False)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_add_cc(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        ticket.add_cc('pzubaty@redhat.com')
        expected_result = MOCK_RESULT
        expected_result.update({'watch_list': 'pzubaty@redhat.com'})
        self.assertEqual(ticket.ticket_content, expected_result)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_add_cc_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=404)
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        result = ticket.add_cc('pzubaty@redhat.com')
        self.assertEqual(result, False)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_rewrite_cc(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        ticket.rewrite_cc(['pzubaty@redhat.com', 'dranck@redhat.com'])
        expected_result = MOCK_RESULT
        expected_result.update({'watch_list':
                                'pzubaty@redhat.com, dranck@redhat.com'})
        self.assertEqual(ticket.ticket_content, expected_result)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_rewrite_cc_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=404)
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        result = ticket.rewrite_cc(['pzubaty@redhat.com', 'dranck@redhat.com'])
        self.assertEqual(result, False)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_remove_cc(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        ticket.remove_cc(['dranck@redhat.com', 'mail@redhat.com'])
        expected_result = MOCK_RESULT
        expected_result.update({'watch_list': 'pzubaty@redhat.com'})
        self.assertEqual(ticket.ticket_content, expected_result)

    @patch.object(servicenow.ServiceNowTicket, '_create_requests_session')
    @patch('servicenow.ServiceNowTicket._verify_project', mock_verify_project)
    @patch('servicenow.ServiceNowTicket.get_ticket_content',
           mock_get_ticket_content)
    def test_remove_cc_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=404)
        ticket = servicenow.ServiceNowTicket(TEST_URL, TABLE,
                                             ticket_id=TICKET_ID)
        result = ticket.remove_cc(['dranck@redhat.com', 'mail@redhat.com'])
        self.assertEqual(result, False)

if __name__ == '__main__':
    main()

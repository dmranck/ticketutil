import logging
from collections import namedtuple
from unittest import main, TestCase
from unittest.mock import patch

import requests
import ticketutil.redmine as redmine

logging.disable(logging.CRITICAL)

URL = 'redmine.com'
PROJECT = 'PROJECT'
TICKET_ID = 'PROJECT-007'
TICKET_URL = "{0}/issues/{1}".format(URL, TICKET_ID)
SUBJECT = 'The ticket subject'
DESCRIPTION = 'The ticket description'
HEADERS = {}
ERROR_MESSAGE = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"

RETURN_RESULT = namedtuple('Result', ['status', 'error_message', 'url', 'ticket_content'])
SUCCESS_RESULT = RETURN_RESULT('Success', None, TICKET_URL, None)
FAILURE_RESULT1 = RETURN_RESULT('Failure', ERROR_MESSAGE, None, None)
FAILURE_RESULT2 = RETURN_RESULT('Failure', '', TICKET_URL, None)

MOCK_CONTENT = {'issue': {'id': TICKET_ID},
                'upload': {'token': 'Token'},
                'project': {'id': 'ID'},
                'issue_statuses': [{'name': 'started', 'id': 1}, {'name': 'finished', 'id': 2}],
                'issue_priorities': [{'name': 'low', 'id': 1}, {'name': 'high', 'id': 2}],
                'users': [{'login': 'me', 'id': 1}, {'login': 'you', 'id': 2}]}


class FakeSession(object):
    """
    Mocks Requests session behavior.
    """

    def __init__(self, status_code=200, headers=HEADERS):
        self.status_code = status_code
        self.headers = headers

    def delete(self, url):
        return FakeResponse(status_code=self.status_code)

    def get(self, url):
        return FakeResponse(status_code=self.status_code)

    def post(self, url, **kwargs):
        return FakeResponse(status_code=self.status_code)

    def put(self, url, json):
        return FakeResponse(status_code=self.status_code)

    def close(self):
        return


class FakeResponse(object):
    """
    Mock response coming from server via Requests.
    """

    def __init__(self, status_code=200):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code == 400:
            raise requests.RequestException
        if self.status_code == 401:
            raise IOError

    def json(self):
        return MOCK_CONTENT


class TestRedmineTicket(TestCase):

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_generate_ticket_url(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertEqual(TICKET_URL, ticket._generate_ticket_url())
        self.assertEqual(ticket.request_result, SUCCESS_RESULT)

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_generate_ticket_url_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        self.assertEqual(None, ticket._generate_ticket_url())
        self.assertEqual(ticket.request_result, SUCCESS_RESULT._replace(url=None))

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_verify_project(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        self.assertTrue(ticket._verify_project(PROJECT))

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_verify_project_not_valid(self, mock_session):
        mock_session.return_value = FakeSession(status_code=400)
        with patch.object(redmine.RedmineTicket, '_verify_project'):
            ticket = redmine.RedmineTicket(URL, PROJECT)
        self.assertFalse(ticket._verify_project(PROJECT))

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_ticket_content_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        t = ticket.get_ticket_content()
        self.assertEqual(t, FAILURE_RESULT1)

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_ticket_content_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=400)
        error_message = "Error getting ticket content"
        with patch.object(redmine.RedmineTicket, '_verify_project'):
            ticket = redmine.RedmineTicket(URL, PROJECT, TICKET_ID)
        t = ticket.get_ticket_content(ticket_id=TICKET_ID)
        self.assertEqual(t, FAILURE_RESULT1._replace(error_message=error_message))

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_ticket_content(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, TICKET_ID)
        t = ticket.get_ticket_content(ticket_id=TICKET_ID)
        self.assertEqual(t.ticket_content, MOCK_CONTENT)

    @patch.object(redmine.RedmineTicket, '_create_ticket_request')
    @patch.object(redmine.RedmineTicket, '_create_ticket_parameters')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_create(self, mock_session, mock_parameters, mock_request):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket.create(SUBJECT, DESCRIPTION, assignee='me')
        mock_parameters.assert_called_with(SUBJECT, DESCRIPTION, {'assignee': 'me'})
        self.assertEqual(request_result, mock_request.return_value)

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_create_no_summary(self, mock_session):
        mock_session.return_value = FakeSession()
        error_message = "subject is a necessary parameter for ticket creation"
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket.create(None, DESCRIPTION, assignee='me')
        self.assertEqual(request_result, FAILURE_RESULT1._replace(error_message=error_message))

    @patch.object(redmine.RedmineTicket, '_prepare_ticket_fields')
    @patch.object(redmine.RedmineTicket, '_get_project_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_create_ticket_parameters(self, mock_session, mock_id, mock_fields):
        mock_session.return_value = FakeSession()
        FIELDS = {'assignee': 'me'}
        mock_fields.return_value = FIELDS
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket._create_ticket_parameters(SUBJECT, DESCRIPTION, FIELDS)
        expected_params = {'issue': {'project_id': mock_id.return_value,
                                     'subject': SUBJECT,
                                     'description': DESCRIPTION,
                                     'assignee': 'me'}}
        self.assertDictEqual(request_result, expected_params)

    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_create_ticket_request_unexpected_response(self, mock_session, mock_id, mock_project):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket._create_ticket_request({})
        self.assertEqual(request_result, FAILURE_RESULT1._replace(error_message=''))

    @patch.object(redmine.RedmineTicket, 'get_ticket_content')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_create_ticket_request(self, mock_session, mock_content):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket._create_ticket_request({})
        self.assertEqual(ticket.ticket_id, TICKET_ID)
        self.assertEqual(ticket.ticket_url, TICKET_URL)
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_edit_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket.edit()
        self.assertEqual(request_result, FAILURE_RESULT1)

    @patch.object(redmine.RedmineTicket, '_prepare_ticket_fields')
    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_edit_unexpected_response(self, mock_session, mock_id, mock_project, mock_fields):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.edit()
        self.assertEqual(request_result, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(redmine.RedmineTicket, 'get_ticket_content')
    @patch.object(redmine.RedmineTicket, '_prepare_ticket_fields')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_edit(self, mock_session, mock_fields, mock_content):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.edit()
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_comment_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket.add_comment('')
        self.assertEqual(request_result, FAILURE_RESULT1)

    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_comment_unexpected_response(self, mock_session, mock_id, mock_project):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_comment('')
        self.assertEqual(request_result, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(redmine.RedmineTicket, 'get_ticket_content')
    @patch.object(redmine.RedmineTicket, '_prepare_ticket_fields')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_comment(self, mock_session, mock_fields, mock_content):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_comment('')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_change_status_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket.change_status('')
        self.assertEqual(request_result, FAILURE_RESULT1)

    @patch.object(redmine.RedmineTicket, '_get_status_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_change_status_no_status_id(self, mock_session, mock_get_id):
        mock_session.return_value = FakeSession()
        mock_get_id.return_value = 0
        error_message = "Not a valid status: "
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.change_status('')
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, TICKET_URL, None))

    @patch.object(redmine.RedmineTicket, '_get_status_id')
    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_change_status_unexpected_response(self, mock_session, mock_id, mock_project, mock_get_id):
        mock_session.return_value = FakeSession(status_code=400)
        mock_get_id.return_value = 1
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.change_status('')
        self.assertEqual(request_result, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(redmine.RedmineTicket, 'get_ticket_content')
    @patch.object(redmine.RedmineTicket, '_get_status_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_change_status(self, mock_session, mock_get_id, mock_content):
        mock_session.return_value = FakeSession()
        mock_get_id.return_value = 1
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.change_status('')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_remove_watcher_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket.remove_watcher('me')
        self.assertEqual(request_result, FAILURE_RESULT1)

    @patch.object(redmine.RedmineTicket, '_get_user_id')
    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_remove_watcher_unexpected_response(self, mock_session, mock_project, mock_ticket_id, mock_get_id):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.remove_watcher('me')
        self.assertEqual(request_result, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(redmine.RedmineTicket, 'get_ticket_content')
    @patch.object(redmine.RedmineTicket, '_get_user_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_remove_watcher(self, mock_session, mock_get_id, mock_content):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.remove_watcher('me')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_watcher_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket.add_watcher('me')
        self.assertEqual(request_result, FAILURE_RESULT1)

    @patch.object(redmine.RedmineTicket, 'get_ticket_content')
    @patch.object(redmine.RedmineTicket, '_get_user_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_watcher(self, mock_session, mock_get_id,  mock_content):
        mock_session.return_value = FakeSession()
        mock_get_id.return_value = 1
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_watcher('me')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(redmine.RedmineTicket, '_get_user_id')
    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_watcher_unexpected_response(self, mock_session, mock_project, mock_ticket_id, mock_get_id):
        mock_session.return_value = FakeSession(status_code=400)
        mock_get_id.return_value = 1
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_watcher('me')
        self.assertEqual(request_result, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(redmine.RedmineTicket, '_get_user_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_watcher_no_watcher_id(self, mock_session, mock_get_id):
        mock_get_id.return_value = 0
        mock_session.return_value = FakeSession()
        error_message = "Error adding me as a watcher to ticket"
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_watcher('me')
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, TICKET_URL, None))

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_attachment_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, FAILURE_RESULT1)

    @patch.object(redmine.RedmineTicket, 'get_ticket_content')
    @patch.object(redmine.RedmineTicket, '_upload_file')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_attachment(self, mock_session, mock_upload, mock_content):
        mock_session.return_value = FakeSession()
        mock_upload.return_value = 1
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, mock_content.return_value)

    @patch.object(redmine.RedmineTicket, '_upload_file')
    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_attachment_unexpected_response(self, mock_session, mock_project, mock_ticket_id, mock_upload):
        mock_session.return_value = FakeSession(status_code=400)
        mock_upload.return_value = 1
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, RETURN_RESULT('Failure', '', TICKET_URL, None))

    @patch.object(redmine.RedmineTicket, '_upload_file')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_add_attachment_no_token(self, mock_session, mock_upload):
        mock_session.return_value = FakeSession()
        mock_upload.return_value = 0
        error_message = "Error attaching file file_name"
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, RETURN_RESULT('Failure', error_message, TICKET_URL, None))

    @patch('builtins.open')
    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_upload_file_unexpected_response(self, mock_session, mock_project, mock_ticket_id, mock_open):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertFalse(ticket._upload_file('file_name'))

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_upload_file_ioerror(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertFalse(ticket._upload_file('file_name'))

    @patch('builtins.open')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_upload_file(self, mock_session, mock_open):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket._upload_file('file_name')
        self.assertEqual(request_result, 'Token')

    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_project_id_unexpected_response(self, mock_session, mock_project, mock_ticket_id):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertFalse(ticket._get_project_id())

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_project(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket._get_project_id()
        self.assertEqual(request_result, 'ID')

    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_status_id_unexpected_response(self, mock_session, mock_project, mock_ticket_id):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertFalse(ticket._get_status_id('finished'))

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_status_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket._get_status_id('finished')
        self.assertEqual(request_result, 2)

    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_priority_id_unexpected_response(self, mock_session, mock_project, mock_ticket_id):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertFalse(ticket._get_priority_id('low'))

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_priority_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket._get_priority_id('low')
        self.assertEqual(request_result, 1)

    @patch.object(redmine.RedmineTicket, '_verify_ticket_id')
    @patch.object(redmine.RedmineTicket, '_verify_project')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_user_id_unexpected_response(self, mock_session, mock_project, mock_ticket_id):
        mock_session.return_value = FakeSession(status_code=400)
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertFalse(ticket._get_user_id('me'))

    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_get_user_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket._get_user_id('me@redhat.com')
        self.assertEqual(request_result, 1)

    @patch.object(redmine.RedmineTicket, '_get_user_id')
    @patch.object(redmine.RedmineTicket, '_get_priority_id')
    @patch.object(redmine.RedmineTicket, '_create_requests_session')
    def test_prepare_ticket_fields(self, mock_session, mock_priority_id, mock_user_id):
        mock_session.return_value = FakeSession()
        mock_priority_id.return_value = 1
        mock_user_id.return_value = 2
        fields = {'priority': 'low', 'assignee': 'me', 'estimated_time': 3}
        expected_fields = {'priority_id': 1, 'assigned_to_id': 2, 'total_estimated_hours': 3}
        ticket = redmine.RedmineTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertDictEqual(ticket._prepare_ticket_fields(fields), expected_fields)


if __name__ == '__main__':
    main()

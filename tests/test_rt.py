import logging
from collections import namedtuple
from unittest import main, TestCase
from unittest.mock import patch

import requests

import ticketutil.rt as rt

logging.disable(logging.CRITICAL)

URL = 'rt.com'
PROJECT = 'PROJECT'
TICKET_ID = 'PROJECT-007'
TICKET_URL = '{0}/Ticket/Display.html?id={1}'.format(URL, TICKET_ID)
SUBJECT = 'The ticket subject'
TEXT = 'The ticket description.\n'
ERROR_MESSAGE = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"

RETURN_RESULT = namedtuple('Result', ['status', 'error_message', 'url', 'ticket_content'])
SUCCESS_RESULT = RETURN_RESULT('Success', None, TICKET_URL, None)
FAILURE_RESULT = RETURN_RESULT('Failure', ERROR_MESSAGE, None, None)


class FakeSession(object):
    """
    Mocks Requests session behavior.
    """

    def __init__(self, status_code=200, principal=None, params={}):
        self.status_code = status_code
        self.principal = principal
        self.params = params

    def get(self, url):
        if 'queue' in url or 'ticket' in url:
            return FakeResponse404(status_code=self.status_code)
        else:
            return FakeResponse(status_code=self.status_code)

    def post(self, url, data=None, files=None):
        return FakeResponse(status_code=self.status_code)

    def close(self):
        return


class FakeResponse(object):
    """
    Mock response coming from server via Requests.
    """

    def __init__(self, status_code=200):
        self.status_code = status_code
        if self.status_code == 200:
            self.text = '200 OK'
        elif self.status_code == 201:
            self.text = '201 Ticket 007 created'
        elif self.status_code == 202:
            self.text = '202 Could not create ticket.'
        elif self.status_code == 204:
            self.text = '204 No queue named {0} exists. Check the project name.'.format(PROJECT)
        elif self.status_code == 400:
            self.text = '400 Bad Request'
        elif self.status_code == 409:
            self.text = '409 Syntax Error'
        else:
            self.text = ''

    def raise_for_status(self):
        if self.status_code == 401:
            raise requests.RequestException


class FakeResponse404(FakeResponse):

    def raise_for_status(self):
        if self.status_code == 404:
            raise requests.RequestException


class TestRTTicket(TestCase):

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_generate_ticket_url(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        self.assertEqual(TICKET_URL, ticket._generate_ticket_url())
        self.assertEqual(ticket.request_result, SUCCESS_RESULT)

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_generate_ticket_url_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT)
        self.assertEqual(None, ticket._generate_ticket_url())
        self.assertEqual(ticket.request_result, SUCCESS_RESULT._replace(url=None))

    @patch('ticketutil.rt.HTTPKerberosAuth')
    @patch('ticketutil.ticket._get_kerberos_principal')
    @patch('ticketutil.rt.requests.Session')
    def test_create_requests_session_kerberos_auth(self, mock_session, mock_principal, mock_auth):
        mock_session.return_value = FakeSession()
        with patch.object(rt.RTTicket, '_create_requests_session'):
            ticket = rt.RTTicket(URL, PROJECT, auth='kerberos')
        session = ticket._create_requests_session()
        self.assertEqual(ticket.principal, mock_principal.return_value)
        self.assertEqual(session.auth, mock_auth.return_value)
        self.assertEqual(session.verify, False)

    @patch('ticketutil.rt.requests.Session')
    def test_create_requests_session_tuple_auth(self, mock_session):
        mock_session.return_value = FakeSession()
        auth = ('me', 'unbreakablepassword')
        params = {'user': 'me', 'pass': 'unbreakablepassword'}
        with patch.object(rt.RTTicket, '_create_requests_session'):
            ticket = rt.RTTicket(URL, PROJECT, auth=auth)
        session = ticket._create_requests_session()
        self.assertEqual(ticket.principal, 'me')
        self.assertEqual(session.params, params)

    @patch('ticketutil.rt.requests.Session')
    def test_create_requests_session_bad_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=201)
        with patch.object(rt.RTTicket, '_create_requests_session'):
            ticket = rt.RTTicket(URL, PROJECT)
        self.assertFalse(ticket._create_requests_session())

    @patch('ticketutil.rt.requests.Session')
    def test_create_requests_session_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        with patch.object(rt.RTTicket, '_create_requests_session'):
            ticket = rt.RTTicket(URL, PROJECT)
        self.assertFalse(ticket._create_requests_session())

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_verify_project_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=404)
        with patch.object(rt.RTTicket, '_verify_project'):
            ticket = rt.RTTicket(URL, PROJECT)
        self.assertFalse(ticket._verify_project(PROJECT))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_verify_project_not_valid(self, mock_session):
        mock_session.return_value = FakeSession(status_code=204)
        with patch.object(rt.RTTicket, '_verify_project'):
            ticket = rt.RTTicket(URL, PROJECT)
        self.assertFalse(ticket._verify_project(PROJECT))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_verify_project(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT)
        self.assertTrue(ticket._verify_project(PROJECT))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_get_ticket_content_no_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT)
        self.assertEqual(ticket.get_ticket_content(), FAILURE_RESULT)

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_get_ticket_content_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=404)
        error_message = "Error getting ticket content"
        with patch.object(rt.RTTicket, '_verify_project'):
            ticket = rt.RTTicket(URL, PROJECT)
        self.assertEqual(ticket.get_ticket_content(TICKET_ID), FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_get_ticket_content_id_not_valid(self, mock_session):
        mock_session.return_value = FakeSession(status_code=400)
        error_message = "Ticket {0} is not valid".format(TICKET_ID)
        ticket = rt.RTTicket(URL, PROJECT)
        self.assertEqual(ticket.get_ticket_content(TICKET_ID), FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_get_ticket_content(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT)
        t = ticket.get_ticket_content(TICKET_ID)
        self.assertEqual(t, SUCCESS_RESULT._replace(url=None, ticket_content={'header': ['200 OK']}))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_create_no_subject(self, mock_session):
        mock_session.return_value = FakeSession()
        error_message = "subject is a necessary parameter for ticket creation"
        ticket = rt.RTTicket(URL, PROJECT)
        request_result = ticket.create(None, TEXT, assignee='me')
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(rt.RTTicket, '_create_ticket_request')
    @patch.object(rt.RTTicket, '_create_ticket_parameters')
    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_create(self, mock_session, mock_parameters, mock_request):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT)
        request_result = ticket.create(SUBJECT, TEXT, assignee='me')
        mock_parameters.assert_called_with(SUBJECT, TEXT, {'assignee': 'me'})
        self.assertEqual(request_result, mock_request.return_value)

    @patch.object(rt, '_prepare_ticket_fields')
    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_create_ticket_parameters(self, mock_session, mock_fields):
        mock_session.return_value = FakeSession()
        fields = {'assignee': 'me'}
        mock_fields.return_value = fields
        content = 'Queue: {0}\nRequestor: {1}\nSubject: {2}\nText: {3}      \n'.format(PROJECT, None, SUBJECT, TEXT)
        content += 'Assignee: me\n'
        ticket = rt.RTTicket(URL, PROJECT)
        ticket.principal = None
        params = ticket._create_ticket_parameters(SUBJECT, TEXT, fields)
        self.assertDictEqual(params, {'content': content})

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_create_ticket_request_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = rt.RTTicket(URL, PROJECT)
        request_result = ticket._create_ticket_request('')
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message=''))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_create_ticket_request_failed(self, mock_session):
        mock_session.return_value = FakeSession(status_code=202)
        ticket = rt.RTTicket(URL, PROJECT)
        error_message = '202 Could not create ticket.'
        request_result = ticket._create_ticket_request('')
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message=error_message))

    @patch.object(rt.RTTicket, '_generate_ticket_url')
    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_create_ticket_request(self, mock_session, mock_url):
        mock_session.return_value = FakeSession(status_code=201)
        ticket = rt.RTTicket(URL, PROJECT)
        request_result = ticket._create_ticket_request('')
        self.assertEqual(request_result,
                         SUCCESS_RESULT._replace(url=None, ticket_content={'header': ['201 Ticket 007 created']}))
        self.assertEqual(ticket.ticket_id, '007')
        self.assertEqual(ticket.ticket_url, mock_url.return_value)

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_edit_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT)
        request_result = ticket.edit()
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_edit_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.edit()
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message='', url=TICKET_URL))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_edit_syntax_error(self, mock_session):
        mock_session.return_value = FakeSession(status_code=409)
        error_message = '409 Syntax Error'
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.edit()
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message=error_message, url=TICKET_URL))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_edit(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.edit()
        self.assertEqual(request_result, SUCCESS_RESULT._replace(ticket_content={'header': ['200 OK']}))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_add_comment_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT)
        request_result = ticket.add_comment('')
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_add_comment_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_comment('')
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message='', url=TICKET_URL))

    @patch.object(rt.RTTicket, '_verify_ticket_id')
    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_add_comment_bad_request(self, mock_session, mock_id):
        mock_session.return_value = FakeSession(status_code=400)
        error_message = '400 Bad Request'
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_comment('')
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message=error_message, url=TICKET_URL))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_add_comment(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_comment('')
        self.assertEqual(request_result, SUCCESS_RESULT._replace(ticket_content={'header': ['200 OK']}))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_change_status_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT)
        request_result = ticket.change_status('')
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_change_status_unexpected_response(self, mock_session):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.change_status('')
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message='', url=TICKET_URL))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_change_status_syntax_error(self, mock_session):
        mock_session.return_value = FakeSession(status_code=409)
        error_message = '409 Syntax Error'
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.change_status('')
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message=error_message, url=TICKET_URL))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_change_status(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.change_status('')
        self.assertEqual(request_result, SUCCESS_RESULT._replace(ticket_content={'header': ['200 OK']}))

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_add_attachment_no_ticket_id(self, mock_session):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, FAILURE_RESULT)

    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_add_attachment_ioerror(self, mock_session):
        mock_session.return_value = FakeSession()
        error_message = 'File file_name not found'
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message=error_message, url=TICKET_URL))

    @patch('builtins.open')
    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_add_attachment_unexpected_response(self, mock_session, mock_open):
        mock_session.return_value = FakeSession(status_code=401)
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message='', url=TICKET_URL))

    @patch('builtins.open')
    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_add_attachment_bad_error(self, mock_session, mock_open):
        mock_session.return_value = FakeSession(status_code=202)
        error_message = '202 Could not create ticket.'
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, FAILURE_RESULT._replace(error_message=error_message, url=TICKET_URL))

    @patch('builtins.open')
    @patch.object(rt.RTTicket, '_create_requests_session')
    def test_add_attachment(self, mock_session, mock_open):
        mock_session.return_value = FakeSession()
        ticket = rt.RTTicket(URL, PROJECT, ticket_id=TICKET_ID)
        request_result = ticket.add_attachment('file_name')
        self.assertEqual(request_result, SUCCESS_RESULT._replace(ticket_content={'header': ['200 OK']}))

    def test_prepare_ticket_fields(self):
        fields = {'cc': 'something', 'admincc': ['me', 'you']}
        expected_result = {'cc': 'something', 'admincc': 'me, you'}
        result = rt._prepare_ticket_fields(fields)
        self.assertEqual(result, expected_result)

    def test_convert_string(self):
        string1 = 'Header1\n\nHeader2\n id: 1\n Attachments:   1000: file'
        string2 = 'Header1\n\n Stack:\n id: 1\n Attachments:   1000: file'
        expected_result1 = {'header': ['Header1', 'Header2'], 'id': '1', '1000': 'file'}
        expected_result2 = ['Header1', '', ' Stack:', ' id: 1', ' Attachments:   1000: file']
        self.assertDictEqual(rt._convert_string(string1), expected_result1)
        self.assertEqual(rt._convert_string(string2), expected_result2)


if __name__ == '__main__':
    main()

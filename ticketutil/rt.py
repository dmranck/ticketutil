import logging
import re

import requests
from requests_kerberos import HTTPKerberosAuth, DISABLED

from . import ticket

__author__ = 'dranck, rnester, kshirsal'

logger = logging.getLogger(__name__)


class RTTicket(ticket.Ticket):
    """
    A RT Ticket object. Contains RT-specific methods for working with tickets.
    """
    def __init__(self, url, project, auth=None, ticket_id=None):
        self.ticketing_tool = 'RT'

        self.auth = auth

        # RT URLs
        self.url = url
        self.rest_url = '{0}/REST/1.0'.format(self.url)
        self.auth_url = '{0}/index.html'.format(self.rest_url)

        # Call our parent class's init method which creates our requests session.
        super(RTTicket, self).__init__(project, ticket_id)

    def _generate_ticket_url(self):
        """
        Generates the ticket URL out of the url, project, and ticket_id.
        :return: ticket_url: The URL of the ticket.
        """
        ticket_url = None

        # If we are receiving a ticket_id, set ticket_url.
        if self.ticket_id:
            ticket_url = "{0}/Ticket/Display.html?id={1}".format(self.url, self.ticket_id)

        # This method is called from set_ticket_id(), _create_ticket_request(), or Ticket.__init__().
        # If this method is being called, we want to update the url field in our Result namedtuple.
        self.request_result = self.request_result._replace(url=ticket_url)

        return ticket_url

    def _create_requests_session(self):
        """
        Creates a Requests Session and authenticates to base API URL with HTTP Basic Auth or Kerberos Auth.
        We're using a Session to persist cookies across all requests made from the Session instance.
        :return s: Requests Session.
        """
        s = requests.Session()
        # Kerberos Auth
        if self.auth == 'kerberos':
            self.principal = ticket._get_kerberos_principal()
            s.auth = HTTPKerberosAuth(mutual_authentication=DISABLED)
            s.verify = False
        # HTTP Basic Auth
        if isinstance(self.auth, tuple):
            username, password = self.auth
            self.principal = username
            s.params.update({'user': username, 'pass': password})

        # Try to authenticate to auth_url.
        try:
            r = s.get(self.auth_url)
            logger.debug("Create requests session: status code: {0}".format(r.status_code))
            r.raise_for_status()
            # Special case for RT. A 200 status code is still returned if authentication failed. Have to check r.text.
            if '200' not in r.text:
                raise requests.RequestException
            logger.info("Successfully authenticated to {0}".format(self.ticketing_tool))
            return s
        except requests.RequestException as e:
            logger.error("Error authenticating to {0}".format(self.auth_url))
            s.close()

    def _verify_project(self, project):
        """
        Queries the RT API to see if project is a valid project for the given RT instance.
        :param project: The project you're verifying.
        :return: True or False depending on if project is valid.
        """
        try:
            r = self.s.get("{0}/queue/{1}".format(self.rest_url, project))
            logger.debug("Verify project: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Unexpected error occurred when verifying project")
            logger.error(e)
            return False

        # RT's API returns 200 even if the project is not valid. We need to parse the response.
        error_response = "No queue named {0} exists".format(project)
        if error_response in r.text:
            logger.error("Project {0} is not valid".format(project))
            return False
        else:
            logger.debug("Project {0} is valid".format(project))
            return True

    def get_ticket_content(self, ticket_id=None, option='show'):
        """
        Queries the RT API to get the ticket_content using ticket_id.
        :param ticket_id: ticket number, if not set self.ticket_id is used.
        :param option: specifies the type of content with possible values 'show', 'attachments', 'comment' and
                       'history'
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if ticket_id is None:
            ticket_id = self.ticket_id
            if not self.ticket_id:
                error_message = "No ticket ID associated with ticket object. " \
                                "Set ticket ID with set_ticket_id(<ticket_id>)"
                logger.error(error_message)
                return self.request_result._replace(status='Failure', error_message=error_message)
        try:
            r = self.s.get("{0}/ticket/{1}/{2}".format(self.rest_url, ticket_id, option))
            logger.debug("Get ticket content: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            error_message = "Error getting ticket content"
            logger.error(error_message)
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # RT's API returns 200 even if the ticket is not valid. We need to parse the response.
        error_responses = ["Ticket {0} does not exist.".format(ticket_id),
                           "Bad Request"]
        if any(error in r.text for error in error_responses):
            error_message = "Ticket {0} is not valid".format(ticket_id)
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        self.ticket_content = _convert_string(r.text)
        return self.request_result._replace(ticket_content=self.ticket_content)

    def create(self, subject, text, **kwargs):
        """
        Creates a ticket.
        The required parameters for ticket creation are subject and text.
        Keyword arguments are used for other ticket fields.
        :param subject: The ticket subject.
        :param text: The ticket text.
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        error_message = ""
        if subject is None:
            error_message = "subject is a necessary parameter for ticket creation"
        if text is None:
            error_message = "text is a necessary parameter for ticket creation"
        if error_message:
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # Create our parameters used in ticket creation.
        params = self._create_ticket_parameters(subject, text, kwargs)

        # Create our ticket.
        return self._create_ticket_request(params)

    def _create_ticket_parameters(self, subject, text, fields):
        """
        Creates the payload for the POST request when creating a RT ticket.

        The required parameters for ticket creation are subject and description.
        Keyword arguments are used for other ticket fields.

        Fields examples:
        subject='Ticket subject'
        text='Ticket text'
        priority='5'
        owner='username@mail.com'
        cc='username@mail.com'
        admincc=['username@mail.com', 'username2@mail.com']

        :param subject: The ticket subject.
        :param text: The ticket text.
        :param fields: Other ticket fields.
        :return: params: A dict to pass in to the POST request containing ticket details.
        """
        # RT requires a special encoding on the Text parameter.
        encoded_text = text.replace('\n', '\n      ')

        content = 'Queue: {0}\n'.format(self.project)
        content += 'Requestor: {0}\n'.format(self.principal)
        content += 'Subject: {0}\n'.format(subject)
        content += 'Text: {0}\n'.format(encoded_text)

        # Some of the ticket fields need to be in a specific form for the tool.
        fields = _prepare_ticket_fields(fields)

        # Iterate through our options and add them to the params dict.
        for key, value in fields.items():
            content += '{0}: {1}\n'.format(key.title(), value)

        params = {'content': content}

        return params

    def _create_ticket_request(self, params):
        """
        Tries to create the ticket through the ticketing tool's API.
        Retrieves the ticket_id and creates the ticket_url.
        :param params: The payload to send in the POST request.
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        # Attempt to create ticket.
        try:
            r = self.s.post('{0}/ticket/new'.format(self.rest_url), data=params)
            logger.debug("Create ticket: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error creating ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        # RT's API returns 200 even if the ticket is not valid. We need to parse the response.
        if 'Could not create ticket' in r.text:
            error_message = r.text.replace('\n', ' ')
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        # Retrieve key from new ticket.
        ticket_content = r.text
        self.ticket_id = re.search('Ticket (\d+) created', ticket_content).groups()[0]
        self.ticket_url = self._generate_ticket_url()
        logger.info("Created ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result

    def edit(self, **kwargs):
        """
        Edits fields in a RT ticket.
        Keyword arguments are used to specify ticket fields.

        Fields examples:
        priority='5'
        owner='username@mail.com'
        cc='username@mail.com'
        admincc=['username@mail.com', 'username2@mail.com']

        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # Some of the ticket fields need to be in a specific form for the tool.
        fields = _prepare_ticket_fields(kwargs)

        content = ''

        # Iterate through our kwargs and add them to the content string.
        for key, value in fields.items():
            content += '{0}: {1}\n'.format(key.title(), value)

        params = {'content': content}

        # Attempt to edit ticket.
        try:
            r = self.s.post("{0}/ticket/{1}/edit".format(self.rest_url, self.ticket_id), data=params)
            logger.debug("Edit ticket: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error editing ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        # RT's API returns 200 even if the ticket is not valid. We need to parse the response.
        if '409 Syntax Error' in r.text:
            error_message = r.text.replace('\n', ' ')
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        logger.info("Edited ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result

    def add_comment(self, comment):
        """
        Adds a comment to a RT issue.
        :param comment: A string representing the comment to be added.
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # RT requires a special encoding on the comment parameter.
        encoded_comment = comment.replace('\n', '\n      ')

        content = 'Action: correspond\n'
        content += 'Text: {0}\n'.format(encoded_comment)

        params = {'content': content}

        # Attempt to add comment to ticket.
        try:
            r = self.s.post('{0}/ticket/{1}/comment'.format(self.rest_url, self.ticket_id), data=params)
            logger.debug("Add comment: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error adding comment to ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        # RT's API returns 200 even if the ticket is not valid. We need to parse the response.
        if '400 Bad Request' in r.text:
            error_message = r.text.replace('\n', ' ')
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        logger.info("Added comment to ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result

    def change_status(self, status):
        """
        Changes status of a RT ticket.
        :param status: Status to change to.
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        content = 'Status: {0}\n'.format(status.lower())

        params = {'content': content}

        # Attempt to change status of ticket.
        try:
            r = self.s.post('{0}/ticket/{1}/edit'.format(self.rest_url, self.ticket_id), data=params)
            logger.debug("Change status: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error changing status of ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        # RT's API returns 200 even if the ticket is not valid. We need to parse the response.
        if '409 Syntax Error' in r.text:
            error_message = r.text.replace('\n', ' ')
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        logger.info("Changed status of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result

    def add_attachment(self, file_name):
        """
        Attaches a file to a RT ticket.
        :param file_name: A string representing the file to attach.
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        content = 'Action: correspond\n'
        content += 'Attachment: {0}\n'.format(file_name)

        params = {'content': content}
        try:
            files = {'attachment_1': open(file_name, 'rb')}
        except IOError:
            error_message = "File {0} not found".format(file_name)
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # Attempt to attach file.
        try:
            r = self.s.post("{0}/ticket/{1}/comment".format(self.rest_url, self.ticket_id), data=params, files=files)
            logger.debug("Add attachment: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error attaching file {0}".format(file_name))
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        # RT's API returns 200 even if the ticket is not valid. We need to parse the response.
        if '200' not in r.text:
            error_message = r.text.replace('\n', ' ')
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        logger.info("Attached file {0} to ticket {1} - {2}".format(file_name, self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result


def _prepare_ticket_fields(fields):
        """
        Makes sure each key value pair in the fields dictionary is in the correct form.
        :param fields: Ticket fields.
        :return: fields: Ticket fields in the correct form for the ticketing tool.
        """
        for key, value in fields.items():
            if key in ['cc', 'admincc']:
                if isinstance(value, list):
                    fields[key] = ', '.join(value)
        return fields


def _convert_string(text):
    """
    Converts string into more appropriate form for reading and accessing.
    :param text: Text to be converted in a form of string.
    :return: List of strings or a dictionary in dependance of which form is preferable.
    """
    lines = text.split('\n')
    if 'Stack' in text:
        return text.split('\n')
    response = {'header': []}
    for line in lines:
        if line:
            if ':' not in line:
                response['header'].append(line)
            elif ':' in line:
                elements = line.split(':')
                if 'Attachments' in elements[0]:
                    response[elements[1].lstrip()] = elements[2].lstrip()
                else:
                    response[elements[0].lstrip()] = elements[1].lstrip()
    return response


def main():
    """
    main() function, not directly callable.
    :return:
    """
    print("Not directly executable")


if __name__ == "__main__":
    main()

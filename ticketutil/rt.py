import logging
import re

import requests

from . import ticket

__author__ = 'dranck, rnester, kshirsal'


class RTTicket(ticket.Ticket):
    """
    A RT Ticket object. Contains RT-specific methods for working with tickets.
    """
    def __init__(self, url, project, auth=None, ticket_id=None):
        self.ticketing_tool = 'RT'

        # Right now, hardcode auth as 'kerberos', which is the only supported auth for RT.
        self.auth = 'kerberos'

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

        return ticket_url

    def _verify_project(self, project):
        """
        Queries the RT API to see if project is a valid project for the given RT instance.
        :param project: The project you're verifying.
        :return: True or False depending on if project is valid.
        """
        try:
            r = self.s.get("{0}/queue/{1}".format(self.rest_url, project))
            logging.debug("Verify project: Status Code: {0}".format(r.status_code))
            r.raise_for_status()
            error_response = "No queue named {0} exists.".format(project)
            # RT's API returns 200 even if the project is not valid. We need to parse the response.
            if error_response in r.text:
                logging.error("Project {0} is not valid.".format(project))
                return False
            else:
                logging.debug("Project {0} is valid".format(project))
                return True
        except requests.RequestException as e:
            logging.error("Unexpected error occurred when verifying project.")
            logging.error(e.args[0])
            return False

    def _verify_ticket_id(self, ticket_id):
        """
        Queries the RT API to see if ticket_id is a valid ticket for the given RT instance.
        :param ticket_id: The ticket you're verifying.
        :return: True or False depending on if ticket is valid.
        """
        try:
            r = self.s.get("{0}/ticket/{1}/show".format(self.rest_url, ticket_id))
            logging.debug("Verify ticket_id: Status Code: {0}".format(r.status_code))
            r.raise_for_status()
            error_response = "Ticket {0} does not exist.".format(ticket_id)
            # RT's API returns 200 even if the ticket is not valid. We need to parse the response.
            if error_response in r.text:
                logging.error("Ticket {0} is not valid.".format(ticket_id))
                return False
            else:
                logging.debug("Ticket {0} is valid".format(ticket_id))
                return True
        except requests.RequestException as e:
            logging.error("Unexpected error occurred when verifying ticket_id.")
            logging.error(e.args[0])
            return False

    def create(self, subject, text, **kwargs):
        """
        Creates a ticket.
        The required parameters for ticket creation are subject and text.
        Keyword arguments are used for other ticket fields.
        :param subject: The ticket subject.
        :param text: The ticket text.
        :return
        """
        if subject is None:
            logging.error("subject is a necessary parameter for ticket creation.")
            return
        if text is None:
            logging.error("text is a necessary parameter for ticket creation.")
            return

        # Create our parameters used in ticket creation.
        params = self._create_ticket_parameters(subject, text, kwargs)

        # Create our ticket.
        self._create_ticket_request(params)

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
        :return:
        """
        # Attempt to create ticket.
        try:
            r = self.s.post('{0}/ticket/new'.format(self.rest_url), data=params)
            r.raise_for_status()
            logging.debug("Create ticket: Status Code: {0}".format(r.status_code))

            # Retrieve key from new ticket.
            ticket_content = r.text
            self.ticket_id = re.search('Ticket (\d+) created', ticket_content).groups()[0]
            self.ticket_url = self._generate_ticket_url()
            logging.info("Created ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error creating ticket")
            logging.error(e.args[0])

    def edit(self, **kwargs):
        """
        Edits fields in a RT ticket.
        Keyword arguments are used to specify ticket fields.

        Fields examples:
        priority='5'
        owner='username@mail.com'
        cc='username@mail.com'
        admincc=['username@mail.com', 'username2@mail.com']

        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

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
            r.raise_for_status()
            logging.debug("Editing Ticket: Status Code: {0}".format(r.status_code))
            logging.info("Edited ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error editing ticket")
            logging.error(e.args[0])

    def add_comment(self, comment):
        """
        Adds a comment to a RT issue.
        :param comment: A string representing the comment to be added.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        # RT requires a special encoding on the comment parameter.
        encoded_comment = comment.replace('\n', '\n      ')

        content = 'Action: correspond\n'
        content += 'Text: {0}\n'.format(encoded_comment)

        params = {'content': content}

        # Attempt to add comment to ticket.
        try:
            r = self.s.post('{0}/ticket/{1}/comment'.format(self.rest_url, self.ticket_id), data=params)
            r.raise_for_status()
            logging.debug("Add comment: Status Code: {0}".format(r.status_code))
            logging.info("Added comment to ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error adding comment to ticket")
            logging.error(e.args[0])

    def change_status(self, status):
        """
        Changes status of a RT ticket.
        :param status: Status to change to.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        content = 'Status: {0}\n'.format(status.lower())

        params = {'content': content}

        # Attempt to change status of ticket.
        try:
            r = self.s.post('{0}/ticket/{1}/edit'.format(self.rest_url, self.ticket_id), data=params)
            r.raise_for_status()
            logging.debug("Changing status of ticket: Status Code: {0}".format(r.status_code))
            logging.info("Changed status of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error changing status of ticket")
            logging.error(e.args[0])

    def add_attachment(self, file_name):
        """
        Attaches a file to a RT ticket.
        :param file_name: A string representing the file to attach.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        content = 'Action: correspond\n'
        content += 'Attachment: {0}\n'.format(file_name)

        params = {'content': content}
        files = {'attachment_1': open(file_name, 'rb')}

        # Attempt to attach file.
        try:
            r = self.s.post("{0}/ticket/{1}/comment".format(self.rest_url, self.ticket_id), data=params, files=files)
            r.raise_for_status()
            logging.debug("Add attachment: Status Code: {0}".format(r.status_code))
            logging.info("Attached File {0}: {1} - {2}".format(file_name, self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error attaching file {0}".format(file_name))
            logging.error(e.args[0])
        except IOError:
            logging.error("{0} not found".format(file_name))


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


def main():
    """
    main() function, not directly callable.
    :return:
    """
    print("Not directly executable")


if __name__ == "__main__":
    main()

import logging
import os

import requests

from . import ticket

__author__ = 'dranck, rnester, kshirsal'

# Disable warnings for requests because we aren't doing certificate verification
requests.packages.urllib3.disable_warnings()

DEBUG = os.environ.get('TICKETUTIL_DEBUG', 'False')

if DEBUG == 'True':
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


class BugzillaTicket(ticket.Ticket):
    """
    A BZ Ticket object. Contains BZ-specific methods for working with tickets.
    """
    def __init__(self, url, project, auth=None, ticket_id=None):
        self.ticketing_tool = 'Bugzilla'

        # Kerberos is default auth if the auth param is not specified.
        # A tuple of the form (<username>, <password>) can also be passed in.
        if isinstance(auth, tuple):
            self.auth = auth
            username, password = auth
            self.credentials = {"login": username, "password": password}
        else:
            self.auth = 'kerberos'
        self.token = None

        # BZ URLs
        self.url = url
        self.rest_url = '{0}/rest/bug'.format(self.url)
        self.auth_url = '{0}/rest/login'.format(self.url)

        # Call our parent class's init method which creates our requests session.
        super(BugzillaTicket, self).__init__(project, ticket_id)

    def _generate_ticket_url(self):
        """
        Generates the ticket URL out of the url, project, and ticket_id.
        :return: ticket_url: The URL of the ticket.
        """
        ticket_url = None

        # If we are receiving a ticket_id, set ticket_url.
        if self.ticket_id:
            ticket_url = "{0}/show_bug.cgi?id={1}".format(self.url, self.ticket_id)

        return ticket_url

    def _create_requests_session(self):
        """
        Returns to the super class if the authentication method is kerberos.
        Creates a Requests Session and authenticates to base API URL with authentication other then kerberos.
        We're using a Session to persist cookies across all requests made from the Session instance.
        :return s: Requests Session.
        """
        if self.auth == 'kerberos':
            return super(BugzillaTicket, self)._create_requests_session()

        # If basic authentication is passed in, generate a token to be used in all requests.
        try:
            s = requests.Session()
            r = s.get(self.auth_url, params=self.credentials, verify=False)
            r.raise_for_status()
            resp = r.json()
            self.token = resp['token']
            logging.debug("Create requests session: Status Code: {0}".format(r.status_code))
            logging.info("Successfully authenticated to {0}.".format(self.ticketing_tool))
            return s

        # We log an error if authentication was not successful, because rest of the HTTP requests will not succeed.
        # If authentication wasn't successful, a token will not be in resp. Add KeyError as exception.
        except (KeyError, requests.RequestException) as e:
            logging.error("Error authenticating to {0}. No valid credentials were provided.".format(self.auth_url))
            logging.error(e.args[0])

    def create(self, summary, description, **kwargs):
        """
        Creates a ticket.
        The required parameters for ticket creation are summary and description.
        Keyword arguments are used for other ticket fields.
        :param summary: The ticket summary.
        :param description: The ticket description.
        :return
        """
        if summary is None:
            logging.error("summary is a necessary parameter for ticket creation.")
            return
        if description is None:
            logging.error("description is a necessary parameter for ticket creation.")
            return

        # Create our parameters used in ticket creation.
        params = self._create_ticket_parameters(summary, description, kwargs)

        # Create our ticket.
        self._create_ticket_request(params)

    def _create_ticket_parameters(self, summary, description, fields):
        """
        Creates the payload for the POST request when creating a Bugzilla ticket.

        The required parameters for ticket creation are summary and description.
        Keyword arguments are used for other ticket fields.

        Fields examples:
        summary='Ticket summary'
        description='Ticket description'
        assignee='username@mail.com'
        qa_contact='username@mail.com'
        component='Test component'
        version='version'
        priority='high'
        severity='medium'
        alias='SomeAlias'

        :param summary: The ticket summary.
        :param description: The ticket description.
        :param fields: Other ticket fields.
        :return: params: A dictionary to pass in to the POST request containing ticket details.
        """
        # Create our parameters for creating the ticket.
        params = {"product": str(self.project),
                  "summary": summary,
                  "description": description}

        # Some of the ticket fields need to be in a specific form for the tool.
        fields = _prepare_ticket_fields(fields)

        # Update params dict with items from fields dict.
        params.update(fields)
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
            if self.token:
                params['token'] = self.token

            r = self.s.post(self.rest_url, json=params)
            r.raise_for_status()
            logging.debug("Create ticket: Status Code: {0}".format(r.status_code))

            # Try to grab the newly created ticket id from the request response.
            # If there's a KeyError, grab the error message from the request response.
            if 'id' in r.json():
                self.ticket_id = r.json()['id']
            elif 'message' in r.json():
                logging.error("Create ticket error message: {0}".format(r.json()['message']))
                return
            else:
                logging.error("Error creating ticket")
                return
            self.ticket_url = self._generate_ticket_url()
            logging.info("Created ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error creating ticket")
            logging.error(e.args[0])

    def edit(self, **kwargs):
        """
        Edits fields in a Bugzilla ticket.
        Keyword arguments are used to specify ticket fields.

        Fields examples:
        summary='Ticket summary'
        assignee='username@mail.com'
        qa_contact='username@mail.com'
        component='Test component'
        version='version'
        priority='high'
        severity='medium'
        alias='SomeAlias'

        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        # Some of the ticket fields need to be in a specific form for the tool.
        kwargs = _prepare_ticket_fields(kwargs)

        params = kwargs
        if self.token:
            params['token'] = self.token

        # Attempt to edit ticket.
        try:
            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            if 'bugs' in r.json():
                if r.json()['bugs'][0]['changes'] == {}:
                    logging.error("No changes made to ticket. Possible invalid field or lack of change in field.")
                    return
            if 'message' in r.json():
                logging.error(r.json()['message'])
                return
            logging.debug("Editing Ticket: Status Code: {0}".format(r.status_code))
            logging.info("Edited ticket with the mentioned fields {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error editing ticket")
            logging.error(e.args[0])

    def add_comment(self, comment):
        """
        Adds a comment to a Bugzilla ticket.
        :param comment: A string representing the comment to be added.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        params = {'comment': comment}

        # Attempt to add comment to ticket.
        try:
            if self.token:
                params['token'] = self.token
            r = self.s.post("{0}/{1}/comment".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Add comment: Status Code: {0}".format(r.status_code))
            logging.info("Added comment to ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error adding comment to ticket")
            logging.error(e.args[0])

    def change_status(self, status, **kwargs):
        """
        Changes status of a Bugzilla ticket.
        Some status changes require a secondary field (i.e. resolution). Specify this as a kwarg.
        A resolution of Duplicate requires dupe_of kwarg with a valid bug ID.
        :param status: Status to change to.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        params = {"status": status}
        params.update(kwargs)

        # Attempt to change status of ticket.
        try:
            if self.token:
                params['token'] = self.token

            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            if 'message' in r.json():
                logging.error("Change status error message: {0}".format(r.json()['message']))
                return
            logging.debug("Changing status of ticket: Status Code: {0}".format(r.status_code))
            logging.info("Changed status of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error changing status of ticket")
            logging.error(e.args[0])

    def add_cc(self, user):
        """
        Adds user(s) to cc list.
        :param user: A string representing one user's email address, or a list of strings for multiple users.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        if isinstance(user, list):
            params = {'cc': {'add': user}}
        else:
            params = {'cc': {'add': [user]}}

        if self.token:
            params['token'] = self.token

        # Attempt to edit ticket.
        try:
            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            if 'bugs' in r.json():
                if r.json()['bugs'][0]['changes'] == {}:
                    logging.error("No changes made to ticket. Possible invalid field or lack of change in field.")
                    return
            if 'message' in r.json():
                logging.error(r.json()['message'])
                return
            logging.debug("Adding user(s) to cc list: Status Code: {0}".format(r.status_code))
            logging.info("Adding user(s) to cc list {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error adding user(s) to cc list")
            logging.error(e.args[0])

    def remove_cc(self, user):
        """
        Removes user(s) from cc list.
        :param user: A string representing one user's email address, or a list of strings for multiple users.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        if isinstance(user, list):
            params = {'cc': {'remove': user}}
        else:
            params = {'cc': {'remove': [user]}}

        if self.token:
            params['token'] = self.token

        # Attempt to edit ticket.
        try:
            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            if 'bugs' in r.json():
                if r.json()['bugs'][0]['changes'] == {}:
                    logging.error("No changes made to ticket. Possible invalid field or lack of change in field.")
                    return
            if 'message' in r.json():
                logging.error(r.json()['message'])
                return
            logging.debug("Removing user(s) from cc list: Status Code: {0}".format(r.status_code))
            logging.info("Removing user(s) from cc list {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error removing user(s) from cc list")
            logging.error(e.args[0])


def _prepare_ticket_fields(fields):
    """
    Makes sure each key value pair in the fields dictionary is in the correct form.
    :param fields: Ticket fields.
    :return: fields: Ticket fields in the correct form for the ticketing tool.
    """
    for key, value in fields.items():
        if key == 'assignee':
            fields['assigned_to'] = value
            fields.pop('assignee')
    return fields


def main():
    """
    main() function, not directly callable.
    :return:
    """
    print("Not directly executable")


if __name__ == "__main__":
    main()

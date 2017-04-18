import base64
import logging
import mimetypes

import requests

from . import ticket

__author__ = 'dranck, rnester, kshirsal'


class BugzillaTicket(ticket.Ticket):
    """
    A BZ Ticket object. Contains BZ-specific methods for working with tickets.
    """
    def __init__(self, url, project, auth=None, ticket_id=None):
        self.ticketing_tool = 'Bugzilla'

        self.auth = auth
        self.credentials = None

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
        # Kerberos Auth
        if self.auth == 'kerberos':
            return super(BugzillaTicket, self)._create_requests_session()

        # Run the rest of this method for both HTTP Basic Auth and APIKey Auth

        # HTTP Basic Auth
        if isinstance(self.auth, tuple):
            username, password = self.auth
            self.credentials = {"login": username, "password": password}
        # API Key Auth
        elif 'api_key' in self.auth:
            self.credentials = self.auth

        s = requests.Session()
        s.params.update(self.credentials)
        s.verify = False

        # Try to authenticate to auth_url.
        try:
            r = s.get(self.auth_url)
            r.raise_for_status()
            logging.debug("Create requests session: Status Code: {0}".format(r.status_code))
            logging.info("Successfully authenticated to {0}.".format(self.ticketing_tool))
            return s
        # We log an error if authentication was not successful, because rest of the HTTP requests will not succeed.
        # If authentication wasn't successful, a token will not be in resp. Add KeyError as exception.
        except (KeyError, requests.RequestException) as e:
            logging.error("Error authenticating to {0}.".format(self.auth_url))
            logging.error(e.args[0])
            s.close()

    def _verify_project(self, project):
        """
        Queries the Bugzilla API to see if project is a valid project for the given Bugzilla instance.
        :param project: The project you're verifying.
        :return: True or False depending on if project is valid.
        """
        try:
            r = self.s.get("{0}/rest/product/{1}".format(self.url, project.replace(" ", "%20")))
            logging.debug("Verify project: Status Code: {0}".format(r.status_code))
            r.raise_for_status()
            # Bugzilla's API returns 200 even if the project is not valid. We need to parse the response.
            if r.json() == {"products": []}:
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
        Queries the Bugzilla API to see if ticket_id is a valid ticket for the given Bugzilla instance.
        :param ticket_id: The ticket you're verifying.
        :return: True or False depending on if ticket is valid.
        """
        try:
            r = self.s.get("{0}/{1}".format(self.rest_url, ticket_id))
            logging.debug("Verify ticket_id: Status Code: {0}".format(r.status_code))
            r.raise_for_status()
            error_responses = ["Bug #{0} does not exist.".format(ticket_id),
                               "\\\"{0}\\\" is out of range for type integer".format(ticket_id),
                               "\'{0}\' is not a valid bug number nor an alias to a bug.".format(ticket_id)]
            # Bugzilla's API returns 200 even if the ticket is not valid. We need to parse the response.
            if any(error in r.text for error in error_responses):
                logging.error("Ticket {0} is not valid.".format(ticket_id))
                return False
            else:
                logging.debug("Ticket {0} is valid".format(ticket_id))
                return True
        except requests.RequestException as e:
            logging.error("Unexpected error occurred when verifying ticket_id.")
            logging.error(e.args[0])
            return False

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
        ticket_id = self.ticket_id
        return ticket_id

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
        fields = _prepare_ticket_fields("create", fields)

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
        kwargs = _prepare_ticket_fields("edit", kwargs)
        params = kwargs

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

    def add_comment(self, comment, **kwargs):
        """
        Adds a comment to a Bugzilla ticket.
        :param comment: A string representing the comment to be added.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        params = {"comment": comment}
        params.update(kwargs)

        # Attempt to add comment to ticket.
        try:
            r = self.s.post("{0}/{1}/comment".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Add comment: Status Code: {0}".format(r.status_code))
            logging.info("Added comment to ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error adding comment to ticket")
            logging.error(e.args[0])

    def add_attachment(self, file_name, data, summary, **kwargs):
        """
        :param file_name: The "file name" that will be displayed in the UI for this attachment.
        :param data: The content of the attachment which is base64 encoded.
        :param summary: A short string describing the attachment.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        # Read the contents from the file path, guess the mimetypes and update the params.
        f = open(data, "rb")
        file_content = f.read()
        content_type = mimetypes.guess_type(data)[0]
        if not content_type:
            content_type = 'application/octet-stream'
        file_content = base64.standard_b64encode(file_content).decode()
        params = {"file_name": file_name,
                  "data": file_content,
                  "summary": summary,
                  "is_patch": False,
                  "content_type": content_type}
        params.update(kwargs)

        # Attempt to change status of ticket.
        try:
            headers = {"Content-Type": "application/json"}
            r = self.s.post("{0}/{1}/attachment".format(self.rest_url, self.ticket_id), json=params, headers=headers)
            r.raise_for_status()
            if 'message' in r.json():
                logging.error("Add attachment: {0}".format(r.json()['message']))
                return
            logging.debug("Adding attachment to ticket: Status Code: {0}".format(r.status_code))
            logging.info("Added a new attachment to: {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error adding attachment to ticket")
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


def _prepare_ticket_fields(operation, fields):
    """
    Makes sure each key value pair in the fields dictionary is in the correct form.
    :param fields: Ticket fields.
    :return: fields: Ticket fields in the correct form for the ticketing tool.
    """
    if "edit" in operation:
        if "groups" in fields:
            if not isinstance(fields["groups"], list):
                fields["groups"] = [fields["groups"]]
        fields["groups"] = {"add": fields["groups"]}

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

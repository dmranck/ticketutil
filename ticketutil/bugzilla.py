import base64
import logging
import mimetypes

import requests

from . import ticket

__author__ = 'dranck, rnester, kshirsal'

logger = logging.getLogger(__name__)


class BugzillaTicket(ticket.Ticket):
    """
    A BZ Ticket object. Contains BZ-specific methods for working with tickets.
    """
    def __init__(self, url, project, auth='kerberos', ticket_id=None):
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

        # This method is called from set_ticket_id(), _create_ticket_request(), or Ticket.__init__().
        # If this method is being called, we want to update the url field in our Result namedtuple.
        self.request_result = self.request_result._replace(url=ticket_url)

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
            logger.debug("Create requests session: status code: {0}".format(r.status_code))
            r.raise_for_status()
        # We log an error if authentication was not successful, because rest of the HTTP requests will not succeed.
        except requests.RequestException as e:
            logger.error("Error authenticating to {0}".format(self.auth_url))
            logger.error(e)
            s.close()
            return

        # Bugzilla's API returns 200 even if the request was not valid. We need to parse the response.
        if "error" in r.json():
            logger.error("Error authenticating to {0}".format(self.auth_url))
            logger.error(r.json()["message"])
            return
        logger.info("Successfully authenticated to {0}".format(self.ticketing_tool))
        return s

    def _verify_project(self, project):
        """
        Queries the Bugzilla API to see if project is a valid project for the given Bugzilla instance.
        :param project: The project you're verifying.
        :return: True or False depending on if project is valid.
        """
        try:
            r = self.s.get("{0}/rest/product/{1}".format(self.url, project.replace(" ", "%20")))
            logger.debug("Verify project: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Unexpected error occurred when verifying project")
            logger.error(e)
            return False

        # Bugzilla's API returns 200 even if the request response is not valid. We need to parse r.text.
        if r.json() == {"products": []}:
            logger.error("Project {0} is not valid".format(project))
            return False
        else:
            logger.debug("Project {0} is valid".format(project))
            return True

    def get_ticket_content(self, ticket_id=None):
        """
        Queries the Bugzilla API to get ticket_content using ticket_id.
        :param ticket_id: ticket number, if not set self.ticket_id is used.
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
            r = self.s.get("{0}/{1}".format(self.rest_url, ticket_id))
            logger.debug("Get ticket content: status code: {0}".format(r.status_code))
            r.raise_for_status()
            self.ticket_content = r.json()
            return self.request_result._replace(ticket_content=self.ticket_content)
        except requests.RequestException as e:
            error_message = "Error getting ticket content"
            logger.error(error_message)
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=error_message)

    def create(self, summary, description, component, version, **kwargs):
        """
        Creates a ticket.
        The required parameters for ticket creation are summary, description, component and version.
        Keyword arguments are used for other ticket fields.
        :param summary: The ticket summary.
        :param description: The ticket description.
        :param component: The ticket component.
        :param version: The ticket version.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        error_message = ""
        required_args = {summary: 'summary', description: 'description', component: 'component', version: 'version'}
        for arg in required_args:
            if arg is None:
                error_message = '{} is a necessary parameter for ticket creation'.format(required_args[arg])
        if error_message:
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # Create our parameters used in ticket creation.
        params = self._create_ticket_parameters(summary, description, component, version, kwargs)

        # Create our ticket.
        return self._create_ticket_request(params)

    def _create_ticket_parameters(self, summary, description, component, version, fields):
        """
        Creates the payload for the POST request when creating a Bugzilla ticket.

        The required parameters for ticket creation are summary, description, component and version.
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
        :param component: The ticket component.
        :param version: The ticket version.
        :param fields: Other ticket fields.
        :return: params: A dictionary to pass in to the POST request containing ticket details.
        """
        # Create our parameters for creating the ticket.
        params = {"product": str(self.project),
                  "summary": summary,
                  "description": description,
                  "component": component,
                  "version": version}

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
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        # Attempt to create ticket.
        try:
            r = self.s.post(self.rest_url, json=params)
            logger.debug("Create ticket: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error creating ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        # Bugzilla's API returns 200 even if the request response is not valid. We need to parse r.text.
        if 'id' in r.json():
            self.ticket_id = r.json()['id']
        elif "error" in r.json():
            error_message = r.json()['message']
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        else:
            error_message = "Error creating ticket"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        self.ticket_url = self._generate_ticket_url()
        logger.info("Created ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result

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

        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # Some of the ticket fields need to be in a specific form for the tool.
        params = _prepare_ticket_fields("edit", kwargs)

        # Attempt to edit ticket.
        try:
            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            logger.debug("Edit ticket: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error editing ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        # Bugzilla's API returns 200 even if the request response is not valid. We need to parse r.text.
        if 'bugs' in r.json():
            if r.json()['bugs'][0]['changes'] == {}:
                error_message = "No changes made to ticket. Possible invalid field or lack of change in field"
                logger.info(error_message)
                return self.request_result
        if 'error' in r.json():
            error_message = r.json()['message']
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        logger.info("Edited ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result

    def add_comment(self, comment, **kwargs):
        """
        Adds a comment to a Bugzilla ticket.
        :param comment: A string representing the comment to be added.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        params = {"comment": comment}
        params.update(kwargs)

        # Attempt to add comment to ticket.
        try:
            r = self.s.post("{0}/{1}/comment".format(self.rest_url, self.ticket_id), json=params)
            logger.debug("Add comment: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error adding comment to ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        # Bugzilla's API returns 200 even if the request response is not valid. We need to parse r.text.
        if 'error' in r.json():
            error_message = r.json()['message']
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        logger.info("Added comment to ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result

    def add_attachment(self, file_name, data, summary, **kwargs):
        """
        :param file_name: The "file name" that will be displayed in the UI for this attachment.
        :param data: A string representing the file to attach.
        :param summary: A short string describing the attachment.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # Read the contents from the file path, guess the mimetypes and update the params.
        try:
            f = open(data, "rb")
        except IOError:
            error_message = "File {0} not found".format(file_name)
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        file_content = f.read()
        f.close()
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
            logger.debug("Add attachment: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error adding attachment to ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        # Bugzilla's API returns 200 even if the request response is not valid. We need to parse r.text.
        if 'error' in r.json():
            error_message = r.json()['message']
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        logger.info("Attached file {0} to ticket {1} - {2}".format(file_name, self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result

    def change_status(self, status, **kwargs):
        """
        Changes status of a Bugzilla ticket.
        Some status changes require a secondary field (i.e. resolution). Specify this as a kwarg.
        A resolution of Duplicate requires dupe_of kwarg with a valid bug ID.
        :param status: Status to change to.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        params = {"status": status}
        params.update(kwargs)

        # Attempt to change status of ticket.
        try:
            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            logger.debug("Change status: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error changing status of ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        if 'error' in r.json():
            error_message = r.json()['message']
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        logger.info("Changed status of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result

    def add_cc(self, user):
        """
        Adds user(s) to cc list.
        :param user: A string representing one user's email address, or a list of strings for multiple users.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        if isinstance(user, list):
            params = {'cc': {'add': user}}
        else:
            params = {'cc': {'add': [user]}}

        # Attempt to edit ticket.
        try:
            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            logger.debug("Add cc: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error adding user(s) to cc list")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        if 'bugs' in r.json():
            if r.json()['bugs'][0]['changes'] == {}:
                error_message = "No changes made to ticket. Possible invalid field or lack of change in field"
                logger.info(error_message)
                return self.request_result
        if 'error' in r.json():
            error_message = r.json()['message']
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        logger.info("Added user(s) to cc list of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result

    def remove_cc(self, user):
        """
        Removes user(s) from cc list.
        :param user: A string representing one user's email address, or a list of strings for multiple users.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        if isinstance(user, list):
            params = {'cc': {'remove': user}}
        else:
            params = {'cc': {'remove': [user]}}

        # Attempt to edit ticket.
        try:
            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            logger.debug("Remove cc: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error removing user(s) from cc list")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        if 'bugs' in r.json():
            if r.json()['bugs'][0]['changes'] == {}:
                error_message = "No changes made to ticket. Possible invalid field or lack of change in field"
                logger.info(error_message)
                return self.request_result
        if 'error' in r.json():
            error_message = r.json()['message']
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)
        logger.info("Removed user(s) from cc list of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        self.request_result = self.get_ticket_content()
        return self.request_result


def _prepare_ticket_fields(operation, fields):
    """
    Makes sure each key value pair in the fields dictionary is in the correct form.
    :param operation: Key for identification of operation type.
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

import logging

import requests

from . import ticket

__author__ = 'dranck, rnester, kshirsal'

logger = logging.getLogger(__name__)


class RedmineTicket(ticket.Ticket):
    """
    A Redmine Ticket object. Contains Redmine-specific methods for working with tickets.
    """
    def __init__(self, url, project, auth=None, ticket_id=None):
        self.ticketing_tool = 'Redmine'

        # The auth param should be of the form (<username>, <password>) for HTTP Basic authentication.
        self.auth = auth

        # Redmine URLs
        self.url = url
        self.rest_url = '{0}/issues'.format(self.url)
        self.auth_url = '{0}/login'.format(self.url)

        # Call our parent class's init method which creates our requests session.
        super(RedmineTicket, self).__init__(project, ticket_id)

        # For Redmine tickets, specify headers.
        self.s.headers.update({'Content-Type': 'application/json'})

    def _generate_ticket_url(self):
        """
        Generates the ticket URL out of the rest_url and ticket_id.
        :return: ticket_url: The URL of the ticket.
        """
        ticket_url = None

        # If we are receiving a ticket_id, set ticket_url.
        if self.ticket_id:
            ticket_url = "{0}/{1}".format(self.rest_url, self.ticket_id)

        # This method is called from set_ticket_id(), _create_ticket_request(), or Ticket.__init__().
        # If this method is being called, we want to update the url field in our Result namedtuple.
        self.request_result = self.request_result._replace(url=ticket_url)

        return ticket_url

    def _verify_project(self, project):
        """
        Queries the Redmine API to see if project is a valid project for the given Redmine instance.
        :param project: The project you're verifying.
        :return: True or False depending on if project is valid.
        """
        try:
            r = self.s.get("{0}/projects/{1}.json".format(self.url, project))
            logger.debug("Verify project: status code: {0}".format(r.status_code))
            r.raise_for_status()
            logger.debug("Project {0} is valid".format(project))
            return True
        except requests.RequestException as e:
            logger.error("Project {0} is not valid".format(project))
            return False

    def get_ticket_content(self, ticket_id=None):
        """
        Queries the Redmine API to get the ticket_content using ticket_id.
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
            r = self.s.get("{0}/{1}.json?include=attachments,journals,watchers,children,relations,changesets"
                           "".format(self.rest_url, ticket_id))
            logger.debug("Get ticket content: status code: {0}".format(r.status_code))
            r.raise_for_status()
            self.ticket_content = r.json()
            return self.request_result._replace(ticket_content=self.ticket_content)
        except requests.RequestException as e:
            error_message = "Error getting ticket content"
            logger.error(error_message)
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=error_message)

    def create(self, subject, description, **kwargs):
        """
        Creates a ticket.
        The required parameters for ticket creation are subject and description.
        Keyword arguments are used for other ticket fields.
        :param subject: The ticket subject.
        :param description: The ticket description.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        error_message = ""
        if subject is None:
            error_message = "subject is a necessary parameter for ticket creation"
        if description is None:
            error_message = "description is a necessary parameter for ticket creation"
        if error_message:
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # Create our parameters used in ticket creation.
        params = self._create_ticket_parameters(subject, description, kwargs)

        # Create our ticket.
        return self._create_ticket_request(params)

    def _create_ticket_parameters(self, subject, description, fields):
        """
        Creates the payload for the POST request when creating a Redmine ticket.

        The required parameters for ticket creation are subject and description.
        Keyword arguments are used for other ticket fields.

        Fields examples:
        subject='Ticket subject'
        description='Ticket description'
        priority='Urgent'
        start_date='2017-01-20'
        due_date='2017-01-25'
        done_ratio='70'
        assignee='username@mail.com'

        :param subject: The ticket subject.
        :param description: The ticket description.
        :param fields: Other ticket fields.
        :return: params: A dictionary to pass in to the POST request containing ticket details.
        """
        # Create our parameters for creating the ticket.
        params = {'issue': {'project_id': self._get_project_id(),
                            'subject': subject,
                            'description': description}}

        # Some of the ticket fields need to be in a specific form for the tool.
        fields = self._prepare_ticket_fields(fields)

        # Update params dict with items from fields dict.
        params['issue'].update(fields)
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
            r = self.s.post("{0}.json".format(self.rest_url), json=params)
            logger.debug("Create ticket: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error creating ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        # Retrieve key from new ticket.
        ticket_content = r.json()
        self.ticket_id = ticket_content['issue']['id']
        self.ticket_url = self._generate_ticket_url()
        self.request_result = self.get_ticket_content()
        logger.info("Created ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        return self.request_result

    def edit(self, **kwargs):
        """
        Edits fields in a Redmine ticket.
        Keyword arguments are used to specify ticket fields.

        Fields examples:
        subject='Ticket subject'
        description='Ticket description'
        priority='Urgent'
        start_date='2017-01-20'
        due_date='2017-01-25'
        done_ratio='70'
        assignee='username@mail.com'

        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # Some of the ticket fields need to be in a specific form for the tool.
        fields = self._prepare_ticket_fields(kwargs)

        params = {'issue': fields}

        # Attempt to edit ticket.
        try:
            r = self.s.put("{0}/{1}.json".format(self.rest_url, self.ticket_id), json=params)
            logger.debug("Edit ticket: status code: {0}".format(r.status_code))
            r.raise_for_status()
            logger.info("Edited ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            self.request_result = self.get_ticket_content()
            return self.request_result
        except requests.RequestException as e:
            logger.error("Error editing ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

    def add_comment(self, comment):
        """
        Adds a comment to a Redmine ticket.
        :param comment: A string representing the comment to be added.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        params = {'issue': {}}
        params['issue']['notes'] = comment

        # Attempt to add comment to ticket.
        try:
            r = self.s.put('{0}/{1}.json'.format(self.rest_url, self.ticket_id), json=params)
            logger.debug("Add comment: status code: {0}".format(r.status_code))
            r.raise_for_status()
            logger.info("Added comment to ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            self.request_result = self.get_ticket_content()
            return self.request_result
        except requests.RequestException as e:
            logger.error("Error adding comment to ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

    def change_status(self, status):
        """
        Changes status of a Redmine ticket.
        :param status: Status to change to.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        status_id = self._get_status_id(status)
        if not status_id:
            error_message = "Not a valid status: {0}".format(status)
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        params = {'issue': {}}
        params['issue']['status_id'] = status_id

        # Attempt to change status of ticket.
        try:
            r = self.s.put('{0}/{1}.json'.format(self.rest_url, self.ticket_id), json=params)
            logger.debug("Change status: status code: {0}".format(r.status_code))
            r.raise_for_status()
            logger.info("Changed status of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            self.request_result = self.get_ticket_content()
            return self.request_result
        except requests.RequestException as e:
            logger.error("Error changing status of ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

    def remove_watcher(self, watcher):
        """
        Removes watcher from a Redmine ticket.
        Accepts an email or username.
        :param watcher: Username or email of watcher to remove.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # If an email address was passed in for watcher param, extract the 'name' piece.
        if '@' in watcher:
            watcher = "{0}".format(watcher.split('@')[0].strip())

        watcher_id = self._get_user_id(watcher)

        try:
            r = self.s.delete("{0}/{1}/watchers/{2}.json".format(self.rest_url, self.ticket_id, watcher_id))
            logger.debug("Remove watcher {0}: status code: {1}".format(watcher, r.status_code))
            r.raise_for_status()
            logger.info("Removed watcher {0} from ticket {1} - {2}".format(watcher, self.ticket_id, self.ticket_url))
            self.request_result = self.get_ticket_content()
            return self.request_result
        except requests.RequestException as e:
            logger.error("Error removing watcher {0} from ticket".format(watcher))
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

    def add_watcher(self, watcher):
        """
        Adds watcher to a Redmine ticket.
        Accepts an email or username.
        :param watcher: Username or email of watcher to remove.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # If an email address was passed in for watcher param, extract the 'name' piece.
        if '@' in watcher:
            watcher = "{0}".format(watcher.split('@')[0].strip())

        watcher_id = self._get_user_id(watcher)

        if watcher_id:
            params = {'user_id': watcher_id}
            try:
                r = self.s.post("{0}/{1}/watchers.json".format(self.rest_url, self.ticket_id), json=params)
                logger.debug("Add watcher {0}: status code: {1}".format(watcher, r.status_code))
                r.raise_for_status()
                logger.info("Added watcher {0} to ticket {1} - {2}".format(watcher, self.ticket_id, self.ticket_url))
                self.request_result = self.get_ticket_content()
                return self.request_result
            except requests.RequestException as e:
                logger.error("Error adding {0} as a watcher to ticket".format(watcher))
                logger.error(e)
                return self.request_result._replace(status='Failure', error_message=str(e))
        else:
            error_message = "Error adding {0} as a watcher to ticket".format(watcher)
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

    def add_attachment(self, file_name):
        """
        Attaches a file to a Redmine ticket.
        :param file_name: A string representing the file to attach.
        :return: self.request_result: Named tuple containing request status, error_message, url info and
                 ticket_content.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        # First, upload the file to Redmine and retrieve a token to be used in subsequent request.
        token = self._upload_file(file_name)

        if token:
            params = {'issue': {}}
            params['issue']['uploads'] = [{'token': token, 'filename': file_name}]

            try:
                r = self.s.put('{0}/{1}.json'.format(self.rest_url, self.ticket_id), json=params)
                logger.debug("Add attachment: status code: {0}".format(r.status_code))
                r.raise_for_status()
                logger.info("Attached file {0} to ticket {1} - {2}".format(file_name, self.ticket_id, self.ticket_url))
                self.request_result = self.get_ticket_content()
                return self.request_result
            except requests.RequestException as e:
                logger.error("Error attaching file {0}".format(file_name))
                logger.error(e)
                return self.request_result._replace(status='Failure', error_message=str(e))
        else:
            error_message = "Error attaching file {0}".format(file_name)
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

    def _upload_file(self, file_name):
        """
        Uploads a file to /uploads.json.
        :param file_name: A string representing the file to upload.
        :return: token: A token to be used in the request to add attachment.
        """
        headers = {'Content-Type': 'application/octet-stream'}

        # Upload file to uploads.json and retrieve token to be used in the add_attachment() request.
        try:
            params = open(file_name, 'rb')
            r = self.s.post("{0}/uploads.json".format(self.url),
                            data=params,
                            headers=headers)
            logger.debug("Upload attachment: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error uploading file {0}".format(file_name))
            logger.error(e)
            return
        except IOError:
            logger.error("{0} not found".format(file_name))
            return

        token = r.json()['upload']['token']
        logger.info("Uploaded file {0} to Redmine".format(file_name))
        return token

    def _get_project_id(self):
        """
        Get project id from project name.
        Project name is used as the parameter when creating the Ticket object,
        but the Project ID is needed when creating the ticket.
        :return: project_id: The id of the project.
        """
        try:
            r = self.s.get('{0}/projects/{1}.json'.format(self.url, self.project))
            logger.debug("Get project id: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error retrieving Project ID")
            logger.error(e)
            return

        project_json = r.json()
        project_id = project_json['project']['id']
        logger.debug("Retrieved Project ID: {0}".format(project_id))
        return project_id

    def _get_status_id(self, status_name):
        """
        Gets status id corresponding to status name using issue_statuses.json.

        :param status_name: The name of the status.
        :return: status_id: The id of the status.
        """
        try:
            r = self.s.get('{0}/issue_statuses.json'.format(self.url))
            logger.debug("Get status id: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error retrieving Redmine status information")
            logger.error(e)
            return

        status_json = r.json()
        for status in status_json['issue_statuses']:
            if status['name'] == status_name:
                return status['id']

    def _get_priority_id(self, priority_name):
        """
        Gets priority id corresponding to priority name using issue_priorities.json.

        :param priority_name: The name of the priority.
        :return: priority_id: The id of the priority.
        """
        try:
            r = self.s.get('{0}/enumerations/issue_priorities.json'.format(self.url))
            logger.debug("Get priority id: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error retrieving Redmine priority information")
            logger.error(e)
            return

        priority_json = r.json()
        for priority in priority_json['issue_priorities']:
            if priority['name'] == priority_name:
                return priority['id']

    def _get_user_id(self, user_name):
        """
        Gets user id corresponding to user name using users.json.

        :param user_name: The name of the user.
        :return: user_id: The id of the user.
        """
        try:
            r = self.s.get('{0}/users.json'.format(self.url))
            logger.debug("Get user id: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error retrieving Redmine user information")
            logger.error(e)
            return

        # If an email address was passed in for user_name param, extract the 'name' piece.
        if '@' in user_name:
            user_name = "{0}".format(user_name.split('@')[0].strip())

        user_json = r.json()
        for user in user_json['users']:
            if user['login'] == user_name:
                return user['id']

    def _prepare_ticket_fields(self, fields):
        """
        Makes sure each key value pair in the fields dictionary is in the correct form.
        :param fields: Ticket fields.
        :return: fields: Ticket fields in the correct form for the ticketing tool.
        """
        for key, value in fields.items():
            if key == 'priority':
                fields['priority_id'] = self._get_priority_id(value)
                fields.pop('priority')
            if key == 'assignee':
                fields['assigned_to_id'] = self._get_user_id(value)
                fields.pop('assignee')
            if key == 'estimated_time':
                fields['total_estimated_hours'] = value
                fields.pop('estimated_time')
        return fields


def main():
    """
    main() function, not directly callable.
    :return:
    """
    print("Not directly executable")


if __name__ == "__main__":
    main()

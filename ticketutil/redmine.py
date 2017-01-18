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
        self.auth_url = '{0}/projects/{1}.json'.format(self.url, project)

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

        return ticket_url

    def create(self, subject, description, **kwargs):
        """
        Creates a ticket.
        The required parameters for ticket creation are subject and description.
        Keyword arguments are used for other ticket fields.
        :param subject: The ticket subject.
        :param description: The ticket description.
        :return
        """
        if subject is None:
            logging.error("subject is a necessary parameter for ticket creation.")
            return
        if description is None:
            logging.error("description is a necessary parameter for ticket creation.")
            return

        # Create our parameters used in ticket creation.
        params = self._create_ticket_parameters(subject, description, kwargs)

        # Create our ticket.
        self._create_ticket_request(params)

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
        :return:
        """
        # Attempt to create ticket.
        try:
            r = self.s.post("{0}.json".format(self.rest_url), json=params)
            r.raise_for_status()
            logging.debug("Create ticket: Status Code: {0}".format(r.status_code))

            # Retrieve key from new ticket.
            ticket_content = r.json()
            self.ticket_id = ticket_content['issue']['id']
            self.ticket_url = self._generate_ticket_url()
            logging.info("Created ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error creating ticket")
            logging.error(e.args[0])

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

        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        # Some of the ticket fields need to be in a specific form for the tool.
        fields = self._prepare_ticket_fields(kwargs)

        params = {'issue': fields}

        # Attempt to edit ticket.
        try:
            r = self.s.put("{0}/{1}.json".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Editing Ticket: Status Code: {0}".format(r.status_code))
            logging.info("Edited ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error editing ticket")
            logging.error(e.args[0])

    def add_comment(self, comment):
        """
        Adds a comment to a Redmine ticket.
        :param comment: A string representing the comment to be added.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        params = {'issue': {}}
        params['issue']['notes'] = comment

        # Attempt to add comment to ticket.
        try:
            r = self.s.put('{0}/{1}.json'.format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Add comment: Status Code: {0}".format(r.status_code))
            logging.info("Added comment to ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error adding comment to ticket")
            logging.error(e.args[0])

    def change_status(self, status):
        """
        Changes status of a Redmine ticket.
        :param status: Status to change to.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        status_id = self._get_status_id(status)
        if not status_id:
            logging.error("Not a valid status: {0}.".format(status))
            return

        params = {'issue': {}}
        params['issue']['status_id'] = status_id

        # Attempt to change status of ticket.
        try:
            r = self.s.put('{0}/{1}.json'.format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Changing status of ticket: Status Code: {0}".format(r.status_code))
            logging.info("Changed status of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error changing status of ticket")
            logging.error(e.args[0])

    def remove_watcher(self, watcher):
        """
        Removes watcher from a Redmine ticket.
        Accepts an email or username.
        :param watcher: Username or email of watcher to remove.
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        # If an email address was passed in for watcher param, extract the 'name' piece.
        if '@' in watcher:
            watcher = "{0}".format(watcher.split('@')[0].strip())

        watcher_id = self._get_user_id(watcher)

        try:
            r = self.s.delete("{0}/{1}/watchers/{2}.json".format(self.rest_url, self.ticket_id, watcher_id))
            r.raise_for_status()
            logging.debug("Remove watcher {0}: Status Code: {0}".format(watcher, r.status_code))
            logging.info("Removed watcher {0} from ticket {1} - {2}".format(watcher, self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error removing watcher {0} from ticket".format(watcher))
            logging.error(e.args[0])

    def add_watcher(self, watcher):
        """
        Adds watcher to a Redmine ticket.
        Accepts an email or username.
        :param watcher: Username or email of watcher to remove.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        # If an email address was passed in for watcher param, extract the 'name' piece.
        if '@' in watcher:
            watcher = "{0}".format(watcher.split('@')[0].strip())

        if watcher:
            watcher_id = self._get_user_id(watcher)
            params = {'user_id': watcher_id}
            try:
                r = self.s.post("{0}/{1}/watchers.json".format(self.rest_url, self.ticket_id), json=params)
                r.raise_for_status()
                logging.debug("Add watcher {0}: Status Code: {0}".format(r.status_code))
                logging.info("Added watcher {0} to ticket {1} - {2}".format(watcher, self.ticket_id, self.ticket_url))
            except requests.RequestException as e:
                logging.error("Error adding {0} as a watcher to ticket".format(watcher))
                logging.error(e.args[0])

    def _get_project_id(self):
        """
        Get project id from project name.
        Project name is used as the parameter when creating the Ticket object,
        but the Project ID is needed when creating the ticket.
        :return:
        """
        try:
            r = self.s.get(self.auth_url)
            r.raise_for_status()
            logging.debug("Get Project ID: Status Code: {0}".format(r.status_code))

            # Retrieve project id.
            project_info = r.json()
            project_id = project_info['project']['id']
            logging.debug("Retrieved Project ID: {0}".format(project_id))
            return project_id
        except requests.RequestException as e:
            logging.error("Error retrieving Project ID")
            logging.error(e.args[0])
            return None

    def _get_status_id(self, status_name):
        """
        Gets status id corresponding to status name using issue_statuses.json.

        :param status_name: The name of the status.
        :return: status_id: The id of the status.
        """
        try:
            r = self.s.get('{0}/issue_statuses.json'.format(self.url))
            r.raise_for_status()
        except requests.RequestException as e:
            logging.error("Error retrieving Redmine status information")
            logging.error(e.args[0])
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
            r.raise_for_status()
        except requests.RequestException as e:
            logging.error("Error retrieving Redmine priority information")
            logging.error(e.args[0])
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
            r.raise_for_status()
        except requests.RequestException as e:
            logging.error("Error retrieving Redmine user information")
            logging.error(e.args[0])
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

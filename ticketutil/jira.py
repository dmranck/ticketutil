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


class JiraTicket(ticket.Ticket):
    """
    A JIRA Ticket object. Contains JIRA-specific methods for working with tickets.
    """
    def __init__(self, url, project, auth=None, ticket_id=None):
        self.ticketing_tool = 'JIRA'

        # Right now, hardcode auth as 'kerberos', which is the only supported auth for JIRA.
        self.auth = 'kerberos'

        # JIRA URLs
        self.url = url
        self.rest_url = '{0}/rest/api/2/issue'.format(self.url)
        self.auth_url = '{0}/step-auth-gss'.format(self.url)

        # Call our parent class's init method which creates our requests session.
        super(JiraTicket, self).__init__(project, ticket_id)

    def _generate_ticket_url(self):
        """
        Generates the ticket URL out of the url, project, and ticket_id.
        :return: ticket_url: The URL of the ticket.
        """
        ticket_url = None

        # If we are receiving a ticket_id, it indicates we'll be doing an update or resolve, so set ticket_url.
        if self.ticket_id:
            if '-' not in self.ticket_id:
                # Adding the project to the beginning of the ticket_id, so that the ticket_id is of the form KEY-XX.
                self.ticket_id = "{0}-{1}".format(self.project, self.ticket_id)
            ticket_url = "{0}/browse/{1}".format(self.url, self.ticket_id)

        return ticket_url

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
        Creates the payload for the POST request when creating a JIRA ticket.

        The required parameters for ticket creation are summary and description.
        Keyword arguments are used for other ticket fields.

        Fields examples:
        summary='Ticket summary'
        description='Ticket description'
        priority='Major'
        type='Task'
        assignee='username'
        reporter='username'
        environment='Environment Test'
        duedate='2017-01-13'
        parent='KEY-XX'
        customfield_XXXXX='Custom field text'

        :param summary: The ticket summary.
        :param description: The ticket description.
        :param fields: Other ticket fields.
        :return: params: A dictionary to pass in to the POST request containing ticket details.
        """
        # Create our parameters for creating the ticket.
        params = {'fields': {}}
        params['fields'] = {'project': {'key': self.project},
                            'summary': summary,
                            'description': description}

        # Some of the ticket fields need to be in a specific form for the tool.
        fields = _prepare_ticket_fields(fields)

        # Update params dict with items from options_dict.
        params['fields'].update(fields)

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

            # Retrieve key from new ticket.
            ticket_content = r.json()
            self.ticket_id = ticket_content['key']
            self.ticket_url = self._generate_ticket_url()
            logging.info("Created ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error creating ticket - {0}".format(list(r.json()['errors'].values())[0]))
            logging.error(e.args[0])

    def edit(self, **kwargs):
        """
        Edits fields in a JIRA ticket.
        Keyword arguments are used to specify ticket fields.

        Fields examples:
        summary='Ticket summary'
        description='Ticket description'
        priority='Major'
        type='Task'
        assignee='username'
        reporter='username'
        environment='Environment Test'
        duedate='2017-01-13'
        parent='KEY-XX'
        customfield_XXXXX='Custom field text'

        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        # Some of the ticket fields need to be in a specific form for the tool.
        fields = _prepare_ticket_fields(kwargs)

        params = {'fields': fields}

        # Attempt to edit ticket.
        try:
            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Editing Ticket: Status Code: {0}".format(r.status_code))
            logging.info("Edited ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error creating ticket - {0}".format(list(r.json()['errors'].values())[0]))
            logging.error(e.args[0])

    def add_comment(self, comment):
        """
        Adds a comment to a JIRA ticket.
        :param comment: A string representing the comment to be added.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        params = {'body': comment}

        # Attempt to add comment to ticket.
        try:
            r = self.s.post("{0}/{1}/comment".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Add comment: Status Code: {0}".format(r.status_code))
            logging.info("Added comment to ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error adding comment to ticket")
            logging.error(e.args[0])

    def change_status(self, status):
        """
        Changes status of a JIRA ticket.

        To view possible workflow transitions for a particular ticket:
        <self.rest_url>/<self.ticket_id>/transitions

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

        params = {'transition': {}}
        params['transition']['id'] = status_id

        # Attempt to change status of ticket
        try:
            r = self.s.post("{0}/{1}/transitions".format(self.rest_url,  self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Changing status of ticket: Status Code: {0}".format(r.status_code))
            logging.info("Changed status of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error changing status of ticket")
            logging.error(e.args[0])

    def remove_all_watchers(self):
        """
        Removes all watchers from a JIRA ticket.
        :return watchers_list: A list of watchers that were removed from ticket.
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        try:
            # Get watchers list and convert to json. Then remove all watchers.
            r = self.s.get("{0}/{1}/watchers".format(self.rest_url, self.ticket_id))
            r.raise_for_status()
            watchers_json = r.json()
            watchers_list = []
            for watcher in watchers_json['watchers']:
                watchers_list.append(watcher['name'])
                r = self.s.delete("{0}/{1}/watchers?username={2}".format(self.rest_url,
                                                                         self.ticket_id,
                                                                         watcher['name']))
                r.raise_for_status()
                logging.debug("Remove watcher {0}: Status Code: {0}".format(watcher['name'], r.status_code))
            logging.info("Removed all watchers from ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            return watchers_list
        except requests.RequestException as e:
            logging.error("Error removing watchers from ticket")
            logging.error(e.args[0])

    def remove_watcher(self, watcher):
        """
        Removes watcher from a JIRA ticket.
        Accepts an email or username.
        :param watcher: Username of watcher to remove.
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        # If an email address was passed in for watcher param, extract the 'name' piece.
        if '@' in watcher:
            watcher = "{0}".format(watcher.split('@')[0].strip())

        try:
            r = self.s.delete("{0}/{1}/watchers?username={2}".format(self.rest_url, self.ticket_id, watcher))
            r.raise_for_status()
            logging.debug("Remove watcher {0}: Status Code: {0}".format(watcher, r.status_code))
            logging.info("Removed watcher {0} from ticket {1} - {2}".format(watcher, self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error removing watcher {0} from ticket".format(watcher))
            logging.error(e.args[0])

    def add_watcher(self, watcher):
        """
        Adds watcher to a JIRA ticket.
        Accepts an email or username.
        :param watcher: Username of watcher to remove.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        # If an email address was passed in for watcher param, extract the 'name' piece.
        # Add double quotes around the name, which is needed for JIRA API.
        if '@' in watcher:
            watcher = "{0}".format(watcher.split('@')[0].strip())
        watcher = "\"{0}\"".format(watcher)

        # For some reason, if you try to add an empty string as a watcher, it adds the requestor.
        # So, only execute this code if the watcher is not an empty string.
        if watcher:
            try:
                r = self.s.post("{0}/{1}/watchers".format(self.rest_url, self.ticket_id), data=watcher)
                r.raise_for_status()
                logging.debug("Add watcher {0}: Status Code: {0}".format(r.status_code))
                logging.info("Added watcher {0} to ticket {1} - {2}".format(watcher, self.ticket_id, self.ticket_url))
            except requests.RequestException as e:
                logging.error("Error adding {0} as a watcher to ticket".format(watcher))
                logging.error(e.args[0])

    def add_attachment(self, file_name):
        """
        Attaches a file to a JIRA ticket.
        :param file_name: A string representing the file to attach.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        headers = {"X-Atlassian-Token": "nocheck"}

        # Attempt to attach file.
        try:
            params = {'file': open(file_name, 'r')}
            r = self.s.post("{0}/{1}/attachments".format(self.rest_url, self.ticket_id),
                            files=params,
                            headers=headers)
            r.raise_for_status()
            logging.debug("Add attachment: Status Code: {0}".format(r.status_code))
            logging.info("Attached File {0}: {1} - {2}".format(file_name, self.ticket_id, self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error attaching file {0}".format(file_name))
            logging.error(e.args[0])
        except IOError:
            logging.error("{0} not found".format(file_name))

    def _get_status_id(self, status_name):
        """
        Gets status id corresponding to status name.

        :param status_name: The name of the status.
        :return: status_id: The id of the status.
        """
        try:
            r = self.s.get('{0}/{1}/transitions'.format(self.rest_url, self.ticket_id))
            r.raise_for_status()
        except requests.RequestException as e:
            logging.error("Error retrieving JIRA status information")
            logging.error(e.args[0])
            return

        status_json = r.json()
        for status in status_json['transitions']:
            if status['name'] == status_name:
                return status['id']


def _prepare_ticket_fields(fields):
        """
        Makes sure each key value pair in the fields dictionary is in the correct form.
        :param fields: Ticket fields.
        :return: fields: Ticket fields in the correct form for the ticketing tool.
        """
        for key, value in fields.items():
            if key in ['priority', 'assignee', 'reporter', 'parent']:
                fields[key] = {'name': value}
            if key == 'type':
                fields['issuetype'] = {'name': value}
                fields.pop('type')
        return fields


def main():
    """
    main() function, not directly callable.
    :return:
    """
    print("Not directly executable")


if __name__ == "__main__":
    main()

import logging
import re
import os

import gssapi
import requests
from requests_kerberos import HTTPKerberosAuth, DISABLED

__author__ = 'dranck, rnester, kshirsal'

# Disable warnings for requests because we aren't doing certificate verification
requests.packages.urllib3.disable_warnings()

DEBUG = True

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


class Ticket(object):
    """
    A class representing a ticket.
    """
    def __init__(self, project_key, ticket_id):
        self.project_key = project_key
        self.ticket_id = ticket_id

        # Possible update()/resolve() instance variables.
        if self.ticket_id:
            self.ticket_url = self.craft_ticket_url()
        else:
            self.ticket_url = None

        # Create our requests session below.
        self.s = self.create_requests_session()

    def create(self, options_dict):
        """
        Creates a ticket - Expecting a dictionary of options to use in the ticket request.
        :param options_dict: Key: Value pairs for updating fields in ticket -
                             See create_ticket_parameters() in inherited classes for examples.
        :return:
        """
        # Create our parameters used in ticket creation.
        params = self.create_ticket_parameters(options_dict)

        # Create our ticket.
        self.create_ticket(params)

    def update(self, comment):
        """
        Updates a ticket.
        :param comment: Comment to add to the ticket.
        :return:
        """
        if self.ticket_id:
            # Update the ticket by adding a comment.
            self.add_comment(comment)
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def resolve(self, transition_id=None):
        """
        Resolve a ticket.
        :param transition_id: Used for JIRA tickets - the transition id of the closed state.
        :return:
        """
        if self.ticket_id:
            # Transition the ticket to the closed state
            self.transition_ticket(transition_id)

            # Include a comment that the ticket was resolved.
            logging.info("Resolved ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def set_ticket_id(self, ticket_id):
        """
        Sets the ticket_id and ticket_url instance vars for the current ticket object.
        :param ticket_id: Ticket id you would like to set.
        :return:
        """
        self.ticket_id = ticket_id
        self.ticket_url = self.craft_ticket_url()

        logging.info("Current ticket: {0} - {1}".format(self.ticket_id, self.ticket_url))

    def create_requests_session(self):
        """
        Creates a Requests Session and authenticates to base API URL with kerberos-requests.
        We're using a Session to persist cookies across all requests made from the Session instance.
        :return s: Requests Session.
        """
        # TODO: Support other authentication methods.
        # Set up authentication for requests session.
        s = requests.Session()
        if self.auth == 'kerberos':
            self.principal = get_kerberos_principal()
            s.auth = HTTPKerberosAuth(mutual_authentication=DISABLED)
            s.verify = False
        if isinstance(self.auth, tuple):
            s.auth = self.auth

        # Try to authenticate to auth_url.
        try:
            r = s.get(self.auth_url)
            r.raise_for_status()
            logging.debug("Create requests session: Status Code: {0}".format(r.status_code))
            logging.info("Successfully authenticated to {0}".format(self.ticketing_tool))
        # We log an error if authentication was not successful, because rest of the HTTP requests will not succeed.
        except requests.RequestException as e:
            logging.error("Error authenticating to {0}. No valid kerberos principal found.".format(self.auth_url))
            logging.error(e.args[0])
        return s

    def close_requests_session(self):
        """
        Closes requests session for Ticket object.
        :return:
        """
        self.s.close()


class BugzillaTicket(Ticket):
    """
    A BZ Ticket object. Contains BZ-specific methods for working with tickets.
    """

    def __init__(self, base_url, project_key, ticket_id=None, auth=None, user=None, password=None):
        self.ticketing_tool = 'Bugzilla'

        # Right now, hardcode auth as 'kerberos', which is the only supported auth for BZ.
        self.auth = auth if auth else 'kerberos'

        self.credentials = {"login": user, "password": password}
        self.token = None

        # BZ URLs
        self.base_url = base_url
        self.rest_url = '{0}/rest/bug'.format(self.base_url)
        self.auth_url = '{0}/rest/login'.format(self.base_url)

        # Call our parent class's init method which creates our requests session.
        super(BugzillaTicket, self).__init__(project_key, ticket_id)

    def craft_ticket_url(self):
        """
        Crafts the ticket URL out of the base_url, project_key, and ticket_id.
        :return: ticket_url: The URL of the ticket.
        """
        ticket_url = None

        # If we are receiving a ticket_id, it indicates we'll be doing an update or resolve, so set ticket_url.
        if self.ticket_id:
            ticket_url = "{0}/show_bug.cgi?id={1}".format(self.base_url, self.ticket_id)

        return ticket_url

    def create_ticket_parameters(self, options_dict):
        """
        Creates the payload for the POST request when creating a Bugzilla ticket.

        Example:
        options_dict = {"product" : "TestProduct",
                        "component" : "TestComponent",
                        "version" : "unspecified",
                        "summary" : "'This is a test bug - please disregard",
                        "alias" : "SomeAlias",
                        "op_sys" : "All",
                        "priority" : "P1",
                        "rep_platform" : "All"}
        :param options_dict: Key: Value pairs for updating fields in Bugzilla.
        :return: params: A dictionary to pass in to the POST request containing ticket details.
        """
        # Create our parameters for creating the ticket.
        params = {"product": str(self.project_key)}

        # Iterate through our options and add them to the params dict.
        params.update(options_dict)
        return params

    def create_requests_session(self):
        """
        Returns to the super class if the authentication method is kerberos.
        Creates a Requests Session and authenticates to base API URL with authentication other then kerberos.
        We're using a Session to persist cookies across all requests made from the Session instance.
        :return s: Requests Session.
        """
        if self.auth != 'rest':
            return super()

        try:
            s = requests.Session()
            r = s.get(self.auth_url, params=self.credentials, verify=False)
            r.raise_for_status()
            resp = r.json()
            self.token = resp['token']
            logging.debug("Create requests session: Status Code: {0}".format(r.status_code))
            logging.info("Successfully authenticated to {0} with token: {1}".format(self.ticketing_tool, self.token))
            return s

        # We log an error if authentication was not successful, because rest of the HTTP requests will not succeed.
        except requests.RequestException as e:
            logging.error("Error authenticating to {0}. No valid credentials were provided.".format(self.auth_url))
            logging.error(e.args[0])

    def create_ticket(self, params):
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


            self.ticket_id = r.json()['id']
            self.ticket_url = self.craft_ticket_url()
            logging.info("Created ticket {0} - {1}".format(self.ticket_id, self.ticket_url))

        # If ticket creation is not successful, log an error.
        except requests.RequestException as e:
            logging.error("Error creating ticket")
            logging.error(e.args[0])

    def add_comment(self, comment):
        """
        Adds a comment to a Bugzilla ticket.
        :param comment: A string representing the comment to be added.
        :return:
        """
        if not self.ticket_id: # Create the payload for our update.
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        try:
            params = {'comment': comment}

            if self.token:
                params['token'] = self.token
            r = self.s.post("{0}/{1}/comment".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Add comment: Status Code: {0}".format(r.status_code))
            logging.info("Updated ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.

        except requests.RequestException as e:
            logging.error("Error updating ticket")
            logging.error(e.args[0])

    def transition_ticket(self, resolve_params):
        """
        Resolving  a Bugzilla ticket.
        :param resolution: A string representing the resolution to be added.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        try:
            # Create the payload for our update.
            params = resolve_params

            if self.token:
                params['token'] = self.token

            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Resolving Ticket: Status Code: {0}".format(r.status_code))
            logging.info("Updated ticket {0} - {1}".format(self.ticket_id, self.ticket_url))

        except requests.RequestException as e:
            logging.error("Error resolving the ticket")
            logging.error(e.args[0])

    def edit_ticket_fields(self, edit_ticket_dict):
        """
        Edits fields in a Bugzilla issue.

        Examples for edit_ticket_dict parameter:
        {'summary': 'New subject',
        'product': 'Valid product label',
        'component': 'Component related to the product against which the bug is raised',
        'version': 'Version against which the bug is supposed to be filed',
        'alias': 'If you wish to set any alias for the bug'}

        :param edit_ticket_dict: Dictionary containing data for editing ticket.
        :return:
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")
            return

        try:
            # Create the payload for our update.
            params = edit_ticket_dict

            if self.token:
                params['token'] = self.token

            r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
            r.raise_for_status()
            logging.debug("Resolving Ticket: Status Code: {0}".format(r.status_code))
            logging.info("Edited ticket with the mentioned fields {0} - {1}".format(self.ticket_id, self.ticket_url))

        except requests.RequestException as e:
            logging.error("Error resolving the ticket")
            logging.error(e.args[0])


class JiraTicket(Ticket):
    """
    A JIRA Ticket object. Contains JIRA-specific methods for working with tickets.
    """
    def __init__(self, base_url, project_key, ticket_id=None, auth=None):
        self.ticketing_tool = 'JIRA'

        # Right now, hardcode auth as 'kerberos', which is the only supported auth for JIRA.
        self.auth = 'kerberos'

        # JIRA URLs
        self.base_url = base_url
        self.rest_url = '{0}/rest/api/2/issue'.format(self.base_url)
        self.auth_url = '{0}/step-auth-gss'.format(self.base_url)

        # Call our parent class's init method which creates our requests session.
        super(JiraTicket, self).__init__(project_key, ticket_id)

    def craft_ticket_url(self):
        """
        Crafts the ticket URL out of the base_url, project_key, and ticket_id.
        :return: ticket_url: The URL of the ticket.
        """
        # Adding the project_key to the beginning of the ticket_id, so that the ticket_id is of the form KEY-XX.
        # If we are receiving a ticket_id, it indicates we'll be doing an update or resolve, so set ticket_url.
        if self.ticket_id:
            self.ticket_id = "{0}-{1}".format(self.project_key, self.ticket_id)
            ticket_url = "{0}/browse/{1}".format(self.base_url, self.ticket_id)

        # If we do not receive a ticket ID in our initialization it indicates we'll be creating a ticket.
        else:
            ticket_url = None

        return ticket_url

    def create_ticket_parameters(self, fields_dict, update_dict=None):
        """
        Creates the payload for the POST request when creating a JIRA ticket.

        Example:
        fields_dict = {'summary': 'Ticket Summary',
                       'description': 'Ticket Description',
                       'priority': {'name': 'Major'}
                       'issuetype': {'name': 'Task'}}

        update_dict = {'issuelinks': [{'add': {'type': {'name': 'Relates'},
                                       'inwardIssue': {'key': 'PROJECT-100'}}}]}

        :param fields_dict: Key: Value pairs for the field dict in JIRA.
        :param update_dict: Key: Value pairs for the update dict in JIRA.
        :return: params: A dictionary to pass in to the POST request containing ticket details.
        """
        # Create our parameters for creating the ticket.
        params = {'fields': {}}
        params['fields']['project'] = {'key': self.project_key}

        # Update params dict with items from options_dict.
        params['fields'].update(fields_dict)

        if update_dict:
            params['update'] = update_dict

        return params

    def create_ticket(self, params):
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
            ticket_id = ticket_content['key']
            ticket_url = "{0}/browse/{1}".format(self.base_url, ticket_id)
            logging.info("Created ticket {0} - {1}".format(ticket_id, ticket_url))
            self.ticket_id = ticket_id
            self.ticket_url = ticket_url

        # If ticket creation is not successful, log an error.
        except requests.RequestException as e:
            logging.error("Error creating ticket")
            logging.error(e.args[0])

    def add_comment(self, comment):
        """
        Adds a comment to a JIRA issue.
        :param comment: A string representing the comment to be added.
        :return:
        """
        if self.ticket_id:
            params = {'body': comment}
            try:
                r = self.s.post("{0}/{1}/comment".format(self.rest_url, self.ticket_id), json=params)
                r.raise_for_status()
                logging.debug("Add comment: Status Code: {0}".format(r.status_code))
                logging.info("Updated ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
            except requests.RequestException as e:
                logging.error("Error updating ticket")
                logging.error(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def transition_ticket(self, transition_id):
        """
        Transitions a JIRA issue to a different workflow state.

        To view possible workflow transitions for a particular issue:
        <self.rest_url>/<self.ticket_id>/transitions

        :param transition_id: The transition id of the desired state.
        :return:
        """
        if self.ticket_id:
            params = {'transition': {}}
            params['transition']['id'] = transition_id

            # Attempt to transition ticket to a new state.
            try:
                r = self.s.post("{0}/{1}/transitions".format(self.rest_url,  self.ticket_id), json=params)
                r.raise_for_status()
                logging.debug("Transition ticket: Status Code: {0}".format(r.status_code))
                logging.info("Transitioned ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
            except requests.RequestException as e:
                logging.error("Error transitioning ticket")
                logging.error(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def edit_ticket_fields(self, edit_ticket_dict):
        """
        Edits fields in a JIRA issue.

        Examples for edit_ticket_dict parameter:
        {'description': 'New Description'}
        {'issuetype': {'name': 'Bug'}}
        {'assignee': {'name': 'dranck'}}

        :param edit_ticket_dict: Dictionary containing data for editing ticket.
        :return:
        """
        if self.ticket_id:
            params = {'fields': edit_ticket_dict}
            try:
                r = self.s.put("{0}/{1}".format(self.rest_url, self.ticket_id), json=params)
                r.raise_for_status()
                logging.debug("Edit ticket field: Status Code: {0}".format(r.status_code))
                logging.info("Edited ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
            except requests.RequestException as e:
                logging.error("Error editing ticket")
                logging.error(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def remove_watchers(self):
        """
        Removes all watchers from a JIRA issue.
        :return watchers_list: A comma-delimited string of watchers that were removed from ticket.
        """
        if self.ticket_id:
            try:
                # Get watchers list and convert to json. Then remove all watchers.
                r = self.s.get("{0}/{1}/watchers".format(self.rest_url, self.ticket_id))
                watchers_json = r.json()
                watchers_list = []
                for watcher in watchers_json['watchers']:
                    watchers_list.append(watcher['name'])
                    r = self.s.delete("{0}/{1}/watchers?username={2}".format(self.rest_url,
                                                                             self.ticket_id,
                                                                             watcher['name']))
                    r.raise_for_status()
                    logging.debug("Remove watcher: Status Code: {0}".format(r.status_code))
                return ", ".join(watchers_list)
            except requests.RequestException as e:
                logging.error("Error removing watchers from ticket")
                logging.error(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def add_watchers(self, watchers_list):
        """
        Adds watchers to a JIRA issue.
        :param watchers_list: A comma-delimited string containing watchers to be added.
        :return:
        """
        if self.ticket_id:
            # Add watchers to ticket.
            # For some reason, if you try to add an empty string as a watcher, it adds the requestor.
            # So, only execute this code if the list of watchers is not an empty string.
            if watchers_list:
                for watcher in watchers_list.split(','):
                    try:
                        # Extract the 'name' piece from the email address.
                        # Add double quotes around the name, which is needed for JIRA API.
                        watcher = "\"{0}\"".format(watcher.split('@')[0].strip())
                        r = self.s.post("{0}/{1}/watchers".format(self.rest_url, self.ticket_id), data=watcher)
                        r.raise_for_status()
                        logging.debug("Add watcher: Status Code: {0}".format(r.status_code))
                    except requests.RequestException as e:
                        logging.debug("Error adding {0} as a watcher to ticket".format(watcher))
                        logging.debug(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")


class RTTicket(Ticket):
    """
    A RT Ticket object. Contains RT-specific methods for working with tickets.
    """
    def __init__(self, base_url, project_key, ticket_id=None, auth=None):
        self.ticketing_tool = 'RT'

        # Right now, hardcode auth as 'kerberos', which is the only supported auth for RT.
        self.auth = 'kerberos'

        # RT URLs
        self.base_url = base_url
        self.rest_url = '{0}/REST/1.0'.format(self.base_url)
        self.auth_url = '{0}/index.html'.format(self.rest_url)

        # Call our parent class's init method which creates our requests session.
        super(RTTicket, self).__init__(project_key, ticket_id)

    def craft_ticket_url(self):
        """
        Crafts the ticket URL out of the base_url, project_key, and ticket_id.
        :return: ticket_url: The URL of the ticket.
        """
        # If we are receiving a ticket_id, it indicates we'll be doing an update or resolve, so set ticket_url.
        if self.ticket_id:
            ticket_url = "{0}/Ticket/Display.html?id={1}".format(self.base_url, self.ticket_id)

        # If we do not receive a ticket ID in our initialization it indicates we'll be creating a ticket.
        else:
            ticket_url = None

        return ticket_url

    def create_ticket_parameters(self, options_dict):
        """
        Creates the payload for the POST request when creating a RT ticket.

        Example:
        options_dict = {'Subject': 'Ticket Title',
                        'Text': 'Ticket Description',
                        'CC': '<email_address_1>, <email_address_2>'}

        :param options_dict: Key: Value pairs for updating fields in RT.
        :return: params: A string to pass in to the POST request containing ticket details.
        """
        # Weird format for request data that RT is expecting...
        params = 'content='
        params += 'Queue: {0}\n'.format(self.project_key)
        params += 'Requestor: {0}\n'.format(self.principal)

        # Iterate through our options and add them to the params dict.
        for key, value in options_dict.items():
            # RT requires a special encoding on the Text parameter.
            if key == 'Text':
                value = self.text_encode(value)
            params += '{0}: {1}\n'.format(key, value)

        return params

    def create_ticket(self, params):
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
            ticket_id = re.search('Ticket (\d+) created', ticket_content).groups()[0]
            ticket_url = "{0}/Ticket/Display.html?id={1}".format(self.base_url, ticket_id)
            logging.info("Created ticket {0} - {1}".format(ticket_id, ticket_url))
            self.ticket_id = ticket_id
            self.ticket_url = ticket_url

        # If ticket creation is not successful, log an error.
        except requests.RequestException as e:
            logging.error("Error creating ticket")
            logging.error(e.args[0])

    def edit_ticket_fields(self, edit_ticket_dict):
        """
        Edits fields in a RT issue.

        Examples for edit_ticket_dict parameter:
        {'Subject': 'New Ticket Title',
        'Priority': '5'}

        :param edit_ticket_dict: Dictionary containing data for editing ticket.
        :return:
        """
        if self.ticket_id:
            params = 'content='

            # Iterate through our options and add them to the params dict.
            for key, value in edit_ticket_dict.items():
                params += '{0}: {1}\n'.format(key, value)

            try:
                r = self.s.post("{0}/ticket/{1}/edit".format(self.rest_url, self.ticket_id), data=params)
                r.raise_for_status()
                logging.debug("Edit ticket field: Status Code: {0}".format(r.status_code))
                logging.info("Edited ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
            except requests.RequestException as e:
                logging.error("Error editing ticket")
                logging.error(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def add_comment(self, comment):
        """
        Adds a comment to a RT issue.
        :param comment: A string representing the comment to be added.
        :return:
        """
        if self.ticket_id:
            # Create the payload for our update.
            params = 'content='
            params += 'Action: correspond\n'
            params += 'Text: {0}\n'.format(comment)

            # Attempt to add comment to ticket.
            try:
                r = self.s.post('{0}/ticket/{1}/comment'.format(self.rest_url, self.ticket_id), data=params)
                r.raise_for_status()
                logging.debug("Add comment: Status Code: {0}".format(r.status_code))
                logging.info("Updated ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
            except requests.RequestException as e:
                logging.error("Error updating ticket")
                logging.error(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def transition_ticket(self, transition_id=None):
        """
        Transitions a RT ticket to the resolved state.
        :param: transition_id: Used for JIRA tickets, not used for RT.
        :return:
        """
        if self.ticket_id:
            # Create the payload for resolving the ticket.
            params = 'content='
            params += 'Status: resolved\n'

            # Attempt to resolve ticket.
            try:
                r = self.s.post('{0}/ticket/{1}/edit'.format(self.rest_url, self.ticket_id), data=params)
                r.raise_for_status()
                logging.debug("Transition ticket: Status Code: {0}".format(r.status_code))
                logging.info("Transitioned ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
            except requests.RequestException as e:
                logging.error("Error transitioning ticket")
                logging.error(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def text_encode(self, text):
        """
        Encodes the text parameter in the form expected by RT's REST API when creating a ticket.
        Replaces spaces with '+' and new lines with '%0A+'.
        :param text: The string that will be used in the text field for our ticket.
        :return: The string containing the replaced characters.
        """
        text = text.replace(' ', '+')
        text = text.replace('\n', '%0A+')
        return text


class RedmineTicket(Ticket):
    """
    A Redmine Ticket object. Contains Redmine-specific methods for working with tickets.
    """
    def __init__(self, base_url, project_key, ticket_id=None, auth=None):
        self.ticketing_tool = 'Redmine'

        # The auth param should be of the form (<username>, <password>) for HTTP Basic authentication.
        self.auth = auth

        # RT URLs
        self.base_url = base_url
        self.rest_url = '{0}/issues'.format(self.base_url)
        self.auth_url = '{0}/projects/{1}.json'.format(self.base_url, project_key)

        # Call our parent class's init method which creates our requests session.
        super(RedmineTicket, self).__init__(project_key, ticket_id)

        # For Redmine tickets, specify headers.
        self.s.headers.update({'Content-Type': 'application/json'})

    def craft_ticket_url(self):
        """
        Crafts the ticket URL out of the rest_url and ticket_id.
        :return: ticket_url: The URL of the ticket.
        """
        # If we are receiving a ticket_id, it indicates we'll be doing an update or resolve, so set ticket_url.
        if self.ticket_id:
            ticket_url = "{0}/{1}".format(self.rest_url, self.ticket_id)

        # If we do not receive a ticket ID in our initialization it indicates we'll be creating a ticket.
        else:
            ticket_url = None

        return ticket_url

    def create_ticket_parameters(self, options_dict):
        """
        Creates the payload for the POST request when creating a Redmine ticket.

        Example:
        options_dict = {'subject': 'Ticket Subject',
                        'description': 'Ticket Description'}

        :param options_dict: Key: Value pairs for updating fields in Redmine.
        :return: params: A dictionary to pass in to the POST request containing ticket details.
        """
        # Create our parameters for creating the ticket.
        params = {'issue': {}}
        params['issue']['project_id'] = self.get_project_id()

        # Update params dict with items from options_dict.
        params['issue'].update(options_dict)

        return params

    def create_ticket(self, params):
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
            ticket_id = ticket_content['issue']['id']
            ticket_url = "{0}/{1}".format(self.rest_url, ticket_id)
            logging.info("Created ticket {0} - {1}".format(ticket_id, ticket_url))
            self.ticket_id = ticket_id
            self.ticket_url = ticket_url

        # If ticket creation is not successful, log an error.
        except requests.RequestException as e:
            logging.error("Error creating ticket")
            logging.error(e.args[0])

    def get_project_id(self):
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

    def edit_ticket_fields(self, edit_ticket_dict):
        """
        Edits fields in a Redmine issue.

        Examples for edit_ticket_dict parameter:
        {'subject': 'New subject',
        'notes': 'Comment about the update'}

        :param edit_ticket_dict: Dictionary containing data for editing ticket.
        :return:
        """
        if self.ticket_id:
            params = {'issue': edit_ticket_dict}
            try:
                r = self.s.put("{0}/{1}.json".format(self.rest_url, self.ticket_id), json=params)
                r.raise_for_status()
                logging.debug("Edit ticket field: Status Code: {0}".format(r.status_code))
                logging.info("Edited ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
            except requests.RequestException as e:
                logging.error("Error editing ticket")
                logging.error(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def add_comment(self, comment):
        """
        Adds a comment to a Redmine issue.
        :param comment: A string representing the comment to be added.
        :return:
        """
        if self.ticket_id:
            # Create the payload for our update.
            params = {'issue': {}}
            params['issue']['notes'] = comment

            # Attempt to add comment to ticket.
            try:
                r = self.s.put('{0}/{1}.json'.format(self.rest_url, self.ticket_id), json=params)
                r.raise_for_status()
                logging.debug("Add comment: Status Code: {0}".format(r.status_code))
                logging.info("Updated ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
            except requests.RequestException as e:
                logging.error("Error updating ticket")
                logging.error(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

    def transition_ticket(self, transition_id):
        """
        Transitions a Redmine ticket to the resolved state.
        :param transition_id: The transition id of the desired state.
        :return:
        """
        if self.ticket_id:
            # Create the payload for resolving the ticket. - Redmine's status_id for the resolved state is '3'.
            params = {'issue': {}}
            params['issue']['status_id'] = transition_id

            # Attempt to resolve ticket.
            try:
                r = self.s.put('{0}/{1}.json'.format(self.rest_url, self.ticket_id), json=params)
                r.raise_for_status()
                logging.debug("Transition ticket: Status Code: {0}".format(r.status_code))
                logging.info("Transitioned ticket {0} - {1}".format(self.ticket_id, self.ticket_url))
            # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
            except requests.RequestException as e:
                logging.error("Error transitioning ticket")
                logging.error(e.args[0])
        else:
            logging.error("No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(ticket_id)")

def get_kerberos_principal():
    """
    Use gssapi to get the current kerberos principal.
    This will be used as the requester for some tools when creating tickets.
    :return: The kerberos principal.
    """
    try:
        return str(gssapi.Credentials(usage='initiate').name).lower()
    except gssapi.raw.misc.GSSError:
        return None

def main():
    """
    main() function, not directly callable.
    :return:
    """
    print("Not directly executable")


if __name__ == "__main__":
    main()

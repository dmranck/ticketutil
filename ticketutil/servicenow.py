import json
import logging

import requests

from ticketutil.ticket import Ticket

__author__ = 'dranck, rnester, kshirsal, pzubaty'

logger = logging.getLogger(__name__)


class ServiceNowTicket(Ticket):
    """
    ServiceNow Ticket object. Contains ServiceNow specific methods for working
    with tickets.
    """

    def __init__(self, url, project, auth=None, ticket_id=None):
        """
        :param url: ServiceNow service url
        :param project: ServiceNow table or project
        :param auth: (<username>, <password>) for HTTP Basic Authentication
        :param ticket_id: ticket number, eg. 'PNT1234567'
        """
        self.ticketing_tool = 'ServiceNow'

        # The auth param should be of the form (<username>, <password>) for
        # HTTP Basic authentication.
        self.url = url
        self.auth = auth
        self.project = project
        self.rest_url = '{0}/api/now/v1/table/{1}'.format(
                        self.url, self.project)
        self.auth_url = self.rest_url

        # Call our parent class's init method which creates our requests
        # session.
        super(ServiceNowTicket, self).__init__(project, ticket_id)

        # For ServiceNow tickets, specify headers.
        self.s.headers.update({'Content-Type': 'application/json',
                               'Accept': 'application/json'})

    def _verify_project(self, project):
        """
        Queries the ServiceNow API to see if project is a valid table for
        the given ServiceNow instance. Query result is also used to get
        display values of available ticket states.
        :param project: The project table you're verifying.
        :return: True or False depending on if project is valid.
        """
        try:
            r = self.s.get("{0}/api/now/table/sys_choice?sysparm_query=name={1}^element=state^inactive=false".format(
                self.url, project))
            logger.debug("Verify project: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Unexpected error occurred when verifying project")
            logger.error(e)
            return False

        # After verifying project, determine possible states using request response.
        self.available_states = {}
        for state in r.json()['result']:
            label = state['label'].lower()
            self.available_states[label] = state['value']
        logger.debug("Project {0} is valid".format(project))
        return True

    def get_ticket_content(self, ticket_id=None):
        """
        Get ticket_content using ticket_id

        :param ticket_id: ticket number, if not set self.ticket_id is used
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if ticket_id is None:
            ticket_id = self.ticket_id
            if not self.ticket_id:
                error_message = "No ticket ID associated with ticket object. " \
                                "Set ticket ID with set_ticket_id(<ticket_id>)"
                logger.error(error_message)
                return self.request_result._replace(status='Failure', error_message=error_message)

        try:
            r = self.s.get("{0}?sysparm_query=GOTOnumber%3D{1}".format(self.rest_url, ticket_id))
            logger.debug("Get ticket content: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            error_message = "Error getting ticket content"
            logger.error(error_message)
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=error_message)

        ticket_content = r.json()
        return self.request_result._replace(ticket_content=ticket_content['result'][0])

    def _verify_ticket_id(self, ticket_id):
        """
        Calls get_ticket_content to make sure ticket if valid.
        :param ticket_id: The ticket you're verifying.
        :return: True or False depending on if ticket is valid.
        """
        result = self.get_ticket_content(ticket_id)
        if 'Failure' in result.status:
            logger.error("Ticket {0} is not valid".format(ticket_id))
            return False
        logger.debug("Ticket {0} is valid".format(ticket_id))
        self.ticket_id = ticket_id
        self.ticket_content = result.ticket_content
        self.sys_id = self.ticket_content['sys_id']
        self.ticket_rest_url = self.rest_url + '/' + self.sys_id
        return True

    def _generate_ticket_url(self):
        """
        Generates the ticket URL out of the url, project, and ticket_id.

        :return: ticket_url: The URL of the ticket.
        """
        ticket_url = None

        # If we are receiving a ticket_id, we have sys_id
        if self.sys_id:
            ticket_url = '{0}/{1}.do?sys_id={2}'.format(self.url, self.project,
                                                        self.sys_id)

        # This method is called from set_ticket_id(), _create_ticket_request(), or Ticket.__init__().
        # If this method is being called, we want to update the url field in our Result namedtuple.
        content = self.get_ticket_content()
        self.request_result = self.request_result._replace(url=ticket_url, ticket_content=content.ticket_content)

        return ticket_url

    def create(self, short_description, description, category, item, **kwargs):
        """
        Creates new issue, new record in the ServiceNow table

        :param short_description: short description of the issue
        :param description: full description of the issue
        :param category: ticket category (Category in WebUI)
        :param item: ticket category item (Item in WebUI)
        :param kwargs: optional fields

        Fields example:
        contact_type = 'Email',
        opened_for = 'PNT',
        assigned_to = 'pzubaty',
        impact = '2',
        urgency = '2',
        priority = '2'

        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        error_message = ""
        if description is None:
            error_message = "description is a necessary parameter for ticket creation"
        if short_description is None:
            error_message = "short_description is a necessary parameter for ticket creation"
        if category is None:
            error_message = "category is a necessary parameter for ticket creation"
        if item is None:
            error_message = "item is a necessary parameter for ticket creation"
        if error_message:
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        self.ticket_content = None
        fields = {'description': description,
                  'short_description': short_description,
                  'u_category': category,
                  'u_item': item}
        kwargs.update(fields)
        params = self._create_ticket_parameters(kwargs)
        return self._create_ticket_request(params)

    def _create_ticket_parameters(self, fields):
        """
        Creates the payload for the POST request when creating new ticket.

        :param fields: optional fields
        """
        fields = _prepare_ticket_fields(fields)

        params = ''
        for key, value in fields.items():
            params += ', {} : {}'.format(json.dumps(key), json.dumps(value))
        params = '{' + params[1:] + '}'
        return params

    def _create_ticket_request(self, params):
        """
        Tries to create the ticket through the ticketing tool's API.
        Retrieves the ticket_id and creates the ticket_url.
        :param params: The payload to send in the POST request.
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        try:
            r = self.s.post(self.rest_url, data=params)
            logger.debug("Create ticket: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error creating ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        ticket_content = r.json()
        self.ticket_content = ticket_content['result']

        self.ticket_id = self.ticket_content['number']
        self.sys_id = self.ticket_content['sys_id']
        self.ticket_url = self._generate_ticket_url()
        self.ticket_rest_url = self.rest_url + '/' + self.sys_id
        logger.info("Created ticket {0} - {1}".format(self.ticket_id, self.ticket_url))

        # Update our ticket_content field and return the result
        self.request_result = self.request_result._replace(ticket_content=self.ticket_content)
        return self.request_result

    def change_status(self, status):
        """
        Change ServiceNow ticket status

        :param status: State to change to
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        try:
            fields = {'state': self.available_states[status.lower()]}
        except KeyError as e:
            error_message = 'Invalid state {}'.format(e)
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        params = self._create_ticket_parameters(fields)

        try:
            r = self.s.put(self.ticket_rest_url, data=params)
            logger.debug("Change status: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error('Failed to change ticket status')
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        self.ticket_content = r.json()['result']
        logger.info("Changed status of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))

        # Update our ticket_content field and return the result
        self.request_result = self.request_result._replace(ticket_content=self.ticket_content)
        return self.request_result

    def edit(self, **kwargs):
        """
        Edit ticket

        Edits a ServiceNow ticket, ticked_id (sys_id) must be set beforehand.
        You can set ticket_id by calling set_ticket_id(ticket_id) method.

        :param kwargs: optional fields

        Fields example:
        contact_type = 'Email',
        opened_for = 'PNT',
        assigned_to = 'pzubaty',
        impact = '2',
        urgency = '2',
        priority = '2'
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        params = self._create_ticket_parameters(kwargs)

        try:
            r = self.s.put(self.ticket_rest_url, data=params)
            logger.debug("Edit ticket: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error("Error editing ticket")
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        self.ticket_content = r.json()['result']
        logger.info("Edited ticket {0} - {1}".format(self.ticket_id, self.ticket_url))

        # Update our ticket_content field and return the result
        self.request_result = self.request_result._replace(ticket_content=self.ticket_content)
        return self.request_result

    def add_comment(self, comment):
        """
        Adds comment

        :param comment: new ticket comment
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        params = self._create_ticket_parameters({'comments': comment})

        try:
            r = self.s.put(self.ticket_rest_url, data=params)
            logger.debug("Add comment: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error('Failed to add the comment')
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        self.ticket_content = r.json()['result']
        logger.info("Added comment to ticket {0} - {1}".format(self.ticket_id, self.ticket_url))

        # Update our ticket_content field and return the result
        self.request_result = self.request_result._replace(ticket_content=self.ticket_content)
        return self.request_result

    def add_cc(self, user):
        """
        Adds user(s) to cc list.
        :param user: A string representing one user's email address, or a list of strings for multiple users.
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        watch_list = self.ticket_content['watch_list'].split(',')
        watch_list = [item.strip() for item in watch_list]
        if isinstance(user, str):
            user = [user]
        for item in user:
            if item not in watch_list:
                watch_list.append(item)

        fields = {'watch_list': ', '.join(watch_list)}
        params = self._create_ticket_parameters(fields)

        try:
            r = self.s.put(self.ticket_rest_url, data=params)
            logger.debug("Add cc: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error('Failed to add user(s) to CC list')
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        self.ticket_content = r.json()['result']
        logger.info("Added user(s) to cc list of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))

        # Update our ticket_content field and return the result
        self.request_result = self.request_result._replace(ticket_content=self.ticket_content)
        return self.request_result

    def rewrite_cc(self, user):
        """
        Rewrites user(s) in cc list.
        :param user: A string representing one user's email address, or a list of strings for multiple users.
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        if isinstance(user, str):
            user = [user]
        fields = {'watch_list': ', '.join(user)}
        params = self._create_ticket_parameters(fields)

        try:
            r = self.s.put(self.ticket_rest_url, data=params)
            logger.debug("Rewrite cc: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error('Failed to rewrite CC list')
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        self.ticket_content = r.json()['result']
        logger.info("Rewrote cc list of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))

        # Update our ticket_content field and return the result
        self.request_result = self.request_result._replace(ticket_content=self.ticket_content)
        return self.request_result

    def remove_cc(self, user):
        """
        Removes user(s) from cc list.
        :param user: A string representing one user's email address, or a list of strings for multiple users.
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        watch_list = self.ticket_content['watch_list'].split(',')
        watch_list = [item.strip() for item in watch_list]
        if isinstance(user, str):
            user = [user]
        for item in user:
            if item in watch_list:
                watch_list.remove(item)
        fields = {'watch_list': ', '.join(watch_list)}
        params = self._create_ticket_parameters(fields)

        try:
            r = self.s.put(self.ticket_rest_url, data=params)
            logger.debug("Remove cc: status code: {0}".format(r.status_code))
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error('Failed to remove user(s) from CC list')
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))

        self.ticket_content = r.json()['result']
        logger.info("Removed user(s) from cc list of ticket {0} - {1}".format(self.ticket_id, self.ticket_url))

        # Update our ticket_content field and return the result
        self.request_result = self.request_result._replace(ticket_content=self.ticket_content)
        return self.request_result

    def add_attachment(self, file_name, name=None):
        """
        Attaches a file to a ServiceNow ticket.
        :param file_name: A string representing the file to attach.
        :param name: A string representing the name under which the file is attached.
        :return: self.request_result: Named tuple containing request status, error_message, and url info.
        """
        if not self.ticket_id:
            error_message = "No ticket ID associated with ticket object. Set ticket ID with set_ticket_id(<ticket_id>)"
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)

        if not name:
            name = file_name

        url = '{}/api/now/attachment/file?table_name={}&table_sys_id={}&file_name={}'.format(self.url, self.project,
                                                                                             self.sys_id, name)
        try:
            with open(file_name, 'rb') as f:
                data = f.read()
            r = self.s.post(url, data=data)
            logger.debug("Add attachment: status code: {0}".format(r.status_code))
            r.raise_for_status()
            logger.info("Attached file {0} to ticket {1} - {2}".format(file_name, self.ticket_id, self.ticket_url))
            return self.request_result
        except requests.RequestException as e:
            logger.error("Error attaching file {0}".format(file_name))
            logger.error(e)
            return self.request_result._replace(status='Failure', error_message=str(e))
        except IOError:
            error_message = "File {0} not found".format(file_name)
            logger.error(error_message)
            return self.request_result._replace(status='Failure', error_message=error_message)


def _prepare_ticket_fields(fields):
    """
    Makes sure each key value pair in the fields dictionary is in
    the correct form.
    :param fields: Ticket fields.
    :return: fields: Ticket fields for the ticketing tool.
    """
    for key, value in fields.items():
        if key in ['opened_for', 'operating_system', 'category', 'item',
                   'severity', 'hostname_affected', 'opened_by_dept']:
            fields['u_{}'.format(key)] = value
            fields.pop(key)
        if key == 'topic':
            fields['u_topic_reportable'] = value
            fields.pop(key)
        if key == 'email_from':
            fields['u_email_from_address'] = value
            fields.pop(key)
    return fields


def main():
    """
    main() function, not directly callable.
    :return:
    """
    print('Not directly executable')


if __name__ == '__main__':
    main()

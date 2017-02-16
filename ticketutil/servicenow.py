"""
ServiceNow ticket

Provided, you have user and pwd, you can create new ticket like this,
but you should need other attributes like Category, Item and other non-optional
attributes from the ServiceNow web GUI.

TODO:
api PATCH method would enable editing comment
api DELETE method - maybe, not that necessary
"""


import logging
import os

import requests

from . import ticket

# TODO ask dranck about credits
__author__ = 'dranck, rnester, kshirsal, pzubaty'

# Disable warnings for requests because we aren't doing certificate
# verification
requests.packages.urllib3.disable_warnings()

DEBUG = os.environ.get('TICKETUTIL_DEBUG', 'False')

if DEBUG == 'True':
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


class ServiceNowTicket(ticket.Ticket):
    """
    ServiceNow Ticket object. Contains ServiceNow specific methods for working
    with tickets.
    """

    def __init__(self, url, project, auth=None, ticket_id=None):
        """
        :param url: ServiceNow service url
        :param project: ServiceNow table or project
        :param auth: (<username>, <password>) for HTTP Basic Authentication
        :param ticked_id: ticked number, eg. PNT1234567
        """
        self.ticketing_tool = 'ServiceNow'
        self.sys_id = None

        # The auth param should be of the form (<username>, <password>) for
        # HTTP Basic authentication.
        self.url = url
        self.auth = auth
        self.table = project
        self.rest_url = '{0}/api/now/v1/table/{1}'.format(self.url, self.table)
        self.auth_url = self.rest_url

        # parent creates request session, ticket_id beforehand causes failure
        super(ServiceNowTicket, self).__init__(project, ticket_id=None)
        if ticket_id:
            self.sys_id = self._get_sys_id()
            super(ServiceNowTicket, self).set_ticket_id(ticket_id)

    def _get_sys_id(self):
        """
        Get sys_id from ticket_id

        :return: sys_id - hashcode identifier in the ticket URL
        """
        try:
            self.s.headers.update({'Content-Type': 'application/json'})
            url = self.rest_url + '?sysparm_query=GOTOnumber%3D'
            url += self.ticket_id
            r = self.s.get(url)
            r.raise_for_status()

            logging.debug("Get sys_id: Status Code: {0}".format(r.status_code))
            ticket_content = r.json()
            return ticket_content['result'][0]['sys_id']
        except:
            requests.RequestException as e:
            logging.error("Error while getting sys_id")
            logging.error(e.args[0])

    def _generate_ticket_url(self):
        """
        Generates the ticket URL out of the url, project, and ticket_id.

        :return: ticket_url: The URL of the ticket.
        """
        ticket_url = None

        # If we are receiving a ticket_id, we have sys_id
        if self.sys_id:
            ticket_url = '{0}/{1}.do?sys_id={2}'.format(self.url, self.table,
                                                        self.sys_id)
        return ticket_url

    def create(self, short_description, description, category, item, **kwargs):
        """
        Creates new issue, new record in the ServiceNow table

        :param short_description: short description of the issue
        :param description: full description of the issue
        :param u_category: ticket category (Category in WebUI)
        :param u_item: ticket category item (Item in WebUI)

        :param kwargs: optional fields

        Fields example:
        'contact_type': 'Email',
        'u_opened_for': 'PNT',
        'assigned_to': 'pzubaty',
        'impact': '2',
        'urgency': '2',
        'priority': '2'
        """
        fields = {'description': description,
                  'short_description': short_description,
                  'u_category': category,
                  'u_item': item}
        kwargs.update(fields)
        params = self._create_ticket_parameters(kwargs)
        self._create_ticket_request(params)

    def _create_ticket_parameters(self, fields):
        """
        Creates the payload for the POST request when creating new ticket.

        :param fields: optional fields
        """
        params = ''
        for key, value in kwargs.items():
            params += ', "{}" : "{}"'.format(key, value)
        params = '{' + params[1:] + '}'
        return params

    def _create_ticket_request(self, params):
        """
        Tries to create the ticket through the ticketing tool's API.
        Retrieves the ticket_id and creates the ticket_url.

        :param params: The payload to send in the POST request.
        """
        try:
            self.s.headers.update({'Content-Type': 'application/json',
                                'Accept': 'application/json'})
            r = self.s.post(self.rest_url, data=params)
            r.raise_for_status()

            logging.debug("Create ticket: Status Code: {0}".format(r.status_code))
            ticket_content = r.json()
            ticket_content = ticket_content['result']

            self.ticket_id = ticket_content['number']
            self.sys_id = ticket_content['sys_id']
            self.ticket_url = self._generate_ticket_url()
            logging.info('Create ticket {0} - {1}'.format(self.ticket_id,
                                                          self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error creating ticket")
            logging.error(e.args[0])

    def change_status(self, status):
        """
        Change ServiceNow ticket status

        :param status: State to change to
        """
        if not self.sys_id:
            logging.error('No ticket ID associated with ticket object. Set '
                          'ticket ID with set_ticket_id(ticket_id)')
            return

        try:
            logging.info('Changing ticket status')
            fields = {'state': status}
            self.edit(**fields)
        except:
            logging.error('Failed to change ticket status')

    def edit(self, **kwargs):
        """
        Edit ticket

        Edits a ServiceNow ticket, ticked_id (sys_id) must be set beforehand.
        You can set ticket_id by calling set_ticket_id(ticket_id) method.

        :param kwargs: optional fields

        Fields example:
        'contact_type' : 'Email',
        'u_opened_for' : 'PNT',
        'assigned_to' : 'pzubaty',
        'impact' : '2',
        'urgency' : '2',
        'priority' : '2'
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set "
                          "ticket ID with set_ticket_id(ticket_id)")
            return
        params = self._create_ticket_parameters(kwargs)

        try:
            self.s.headers.update({'Content-Type': 'application/json',
                                   'Accept': 'application/json'})
            url = self.rest_url + '/' + self.sys_id
            r = self.s.put(url, data=params)
            r.raise_for_status()
            logging.debug("Editing Ticket: Status Code: {0}"
                          .format(r.status_code))
            logging.info("Edited ticket {0} - {1}".format(self.ticket_id,
                                                          self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error editing ticket")
            logging.error(e.args[0])

    def add_comment(self, comment):
        """
        Adds comment

        :param comment: new ticket comment
        """
        try:
            logging.info('Adding comment')
            fields = {'comments': comment}
            self.edit(**fields)
        except:
            logging.error('Failed to add the comment')


def main():
    """
    main() function, not directly callable.
    :return:
    """
    print('Not directly executable')


if __name__ == '__main__':
    main()

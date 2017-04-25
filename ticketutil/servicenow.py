import os
import logging
import requests
import json

from ticketutil.ticket import Ticket

__author__ = 'dranck, rnester, kshirsal, pzubaty'

STATE = {'new':'0',
         'open':'1',
         'work in progress':'2',
         'pending':'-6',
         'pending approval':'-9',
         'pending customer':'-1',
         'pending change':'-4',
         'pending vendor':'-5',
         'resolved':'5',
         'closed completed':'3',
         'closed cancelled':'8'}


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
        :param ticked_id: ticked number, eg. 'PNT1234567'
        """
        self.ticketing_tool = 'ServiceNow'

        # The auth param should be of the form (<username>, <password>) for
        # HTTP Basic authentication.
        self.url = url
        self.auth = auth
        self.project = project
        self.rest_url = '{0}/api/now/v1/table/{1}'.format(self.url, self.project)
        self.auth_url = self.rest_url
        self.headers_post_ = {'Content-Type': 'application/json',
                              'Accept': 'application/json'}
        # Call our parent class's init method which creates our requests session.
        super(ServiceNowTicket, self).__init__(project, ticket_id)

    def _verify_project(self, project):
        """
        Queries the ServiceNow API to see if project is a valid table for
        the given ServiceNow instance.
        :param project: The project table you're verifying.
        :return: True or False depending on if project is valid.
        """
        try:
            r = self.s.get('{0}?sysparm_limit=1'.format(self.rest_url))
            logging.debug("Verify project: Status Code: {0}".format(r.status_code))
            r.raise_for_status()
            logging.debug("Project {0} is valid".format(project))
            return True
        except requests.RequestException as e:
            logging.error("Unexpected error occurred when verifying project.")
            logging.error(e.args)
            return False

    def get_ticket_content(self, ticket_id=None):
        """
        Get ticket_content using ticket_id

        :param ticked_id: ticked number, if not set self.ticket_id is used
        :return: ticket content
        """
        if ticket_id is None:
            ticket_id = self.ticket_id
        try:
            self.s.headers.update({'Content-Type': 'application/json'})
            url = self.rest_url + '?sysparm_query=GOTOnumber%3D'
            url += ticket_id
            r = self.s.get(url)
            r.raise_for_status()

            logging.debug("Get ticket content: Status Code: {0}"
                          .format(r.status_code))
            ticket_content = r.json()
            return ticket_content['result'][0]
        except requests.RequestException as e:
            logging.error("Error while getting ticket content")
            logging.error(e.args)
            return False

    def _verify_ticket_id(self, ticket_id):
        """
        Queries the ServiceNow API to see if ticket_id is a valid ticket for
        the given ServiceNow instance.
        :param ticket_id: The ticket you're verifying.
        :return: True or False depending on if ticket is valid.
        """
        try:
            result = self.get_ticket_content(ticket_id)
            if not result:
                raise requests.RequestException
            else:
                logging.debug("Ticket {0} is valid".format(ticket_id))
                self.ticket_id = ticket_id
                self.ticket_content = result
                self.sys_id = self.ticket_content['sys_id']
                self.ticket_rest_url = self.rest_url + '/' + self.sys_id
                return True
        except requests.RequestException as e:
            logging.error("Ticket {0} is not valid.".format(ticket_id))
            logging.error(e.args)
            return False

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
        """
        msg = 'is a mandatory parameter for ticket creation.'
        if description is None:
            logging.error('description {}'.format(msg))
            return
        if short_description is None:
            logging.error('short_description {}'.format(msg))
            return
        if category is None:
            logging.error('category {}'.format(msg))
            return
        if item is None:
            logging.error('item {}'.format(msg))
            return

        self.ticket_content = None
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
        fields = self._prepare_ticket_fields(fields)

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
        """
        try:
            self.s.headers.update(self.headers_post_)
            r = self.s.post(self.rest_url, data=params)
            r.raise_for_status()

            logging.debug("Create ticket: Status Code: {0}"
                          .format(r.status_code))
            ticket_content = r.json()
            self.ticket_content = ticket_content['result']

            self.ticket_id = self.ticket_content['number']
            self.sys_id = self.ticket_content['sys_id']
            self.ticket_url = self._generate_ticket_url()
            self.ticket_rest_url = self.rest_url + '/' + self.sys_id
            logging.info('Create ticket {0} - {1}'.format(self.ticket_id,
                                                          self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error creating ticket")
            logging.error(e.args)

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
            params = self._create_ticket_parameters({'state':STATE[status.lower()]})
            self.s.headers.update(self.headers_post_)
            r = self.s.put(self.ticket_rest_url, data=params)
            r.raise_for_status()
            self.ticket_content = r.json()['result']
            logging.info('Ticket {0} status changed successfully'
                         .format(self.ticket_id))
        except requests.RequestException as e:
            logging.error('Failed to change ticket status')
            return False

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
        """
        if not self.ticket_id:
            logging.error("No ticket ID associated with ticket object. Set "
                          "ticket ID with set_ticket_id(ticket_id)")
            return
        params = self._create_ticket_parameters(kwargs)

        try:
            self.s.headers.update(self.headers_post_)
            r = self.s.put(self.ticket_rest_url, data=params)
            r.raise_for_status()
            self.ticket_content = r.json()['result']
            logging.debug("Editing Ticket: Status Code: {0}"
                          .format(r.status_code))
            logging.info("Edited ticket {0} - {1}".format(self.ticket_id,
                                                          self.ticket_url))
        except requests.RequestException as e:
            logging.error("Error editing ticket")
            logging.error(e.args)
            return False

    def add_comment(self, comment):
        """
        Adds comment

        :param comment: new ticket comment
        """
        try:
            logging.info('Adding comment to {0}'.format(self.ticket_id))
            params = self._create_ticket_parameters({'comments' : comment})
            self.s.headers.update(self.headers_post_)
            r = self.s.put(self.ticket_rest_url, data=params)
            r.raise_for_status()
            self.ticket_content = r.json()['result']
            logging.info('Comment created successfully')
        except requests.RequestException as e:
            logging.error('Failed to add the comment')
            return False

    def add_cc(self, user):
        """
        Adds user(s) to cc list.
        :param user: A string representing one user's email address, or a list
        of strings for multiple users.
        :return:
        """
        try:
            logging.info('Adding user(s) to CC list')
            watch_list = self.ticket_content['watch_list'].split(',')
            watch_list = [item.strip() for item in watch_list]
            if isinstance(user, str):
                user = [user]
            for item in user:
                if item not in watch_list:
                    watch_list.append(item)

            fields = {'watch_list' : ', '.join(watch_list)}
            params = self._create_ticket_parameters(fields)
            self.s.headers.update(self.headers_post_)
            r = self.s.put(self.ticket_rest_url, data=params)
            r.raise_for_status()
            self.ticket_content = r.json()['result']
            logging.info('Users added to CC list of {0}'
                         .format(self.ticket_id))
        except requests.RequestException as e:
            logging.error('Failed to add user(s) to CC list')
            return False

    def rewrite_cc(self, user):
        """
        Rewrites user(s) in cc list.
        :param user: A string representing one user's email address, or a list
        of strings for multiple users.
        :return:
        """
        try:
            logging.info('Rewriting CC list')
            if isinstance(user, str):
                user = [user]

            fields = {'watch_list' : ', '.join(user)}
            params = self._create_ticket_parameters(fields)
            self.s.headers.update(self.headers_post_)
            r = self.s.put(self.ticket_rest_url, data=params)
            r.raise_for_status()
            self.ticket_content = r.json()['result']
            logging.info('CC list rewritten for {0}'
                         .format(self.ticket_id))
        except requests.RequestException as e:
            logging.error('Failed to rewrite CC list')
            return False

    def remove_cc(self, user):
        """
        Removes user(s) from cc list.
        :param user: A string representing one user's email address, or a list
        of strings for multiple users.
        :return:
        """
        try:
            logging.info('Removing user(s) from CC list')
            watch_list = self.ticket_content['watch_list'].split(',')
            watch_list = [item.strip() for item in watch_list]
            if isinstance(user, str):
                user = [user]
            for item in user:
                if item in watch_list:
                    watch_list.remove(item)

            fields = {'watch_list' : ', '.join(watch_list)}
            params = self._create_ticket_parameters(fields)
            self.s.headers.update(self.headers_post_)
            r = self.s.put(self.ticket_rest_url, data=params)
            r.raise_for_status()
            self.ticket_content = r.json()['result']
            logging.info('User(s) removed from CC list of {0}'
                         .format(self.ticket_id))
        except requests.RequestException as e:
            logging.error('Failed to remove user(s) from CC list')
            return False

    def _prepare_ticket_fields(self, fields):
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


    def devops_one_url(self):
        """
        Creates DevOps One URL of the existing ticket
        """
        return '{server}/pnt/?id=ticket&sys_id={sys_id}&table={table}'.format(
                server=self.url, sys_id=self.sys_id, table=self.project)


def test():
    table = 'x_redha_pnt_devops_table'
    server = 'https://redhat.service-now.com'
    # server = 'https://redhatqa.service-now.com'
    # user = 'pnt_test_api'
    user = 'pnt_ticketutil_api'
    f = open('/etc/servicenow-pass.conf')
    pwd = f.readline()[:-1] # move to system env instead
    auth = (user,pwd)

    ticket = ServiceNowTicket(server, table, auth)
    description = ('This is just a simple test for ticketutil library. Calling'
                   'ServiceNowTicket class you are able to create tickets in '
                   'the ServiceNow automatically.\\n You need however to provide '
                   'username and password (at the moment only basic auth is '
                   'supported. Module created by pzubaty@redhat.com')

    ticket.create(short_description='TEST adding ServiceNow API into ticketutil',
                  description=description,
                  category='Communication',
                  item='ServiceNow')
    pnt_url = ticket.devops_one_url()
    logging.info('Ticket in DevOps One: {}'.format(pnt_url))
    ticket.close_requests_session()


def test_comment(ticket_id):
    table = 'x_redha_pnt_devops_table'
    server = 'https://redhat.service-now.com'
    # server = 'https://redhatqa.service-now.com'
    # user = 'pnt_test_api'
    user = 'pnt_ticketutil_api'
    f = open('/etc/servicenow-pass.conf')
    pwd = f.readline()[:-1]
    auth = (user,pwd)

    ticket = ServiceNowTicket(server, table, auth, ticket_id)
    ticket.add_comment('This is test of adding CC to ServiceNow ticket,\n sorry for incovenience. "quotation test"')
    ticket.edit(assigned_to = 'pzubaty', priority = '3',
                email_from = 'pzubaty@redhat.com', category='Application',
                hostname_affected = '127.0.0.1')
    # ticket.rewrite_cc(['pzubaty@redhat.com', 'dranck@redhat.com'])
    ticket.remove_cc(['dranck@redhat.com', 'dranck.com'])
    ticket.add_cc('pzubaty@redhat.com')
    ticket.change_status('Pending')
    ticket.close_requests_session()


def main():
    """
    main() function, not directly callable.
    :return:
    """
    print('Not directly executable')


if __name__ == '__main__':
    main()

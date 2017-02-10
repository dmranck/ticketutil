import logging
import os

import requests

from . import ticket

#TODO ask dranck about credits
__author__ = 'dranck, rnester, kshirsal, pzubaty'

# Disable warnings for requests because we aren't doing certificate verification
requests.packages.urllib3.disable_warnings()

DEBUG = os.environ.get('TICKETUTIL_DEBUG', 'False')

if DEBUG == 'True':
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


class ServiceNowTicket(ticket.Ticket):
    """
    ServiceNow Ticket object. Contains ServiceNow specific methods for working with tickets.
    """
    def __init__(self, url, project, auth=None, ticket_id=None):
        self.ticketing_tool = 'ServiceNow'

        # The auth param should be of the form (<username>, <password>) for HTTP Basic authentication.
        self.url = url
        self.auth = auth
        self.table = project
        self.rest_url = '{0}/api/now/v1/table/{1}'.format(self.url, self.table)
        self.auth_url = self.rest_url

        super(ServiceNowTicket, self).__init__(project, ticket_id)

        # OK for GET, but will it blend? Accept part might be needed later
        self.s.headers.update({'Content-Type': 'application/json'})


    def process_response(self, response):
        """
        Helper function to process Requests response or raise exception
        """
        try:
            if (response.status_code != 201 and
                response.status_code != 200):
                raise
            result = response.json()['result']
            return result
        except:
            logging.error('Headers: {0}'.format(response.headers))
            logging.error('Error Response: {0}'.format(response.json()))


    def api_get(self, url):
        """
        API GET wrapper
        """
        self.s.headers.update({'Content-Type': 'application/json'})
        response = self.s.get(url)
        logging.debug("GET request Status Code: {0}"
                      .format(response.status_code))
        return process_response(response)


    def api_post(self, url, data):
        """
        API POST wrapper
        :param text: text to be inserted into table record
        """
        self.s.headers.update({"Content-Type":"application/json",
                               "Accept":"application/json"})
        response = self.s.post(url, data=data)
        logging.debug("POST request Status Code: {0}"
                      .format(response.status_code))
        return process_response(response)


    def api_put(self, url, data):
        """
        API PUT wrapper
        Updates table content.
        :param text: text to be inserted into table record
        """
        self.s.headers.update({"Content-Type":"application/json",
                               "Accept":"application/json"})
        response = self.s.put(url, data=data)
        logging.debug("PUT request Status Code: {0}"
                      .format(response.status_code))
        return process_response(response)


    def get_sys_id(self):
        """
        """
        url = self.rest_url + '?sysparm_query=GOTOnumber%3D'
        url += self.ticket_id
        result = api_get(url)
        return result[0]['sys_id']


    def _generate_ticket_url(self):
        """
        Generates the ticket URL out of the url, project, and ticket_id.
        :return: ticket_url: The URL of the ticket.
        """
        ticket_url = None

        # If we are receiving a ticket_id, set ticket_url.
        if self.ticket_id:
            self.sys_id = get_sys_id() if not self.sys_id
            ticket_url = "{0}/{1}.do?sys_id={2}".format(self.url, self.table,
                                                        self.sys_id)
        return ticket_url


    def create(self, short_description, **kwargs):
        """
        Creates new issue, new record in the ServiceNow table

        The required parameter is short description of the issue.
        Keyword arguments are used for other issue fields.

        :param short_description: short description of the issue
        """
        if short_description None:
            logging.error("short_description "
                          "is a necessary parameter for ticket creation.")
            return

        params = self._create_ticket_parameters(short_description, kwargs)
        self._create_ticket_request(params)


    def _create_ticket_parameters(self, short_description, fields):
        """
        """
        params = '{"short_description" : "{}"'.format(short_description)
        for key, value in fields.items():
            params += ', "{}" : "{}"'.format(key.title(), value)
        params += '}'


    def _create_ticket_request(self, params):
        """
        """
        result = self.api_post(self.rest_url, params)
        self.ticket_id = result['number']
        self.sys_id = result['sys_id']
        self.ticket_url = self._generate_ticket_url()
        logging.info("Created issue {0} - {1}".format(self.ticket_id,
                                                      self.ticket_url)


    def add_comment(self, comment):
        """
        """
        if not self.sys_id:
            logging.error("Attribute sys_id needs before calling add_comment.")
            return

        url = self.rest_url + "/" + self.sys_id
        data = '{"comments" : "' + comment + '" }'
        result = api_put(url, data)
        if result['number']:
            logging.info("Added comment to issue {0} - {1}"
                         .format(self.ticket_id, self.ticket_url))
        else:
            logging.error("Error adding comment to issue")


    # TODO
    # def change_status(self, status):
    # def edit(self, **kwargs):


def main():
    """
    main() function, not directly callable.
    :return:
    """
    print("Not directly executable")


if __name__ == "__main__":
    main()

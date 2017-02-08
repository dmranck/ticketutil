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
        self.rest_url = '{0}/api/now/v1/table/{1}'.format(self.url, project)
        self.auth_url = self.rest_url

        super(ServiceNowTicket, self).__init__(project, ticket_id)

        # OK for GET, but will it blend? Accept part might be needed later
        self.s.headers.update({'Content-Type': 'application/json'})


    def _generate_ticket_url(self):


    def create(self, short_description, fields):


    def _create_ticket_parameters(self ):


    def _create_ticket_request(self, params):


    def edit(self, **kwargs):


    def add_comment(self, comment):


def change_status(self, status):


def main():
    """
    main() function, not directly callable.
    :return:
    """
    print("Not directly executable")


if __name__ == "__main__":
main()

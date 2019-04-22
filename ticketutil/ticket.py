import logging
from collections import namedtuple

import gssapi
import requests
from requests_kerberos import HTTPKerberosAuth, DISABLED

__author__ = 'dranck, rnester, kshirsal'

# Disable warnings for requests because we aren't doing certificate verification
requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)


class TicketException(Exception):
    """An issue occurred when performing a ticketing operation."""


class Ticket(object):
    """
    A class representing a ticket.
    """
    def __init__(self, project, ticket_id):
        self.project = project
        self.ticket_id = ticket_id
        self.ticket_url = None

        # Create our default namedtuple for our request results.
        Result = namedtuple('Result', ['status', 'error_message', 'url', 'ticket_content'])
        self.request_result = Result('Success', None, None, None)

        # Create our requests session below. Raise an exception if a session object is not returned.
        self.s = self._create_requests_session()
        if not self.s:
            raise TicketException("Error authenticating to {0}".format(self.auth_url))

        # Verify that project is valid.
        if not self._verify_project(self.project):
            raise TicketException("Project {0} is not valid".format(self.project))

        # Verify that optional ticket_id parameter is valid. If valid, generate ticket_url.
        if self.ticket_id:
            if not self._verify_ticket_id(self.ticket_id):
                raise TicketException("Ticket {0} is not valid".format(self.ticket_id))
            else:
                self.ticket_url = self._generate_ticket_url()

    def _verify_ticket_id(self, ticket_id):
        """
        Check if ticket_id is connected with valid ticket for the given ticketing tool instance.
        :param ticket_id: The ticket you're verifying.
        :return: True or False depending on if ticket is valid.
        """
        result = self.get_ticket_content(ticket_id)
        if 'Failure' in result.status:
            logger.error("Ticket {0} is not valid".format(ticket_id))
            return False
        logger.debug("Ticket {0} is valid".format(ticket_id))
        self.ticket_id = ticket_id
        return True

    def set_ticket_id(self, ticket_id):
        """
        Sets the ticket_id and ticket_url instance vars for the current Ticket object.
        :param ticket_id: Ticket id you would like to set.
        :return: self.request_result: Named tuple containing status, error_message, and url info.
        """
        if self._verify_ticket_id(ticket_id):
            self.ticket_id = ticket_id
            self.ticket_url = self._generate_ticket_url()
            logger.info("Current ticket: {0} - {1}".format(self.ticket_id, self.ticket_url))
            return self.request_result
        else:
            logger.error("Unable to set ticket id to {0}".format(ticket_id))
            error_message = "Ticket ID not valid"
            return self.request_result._replace(status='Failure', error_message=error_message)

    def get_ticket_id(self):
        """
        Returns the ticket_id for the current Ticket object.
        :return: self.ticket_id: The ID of the ticket.
        """
        logger.info("Returned ticket id: {0}".format(self.ticket_id))
        return self.ticket_id

    def get_ticket_url(self):
        """
        Returns the ticket_url for the current Ticket object.
        :return: self.ticket_url: The URL of the ticket.
        """
        logger.info("Returned ticket url: {0}".format(self.ticket_url))
        return self.ticket_url

    def _create_requests_session(self):
        """
        Creates a Requests Session and authenticates to base API URL with kerberos-requests.
        We're using a Session to persist cookies across all requests made from the Session instance.
        :return s: Requests Session.
        """
        # TODO: Support other authentication methods.
        # Set up authentication for requests session.
        s = requests.Session()
        if self.auth == 'kerberos':
            self.principal = _get_kerberos_principal()
            s.auth = HTTPKerberosAuth(mutual_authentication=DISABLED)
            s.verify = False
        if isinstance(self.auth, tuple):
            s.auth = self.auth
            s.verify = False

        # Try to authenticate to auth_url.
        try:
            r = s.get(self.auth_url)
            logger.debug("Create requests session: status code: {0}".format(r.status_code))
            r.raise_for_status()
            logger.info("Successfully authenticated to {0}".format(self.ticketing_tool))
            return s
        except requests.RequestException as e:
            logger.error("Error authenticating to {0}".format(self.auth_url))
            logger.error(e)
            s.close()

    def close_requests_session(self):
        """
        Closes requests session for Ticket object.
        :return:
        """
        if self.s:
            self.s.close()
            return self.request_result


def _get_kerberos_principal():
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

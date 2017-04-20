import logging
import os

import gssapi
import requests
from requests_kerberos import HTTPKerberosAuth, DISABLED

__author__ = 'dranck, rnester, kshirsal'

# Disable warnings for requests because we aren't doing certificate verification
requests.packages.urllib3.disable_warnings()

LOG_LEVEL = os.environ.get('TICKETUTIL_LOG_LEVEL', 'INFO')

if LOG_LEVEL == 'DEBUG':
    logging.basicConfig(level=logging.DEBUG)
elif LOG_LEVEL == 'INFO':
    logging.basicConfig(level=logging.INFO)
elif LOG_LEVEL == 'WARNING':
    logging.basicConfig(level=logging.WARNING)
elif LOG_LEVEL == 'ERROR':
    logging.basicConfig(level=logging.ERROR)
elif LOG_LEVEL == 'CRITICAL':
    logging.basicConfig(level=logging.CRITICAL)


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

        # Create our requests session below. Raise an exception if a session object is not returned.
        self.s = self._create_requests_session()
        if not self.s:
            raise TicketException("Error authenticating to {0}.".format(self.auth_url))

        # Verify that project is valid.
        if not self._verify_project(self.project):
            raise TicketException("Project {0} is not valid.".format(self.project))

        # Verify that optional ticket_id parameter is valid. If valid, generate ticket_url.
        if self.ticket_id:
            if not self._verify_ticket_id(self.ticket_id):
                raise TicketException("Ticket {0} is not valid.".format(self.ticket_id))
            else:
                self.ticket_url = self._generate_ticket_url()

    def set_ticket_id(self, ticket_id):
        """
        Sets the ticket_id and ticket_url instance vars for the current Ticket object.
        :param ticket_id: Ticket id you would like to set.
        :return:
        """
        if self._verify_ticket_id(ticket_id):
            self.ticket_id = ticket_id
            self.ticket_url = self._generate_ticket_url()
            logging.info("Current ticket: {0} - {1}".format(self.ticket_id, self.ticket_url))
        else:
            logging.error("Unable to set ticket id to {0}.".format(ticket_id))

    def get_ticket_id(self):
        """
        Returns the ticket_id for the current Ticket object.
        :return: self.ticket_id: The ID of the ticket.
        """
        logging.info("Returned ticket id: {0}".format(self.ticket_id))
        return self.ticket_id

    def get_ticket_url(self):
        """
        Returns the ticket_url for the current Ticket object.
        :return: self.ticket_url: The URL of the ticket.
        """
        logging.info("Returned ticket url: {0}".format(self.ticket_url))
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

        # Try to authenticate to auth_url.
        try:
            r = s.get(self.auth_url)
            r.raise_for_status()
            logging.debug("Create requests session: Status Code: {0}".format(r.status_code))
            logging.info("Successfully authenticated to {0}".format(self.ticketing_tool))
            return s
        # We log an error if authentication was not successful, because rest of the HTTP requests will not succeed.
        # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
        except requests.RequestException as e:
            logging.error("Error authenticating to {0}.".format(self.auth_url))
            logging.error(e.args[0])
            s.close()

    def close_requests_session(self):
        """
        Closes requests session for Ticket object.
        :return:
        """
        if self.s:
            self.s.close()


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

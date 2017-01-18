import logging
import os

import gssapi
import requests
from requests_kerberos import HTTPKerberosAuth, DISABLED

__author__ = 'dranck, rnester, kshirsal'

# Disable warnings for requests because we aren't doing certificate verification
requests.packages.urllib3.disable_warnings()

DEBUG = os.environ.get('TICKETUTIL_DEBUG', 'False')

if DEBUG == 'True':
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


class Ticket(object):
    """
    A class representing a ticket.
    """
    def __init__(self, project, ticket_id):
        self.project = project
        self.ticket_id = ticket_id

        if self.ticket_id:
            self.ticket_url = self._generate_ticket_url()
        else:
            self.ticket_url = None

        # Create our requests session below.
        self.s = self._create_requests_session()

    def set_ticket_id(self, ticket_id):
        """
        Sets the ticket_id and ticket_url instance vars for the current ticket object.
        :param ticket_id: Ticket id you would like to set.
        :return:
        """
        self.ticket_id = ticket_id
        self.ticket_url = self._generate_ticket_url()

        logging.info("Current ticket: {0} - {1}".format(self.ticket_id, self.ticket_url))

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
        # We log an error if authentication was not successful, because rest of the HTTP requests will not succeed.
        # Instead of using e.message, use e.args[0] instead to prevent DeprecationWarning for exception.message.
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

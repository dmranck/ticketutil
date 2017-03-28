#!/usr/bin/env python

import base64
import urllib
import json

from ticketutil.bugzilla import BugzillaTicket
from requests.auth import HTTPBasicAuth

from local_settings import username, password, apikey

t = BugzillaTicket('https://beta-bugzilla.redhat.com',
                   'Red Hat Network',
                   auth=HTTPBasicAuth(username, password))

new_ticket = t.create(summary='Ticket Summary',
                      description="Example",
                      component='RHN/API',
                      version='_unset')


t.add_attachment(file_name="test_attachment.patch",
                 data=json.loads(base64.b64encode(open('/home/kumudini/Documents/Can-B-Erased/examples.txt', 'rb').read())),
                 summary="NEW_Attachment",
                 content_type="text/plain")

ticketutil
==========

.. image:: https://img.shields.io/badge/python-2.7%2C%203.3%2C%203.4%2C%203.5%2C%203.6-blue.svg
    :target: https://pypi.python.org/pypi/ticketutil/1.5.0

.. image:: https://img.shields.io/badge/pypi-v1.5.0-blue.svg
    :target: https://pypi.python.org/pypi/ticketutil/1.5.0

ticketutil is a Python module that allows you to easily interact with
various ticketing tools using their REST APIs. Currently, the supported
tools are JIRA, RT, Redmine, Bugzilla, and ServiceNow. All tools support
HTTP Basic authentication, while JIRA and RT also support Kerberos
authentication. Additionally, Bugzilla supports API key authentication and
Jira supports Personal Access Token authentication.

This module allows you to create tickets, add comments, edit ticket
fields, and change the status of tickets in each tool. Additional
lower-level tool-specific functions are supported - adding and removing
watchers in JIRA, adding attachments in JIRA, etc.

Simplify all of your ticketing operations with ticketutil:

.. code-block:: python

    from ticketutil.jira import JiraTicket
    ticket = JiraTicket(<jira_url>, <project_key>, auth='kerberos')

    # Create a ticket and perform some common ticketing operations.
    t = ticket.create(summary='Ticket summary',
                      description='Ticket description',
                      type='Task')
    t = ticket.add_comment('Test Comment')
    t = ticket.change_status('Done')

    # Check status of previous ticketing operation and print URL of ticket.
    print(t.status)
    print(t.url)

    # Close Requests session.
    ticket.close_requests_session()

Installation
------------

Install ticketutil with ``pip install ticketutil``.

ticketutil is compatible with Python 2.7, 3.3, 3.4, 3.5, and 3.6.
Note: For Python 2.6 and lower, an additional package, importlib, may
need to be installed.

If not installing with pip, a short list of packages defined in the
requirements.txt file need to be installed. To install the required
packages, type ``pip install -r requirements.txt``.

Documentation
-------------

Documentation for ticketutil is available at:
http://ticketutil.readthedocs.io.

Comments? / Questions? / Coming Soon
------------------------------------

For questions / comments, email dranck@redhat.com.
For anything specific to Bugzilla, email kshirsal@redhat.com.
For ServiceNow related questions, email pzubaty@redhat.com.

The plan for ticketutil is to support more ticketing tools in the near
future and to support more ticketing operations for the currently
supported tools. Please let us know if there are any suggestions /
requests.
Thanks!

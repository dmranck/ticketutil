ticketutil
==========

.. image:: https://img.shields.io/badge/python-2.7%2C%203.3%2C%203.4%2C%203.5%2C%203.6-blue.svg
    :target: https://pypi.python.org/pypi/ticketutil/1.0.4

.. image:: https://img.shields.io/badge/pypi-v1.0.4-blue.svg
    :target: https://pypi.python.org/pypi/ticketutil/1.0.4

ticketutil is a Python module that allows you to easily interact with 
various ticketing tools using their REST APIs. Currently, the supported 
tools are JIRA, RT, Redmine and Bugzilla.
Kerberos authentication is supported for JIRA and RT, while
HTTP Basic authentication is supported for Redmine and Bugzilla.

This module allows you to create tickets, add comments, edit ticket
fields, and change the status of tickets in each tool. Additional 
lower-level tool-specific functions are supported - adding and removing 
watchers in JIRA, adding attachments in JIRA, etc.

Simplify all of your ticketing operations with ticketutil:

.. code-block:: python

    from ticketutil.jira import JiraTicket
    t = JiraTicket(<jira_url>, <project_key>, auth='kerberos')

    # Create a ticket and perform some common ticketing operations.
    t.create(summary='Ticket summary',
             description='Ticket description')
    t.add_comment('Test Comment')
    t.change_status('Done')

    # Close Requests session.
    t.close_requests_session()

Installation
------------

Install ticketutil with ``pip install ticketutil``.

ticketutil is compatible with Python 2.7, 3.3, 3.4, 3.5, and 3.6.
Note: For Python 2.6 and lower, an additional package, importlib, may 
need to be installed.

If not installing with pip, a short list of packages defined in the 
requirements.txt file need to be installed. To install the required 
packages, type ``pip install -r requirements.txt``.

Usage
-----

Note: To enable debug logging for ticketutil, set an environment 
variable named TICKETUTIL_DEBUG to 'True'. If this environment variable
is set to anything else or does not exist, debug logging will be 
disabled.

The general usage workflow for creating new tickets is:

* Create a JiraTicket, RTTicket, RedmineTicket, or BugzillaTicket
  object with ``<url>``, ``<project>`` and ``<auth>``. This verifies that you
  are able to properly authenticate to the ticketing tool. For tools that
  require HTTP Basic Authentication (Redmine and Bugzilla), the ``<auth>``
  parameter should contain the username and password specified as a
  tuple. For tools that support kerberos authentication (JIRA and RT),
  the ``<auth>`` parameter should contain 'kerberos'.
* Create a ticket with the ``create()`` method. This sets the ``ticket_id``
  instance variable, allowing you to perform more tasks on the ticket.
* Add comments, edit ticket fields, add watchers, change the ticket
  status, etc on the ticket.
* Close ticket Requests session with ``close_requests_session()``.
 
To work on existing tickets, you can also pass in a fourth parameter 
when creating a Ticket object: ``<ticket_id>``. The general workflow for
working with existing tickets is as follows:

* Create a JiraTicket, RTTicket, RedmineTicket, or BugzillaTicket
  object with ``<url>``, ``<project_key>``, ``<auth>`` and ``<ticket_id>``.
* Add comments, edit ticket fields, add watchers, change the ticket
  status, etc on the ticket.
* Close ticket Requests session with ``close_requests_session()``.
 
There is also a ``set_ticket_id()`` method for a Ticket object. This is
useful if you are working with a Ticket object that already has the 
``<ticket_id>`` instance variable set, but would like to begin working
on a separate ticket. Instead of creating a new Ticket object, you can
simply pass an existing ``<ticket_id>`` in to the ``set_ticket_id()``
method to begin working on another ticket.

See the docstrings in the code or the tool-specific files in the docs
and examples directories for more information.

Comments? / Questions? / Coming Soon
------------------------------------

For questions / comments, email dranck@redhat.com. 
For anything specific to Bugzilla, email kshirsal@redhat.com.

The plan for ticketutil is to support more ticketing tools in the near 
future and to support more ticketing operations for the currently
supported tools. Please let us know if there are any suggestions / 
requests.
Thanks!

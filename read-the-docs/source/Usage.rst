Usage
=====

Create a Ticket object
----------------------

Create a JiraTicket, RTTicket, RedmineTicket, BugzillaTicket
or ServiceNowTicket object with ``<url>``, ``<project>`` and ``<auth>``. This
verifies that you are able to properly authenticate to the ticketing tool.
To use HTTP Basic Authentication, the ``<auth>`` parameter should contain the
username and password specified as a tuple. For tools that support kerberos
authentication (JIRA and RT), the ``<auth>`` parameter should contain
'kerberos'.


Work with a new ticket
----------------------

+ Create a ticket with the ``create()`` method. This sets the ``ticket_id``
  instance variable, allowing you to perform more tasks on the ticket.

+ Add comments, edit ticket fields, add watchers, change the ticket
  status, etc on the ticket.

+ Close ticket Requests session with ``close_requests_session()``.


Work with an existing ticket
----------------------------

There is also a ``set_ticket_id()`` method for a Ticket object. This is
useful if you are working with a Ticket object that already has the
``<ticket_id>`` instance variable set, but would like to begin working
on a separate ticket. Instead of creating a new Ticket object, you can
simply pass an existing ``<ticket_id>`` in to the ``set_ticket_id()``
method to begin working on another ticket.

+ To work on existing tickets, you can also pass in a fourth parameter
  when creating a Ticket object: ``<ticket_id>``. The general workflow for
  working with existing tickets is as follows:

+ Create a JiraTicket, RTTicket, RedmineTicket, BugzillaTicket
  or ServiceNowTicket object with ``<url>``, ``<project_key>``, ``<auth>`` and
  ``<ticket_id>``.

+ Add comments, edit ticket fields, add watchers, change the ticket
  status, etc on the ticket.

+ Close ticket Requests session with ``close_requests_session()``.

+ To return the current Ticket object's ticket_id or ticket_url, use the
  ``get_ticket_id()`` or ``get_ticket_url()`` methods.

.. seealso::

    See the docstrings in the code or the tool-specific sections in the documentation for more information on
    supported methods and examples.


Running unit tests
------------------

To run unit tests in Bash terminal use this command:

.. code-block:: python

    python3 -m unittest discover ./tests/


Return Statements
-----------------

The main user-accessible methods in ticketutil return the status of the method
(Success or Failure), the error message if the status is a Failure, and the
URL of the ticket. An example is below.

.. code-block:: python

    # Create Ticket object and create a ticket.
    ticket = JiraTicket(. . . .)
    t = ticket.create(. . . .)

    # View status of create(). Will either return 'Success' or 'Failure'.
    print(t.status)

    # View error message if status of create() is 'Failure'.
    print(t.error_message)

    # View URL of ticket.
    print(t.url)

    # Close Requests session.
    ticket.close_requests_session()

.. note::

    For JIRA, the ``remove_all_watchers()`` method returns a list of the
    watchers that were removed from the ticket. Access this data with
    ``t.watchers``.

.. note::

    For ServiceNow, Jira, Bugzilla and Redmine the user-accessible methods return a ``ticket_content``
    field, which contains a json representation of the current ticket's content.
    Access this data with ``t.ticket_content``.

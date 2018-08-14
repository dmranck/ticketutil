JIRA
====

This document contains information on the methods available when working
with a JiraTicket object. A list of the JIRA fields that have been
tested when creating and editing tickets is included. Because each
instance of JIRA can have custom fields and custom values, some of the
tested fields may not be applicable to certain instances of JIRA.
Additionally, your JIRA instance may contain ticket fields that we have
not tested. Custom field names and values can be passed in as keyword
arguments when creating and editing tickets, and the JIRA REST API
should be able to process them. See JIRA's REST API documentation for
more information on custom fields:
https://docs.atlassian.com/jira/REST/cloud/

Methods
^^^^^^^

-  `get_ticket_content() <#get_ticket_content>`__
-  `create() <#create>`__
-  `edit() <#edit>`__
-  `add_comment() <#comment>`__
-  `change_status() <#status>`__
-  `remove_all_watchers() <#remove_all_watchers>`__
-  `remove_watcher() <#remove_watcher>`__
-  `add_watcher() <#add_watcher>`__
-  `add_attachment() <#add_attachment>`__

get_ticket_content()
--------------------

``get_ticket_content(self, ticket_id=None)``

Queries the JIRA API to get ticket_content using ticket_id. The ticket_content
is expressed in a form of dictionary as a result of JIRA API's get issue:
https://docs.atlassian.com/software/jira/docs/api/REST/7.6.1/#api/2/issue-getIssue

.. code:: python

    t = ticket.get_ticket_content(<ticket_id>)
    returned_ticket_content = t.ticket_content

create()
--------

``create(self, summary, description, type, **kwargs)``

Creates a ticket. The required parameters for ticket creation are
summary, description and type. Keyword arguments are used for other ticket
fields.

.. code:: python

    t = ticket.create(summary='Ticket summary',
                      description='Ticket description',
                      type='Task')

The following keyword arguments were tested and accepted by our
particular JIRA instance during ticket creation:

.. code:: python

    summary='Ticket summary'
    description='Ticket description'
    priority='Major'
    type='Task'
    assignee='username'
    reporter='username'
    environment='Environment Test'
    duedate='2017-01-13'
    parent='KEY-XX'
    customfield_XXXXX='Custom field text'

While creating a Sub task, parent ticket id is required, otherwise create()
method fails with KeyError - "Parent field is required while creating a Sub
Task"

edit()
------

``edit(self, **kwargs)``

Edits fields in a JIRA ticket. Keyword arguments are used to specify
ticket fields.

.. code:: python

    t = ticket.edit(summary='Ticket summary')

The following keyword arguments were tested and accepted by our
particular JIRA instance during ticket editing:

.. code:: python

    summary='Ticket summary'
    description='Ticket description'
    priority='Major'
    type='Task'
    assignee='username'
    reporter='username'
    environment='Environment Test'
    duedate='2017-01-13'
    parent='KEY-XX'
    customfield_XXXXX='Custom field text'

add_comment()
-------------

``add_comment(self, comment)``

Adds a comment to a JIRA ticket.

.. code:: python

    t = ticket.add_comment('Test comment')

change_status()
---------------

``change_status(self, status)``

Changes status of a JIRA ticket.

.. code:: python

    t = ticket.change_status('In Progress')

remove_all_watchers()
---------------------

``remove_all_watchers(self)``

Removes all watchers from a JIRA ticket.

.. code:: python

    t = ticket.remove_all_watchers()

remove_watcher()
----------------

``remove_watcher(self, watcher)``

Removes watcher from a JIRA ticket. Accepts an email or username.

.. code:: python

    t = ticket.remove_watcher('username')

add_watcher()
-------------

``add_watcher(self, watcher)``

Adds watcher to a JIRA ticket. Accepts an email or username.

.. code:: python

    t = ticket.add_watcher('username')

add_attachment()
----------------

``add_attachment(self, file_name)``

Attaches a file to a JIRA ticket.

.. code:: python

    t = ticket.add_attachment('filename.txt')


Examples
^^^^^^^^

Create JIRATicket object
------------------------

Authenticate through HTTP Basic Authentication:

.. code:: python

    >>> from ticketutil.jira import JiraTicket
    >>> ticket = JiraTicket(<jira_url>,
                            <project_key>,
                            auth=('username', 'password'))

Authenticate through Kerberos after running ``kinit``:

.. code:: python

    >>> from ticketutil.jira import JiraTicket
    >>> ticket = JiraTicket(<jira_url>,
                            <project_key>,
                            auth='kerberos')

You should see the following response:

::

    INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): <jira_url>
    INFO:root:Successfully authenticated to JIRA

You now have a ``JiraTicket`` object that is associated with the
``<project_key>`` project.

Some example workflows are found below. Notice that the first step is to
create a JiraTicket object with a url and project key (and with a ticket
id when working with existing tickets), and the last step is closing the
Requests session with ``t.close_requests_session()``.

When creating a JIRA ticket, ``summary`` and ``description`` are
required parameters. Also, the Reporter is automatically filled in as
the current kerberos principal.

Note: The tested parameters for the create() and edit() methods are
found in the docstrings in the code and in the docs folder. Any other
ticket field can be passed in as a keyword argument, but be aware that
the value for non-tested fields or custom fields may be in a
non-intuitive format. See JIRA's REST API documentation for more
information: https://docs.atlassian.com/jira/REST/cloud/

Create and update JIRA ticket
-----------------------------

.. code:: python

    from ticketutil.jira import JiraTicket

    # Create a ticket object and pass the url and project key in as strings.
    ticket = JiraTicket(<jira_url>,
                        <project_key>,
                        auth='kerberos')

    # Create a ticket and perform some common ticketing operations.
    t = ticket.create(summary='Ticket summary',
                      description='Ticket description',
                      type='Task',
                      priority='Major',
                      assignee='username')
    t = ticket.get_ticket_content('Ticket_ID')
    t = ticket.add_comment('Test Comment')
    t = ticket.edit(priority='Critical',
                    type='Bug')
    t = ticket.remove_all_watchers()
    t = ticket.add_watcher('username')
    t = ticket.add_attachment('file_to_attach.txt')
    t = ticket.change_status('In Progress')

    # Close Requests session.
    ticket.close_requests_session()

Update existing JIRA tickets
----------------------------

.. code:: python

    from ticketutil.jira import JiraTicket

    # Create a ticket object and pass the url, project key, and ticket id in as strings.
    ticket = JiraTicket(<jira_url>,
                        <project_key>,
                        auth='kerberos',
                        ticket_id=<ticket_id>)

    # Perform some common ticketing operations.
    t = ticket.add_comment('Test Comment')
    t = ticket.edit(priority='Critical',
                    type='Bug')

    # Check the actual ticket content after applied updates
    t = ticket.get_ticket_content()
    returned_ticket_content = t.ticket_content

    # Work with a different ticket.
    t = ticket.set_ticket_id(<new_ticket_id>)
    t = ticket.remove_watcher('username')
    t = ticket.add_watcher('username')
    t = ticket.change_status('Done')

    # Close Requests session.
    ticket.close_requests_session()

Create a Sub-Task inside existing JIRA ticket
---------------------------------------------

.. code:: python

    from ticketutil.jira import JiraTicket

    # Create a ticket object and pass the url and project key in as strings.
    t = JiraTicket(<jira_url>,
                   <project_key>,
                   auth=('username', 'password'))

    # Create a ticket and perform some common ticketing operations.
    t.create(summary='Sub Task summary',
             description='Sub Task description',
             assignee='username',
             type='Sub-task',
             parent='existing_ticket_id')
    t.change_status('In Progress')

    # Close Requests session.
    t.close_requests_session()

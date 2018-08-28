Redmine
=======

This document contains information on the methods available when working
with a RedmineTicket object. A list of the Redmine fields that have been
tested when creating and editing tickets is included. Because each
instance of Redmine can have custom fields and custom values, some of
the tested fields may not be applicable to certain instances of Redmine.
Additionally, your Redmine instance may contain ticket fields that we
have not tested. Custom field names and values can be passed in as
keyword arguments when creating and editing tickets, and the Redmine
REST API should be able to process them. See Redmine's REST API
documentation for more information on custom fields:
http://www.redmine.org/projects/redmine/wiki/Rest\_api

Note: Redmine's REST API requires that you refer to many fields using
their 'id' values instead of their 'name's, including Project, Status,
Priority, and User. For these four fields, we have ``_get_<field>_id()``
methods, so you can use the name instead of having to look up the id.

Methods
^^^^^^^

-  `get_ticket_content() <#get_ticket_content>`__
-  `create() <#create>`__
-  `edit() <#edit>`__
-  `add_comment() <#comment>`__
-  `change_status() <#status>`__
-  `remove_watcher() <#remove_watcher>`__
-  `add_watcher() <#add_watcher>`__
-  `add_attachment() <#add_attachment>`__


get_ticket_content()
--------------------

``get_ticket_content(self, ticket_id=None)``

Queries the Redmine API to get ticket_content using ticket_id. The
ticket_content is expressed in a form of dictionary as a result of Redmine API's
get issue:
http://www.redmine.org/projects/redmine/wiki/Rest_Issues#Showing-an-issue

.. code:: python

    t = ticket.get_ticket_content(<ticket_id>)
    returned_ticket_content = t.ticket_content

create()
--------

``create(self, subject, description, **kwargs)``

Creates a ticket. The required parameters for ticket creation are
subject and description. Keyword arguments are used for other ticket
fields.

.. code:: python

    t = ticket.create(subject='Ticket subject',
                      description='Ticket description')

The following keyword arguments were tested and accepted by our
particular Redmine instance during ticket creation:

.. code:: python

    subject='Ticket subject'
    description='Ticket description'
    priority='Urgent'
    start_date='2017-01-20'
    due_date='2017-01-25'
    done_ratio='70'
    assignee='username@mail.com'


edit()
------

``edit(self, **kwargs)``

Edits fields in a Redmine ticket. Keyword arguments are used to specify
ticket fields.

.. code:: python

    t = ticket.edit(subject='Ticket subject')

The following keyword arguments were tested and accepted by our
particular Redmine instance during ticket editing:

.. code:: python

    subject='Ticket subject'
    description='Ticket description'
    priority='Urgent'
    start_date='2017-01-20'
    due_date='2017-01-25'
    done_ratio='70'
    assignee='username@mail.com'


add_comment()
-------------

``add_comment(self, comment)``

Adds a comment to a Redmine ticket.

.. code:: python

    t = ticket.add_comment('Test comment')


change_status()
---------------

``change_status(self, status)``

Changes status of a Redmine ticket.

.. code:: python

    t = ticket.change_status('Resolved')


remove_watcher()
----------------

``remove_watcher(self, watcher)``


Removes watcher from a Redmine ticket. Accepts an email or username.

.. code:: python

    t = ticket.remove_watcher('username')


add_watcher()
-------------

``add_watcher(self, watcher)``


Adds watcher to a Redmine ticket. Accepts an email or username.

.. code:: python

    t = ticket.add_watcher('username')


add_attachment()
----------------

``add_attachment(self, file_name)``


Attaches a file to a Redmine ticket.

.. code:: python

    t = ticket.add_attachment('filename.txt')


Examples
^^^^^^^^

Create RedmineTicket object
----------------------------

Currently, ticketutil supports HTTP Basic authentication for Redmine.
When creating a RedmineTicket object, pass in your username and password
as a tuple into the auth argument. You can also use an API key passed in
as a username with a random password for ``<password>``. For more
details, see
http://www.redmine.org/projects/redmine/wiki/Rest\_api#Authentication.

.. code:: python

    >>> from ticketutil.redmine import RedmineTicket
    >>> ticket = RedmineTicket(<redmine_url>,
                               <project_name>,
                               auth=(<username>, <password>))

You should see the following response:

::

    INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): <redmine_url>
    INFO:root:Successfully authenticated to Redmine

You now have a ``RedmineTicket`` object that is associated with the
``<project_name>`` project.

Some example workflows are found below. Notice that the first step is to
create a RedmineTicket object with a url and project key (and with a
ticket id when working with existing tickets), and the last step is
closing the Requests session with ``t.close_requests_session()``.

When creating a Redmine ticket, ``subject`` and ``description`` are
required parameters. Also, the Reporter is automatically filled in as
the current username.

Note: The tested parameters for the create() and edit() methods are
found in the docstrings in the code and in the docs folder. Any other
ticket field can be passed in as a keyword argument, but be aware that
the value for non-tested fields or custom fields may be in a
non-intuitive format. See Redmine's REST API documentation for more
information: http://www.redmine.org/projects/redmine/wiki/Rest\_api

Create and update Redmine ticket
--------------------------------

.. code:: python

    from ticketutil.redmine import RedmineTicket

    # Create a ticket object and pass the url and project name in as strings.
    ticket = RedmineTicket(<redmine_url>,
                           <project_name>,
                           auth=(<username>, <password>))

    # Create a ticket and perform some common ticketing operations.
    t = ticket.create(subject='Ticket subject',
                      description='Ticket description',
                      priority='Urgent',
                      start_date='2017-01-20',
                      due_date='2017-01-25',
                      done_ratio='70',
                      assignee='username@mail.com')
    t = ticket.add_comment('Test Comment')
    t = ticket.edit(priority='Normal',
                    due_date='2017-02-25')
    t = ticket.add_attachment('file_to_attach.txt')
    t = ticket.add_watcher('username1')
    t = ticket.remove_watcher('username2')
    t = ticket.change_status('Closed')

    # Close Requests session.
    ticket.close_requests_session()

Update existing Redmine tickets
-------------------------------

.. code:: python

    from ticketutil.redmine import RedmineTicket

    # Create a ticket object and pass the url, project name, and ticket id in as strings.
    ticket = RedmineTicket(<redmine_url>,
                           <project_name>,
                           auth=(<username>, <password>),
                           ticket_id=<ticket_id>)

    # Perform some common ticketing operations.
    t = ticket.add_comment('Test Comment')
    t = ticket.edit(priority='High',
                    done_ratio='90')

    # Check the ticket content.
    t = ticket.get_ticket_id()
    returned_ticket_content = t.ticket_content

    # Work with a different ticket.
    t = ticket.set_ticket_id(<new_ticket_id>)
    t = ticket.change_status('Resolved')

    # Close Requests session.
    ticket.close_requests_session()

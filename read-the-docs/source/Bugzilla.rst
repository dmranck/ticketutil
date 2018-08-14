Bugzilla
=========

This document contains information on the methods available when working
with a BugzillaTicket object. A list of the Bugzilla fields that have
been tested when creating and editing tickets is included. Because each
instance of Bugzilla can have custom fields and custom values, some of
the tested fields may not be applicable to certain instances of
Bugzilla. Additionally, your Bugzilla instance may contain ticket fields
that we have not tested. Custom field names and values can be passed in
as keyword arguments when creating and editing tickets, and the Bugzilla
REST API should be able to process them. See Bugzilla's REST API
documentation for more information on custom fields:
http://bugzilla.readthedocs.io/en/latest/api/index.html

Methods
^^^^^^^

-  `get_ticket_content() <#get_ticket_content>`__
-  `create() <#create>`__
-  `edit() <#edit>`__
-  `add_comment() <#comment>`__
-  `change_status() <#status>`__
-  `remove_cc() <#remove_cc>`__
-  `add_cc() <#add_cc>`__
-  `add_attachment() <#add_attachment>`__

get_ticket_content()
--------------------

``get_ticket_content(self, ticket_id=None)``

Queries the Bugzilla API to get ticket_content using ticket_id. The
ticket_content is expressed in a form of dictionary as a result of Bugzilla API's
get issue: http://bugzilla.readthedocs.io/en/latest/api/core/v1/bug.html#get-bug

.. code:: python

    t = ticket.create(ticket_id=<ticket_id>)
    returned_ticket_content = t.ticket_content

create()
--------

``create(self, summary, description, **kwargs)``

Creates a ticket. The required parameters for ticket creation are
summary and description. Keyword arguments are used for other ticket
fields.

.. code:: python

    t = ticket.create(summary='Ticket summary',
                      description='Ticket description')

The following keyword arguments were tested and accepted by our
particular Bugzilla instance during ticket creation:

.. code:: python

    summary='Ticket summary'
    description='Ticket description'
    assignee='username@mail.com'
    qa_contact='username@mail.com'
    component='Test component'
    version='version'
    priority='high'
    severity='medium'
    alias='SomeAlias'
    groups='GroupName'

edit()
------

``edit(self, **kwargs)``

Edits fields in a Bugzilla ticket. Keyword arguments are used to specify
ticket fields.

.. code:: python

    t = ticket.edit(summary='Ticket summary')

The following keyword arguments were tested and accepted by our
particular Bugzilla instance during ticket editing:

.. code:: python

    summary='Ticket summary'
    assignee='username@mail.com'
    qa_contact='username@mail.com'
    component='Test component'
    version='version'
    priority='high'
    severity='medium'
    alias='SomeAlias'
    groups='Group Name'

add_comment()
-------------

``add_comment(self, comment, **kwargs )``

Adds a comment to a Bugzilla ticket. Keyword arguments are used to
specify comment options.

.. code:: python

    t = ticket.add_comment('Test comment')

change_status()
---------------

``change_status(self, status, **kwargs)``

Changes status of a Bugzilla ticket. Some status changes require a
secondary field (i.e. resolution). Specify this as a keyword argument. A
resolution of Duplicate requires dupe\_of keyword argument with a valid
bug ID.

.. code:: python

    t = ticket.change_status('NEW')
    t = ticket.change_status('CLOSED', resolution='DUPLICATE', dupe_of='<bug_id>')

remove_cc()
-----------

``remove_cc(self, user)``

Removes user(s) from CC List of a Bugzilla ticket. Accepts a string
representing one user's email address, or a list of strings for multiple
users.

.. code:: python

    t = ticket.remove_cc('username@mail.com')

add_cc()
--------

``add_cc(self, user)``

Adds user(s) to CC List of a Bugzilla ticket. Accepts a string
representing one user's email address, or a list of strings for multiple
users.

.. code:: python

    t = ticket.add_cc(['username1@mail.com', 'username2@mail.com'])

add_attachment()
----------------

``add_attachment(self, file_name, data, summary, **kwargs )``

Add attachment in a Bugzilla ticket. Keyword arguments are used to
specify additional attachment options.

.. code:: python

    t = ticket.add_attachment(file_name='Name to be displayed on UI',
                              data='Location(path) or contents of the attachment',
                              summary='A short string describing the attachment.')

Examples
^^^^^^^^

Create BugzillaTicket object
----------------------------

Currently, ticketutil supports ``HTTP Basic authentication`` and
``API key authentication`` for Bugzilla.

While creating a bugzilla ticket you can pass in your username and
password as a tuple into the auth argument. The code then authenticates
for subsequent API calls. For more details, see:
http://bugzilla.readthedocs.io/en/latest/api/index.html.

.. code:: python

    >>> from ticketutil.bugzilla import BugzillaTicket
    >>> ticket = BugzillaTicket(<bugzilla_url>,
                                <product_name>,
                                auth=(<username>, <password>))

OR, you can use API key authentication. Before you use API key
authentication, you need to generate the API key for your account by
clicking on the API Keys section under your user preferences in
Bugzilla. When creating a BugzillaTicket object, you can pass in a
dictionary of the form {'api\_key': '} into the auth argument. The code
then authenticates for subsequent API calls. For more details, see:
http://bugzilla.readthedocs.io/en/latest/api/core/v1/general.html#authentication.

.. code:: python

    >>> from ticketutil.bugzilla import BugzillaTicket
    >>> ticket = BugzillaTicket(<bugzilla_url>,
                                <product_name>,
                                auth=({'api_key': '<your-api-key>'})

You now have a ``BugzillaTicket`` object that is associated with the
``<product_name>`` product.

Some example workflows are found below. Notice that the first step is to
create a BugzillaTicket object with a url and product name (and with a
ticket id when working with existing tickets), and the last step is
closing the Requests session with ``t.close_requests_session()``.

When creating a Bugzilla ticket, ``summary`` and ``description`` are
required parameters. Also, the Reporter is automatically filled in as
the current kerberos principal or username supplied during
authentication.

Note: The tested parameters for the create() and edit() methods are
found in the docstrings in the code and in the docs folder. Any other
ticket field can be passed in as a keyword argument, but be aware that
the value for non-tested fields or custom fields may be in a
non-intuitive format. See Bugzilla's REST API documentation for more
information: http://bugzilla.readthedocs.io/en/latest/api/index.html

Create and update Bugzilla ticket
---------------------------------

.. code:: python

    from ticketutil.bugzilla import BugzillaTicket

    # Create a ticket object and pass the url and product name in as strings.
    ticket = BugzillaTicket(<bugzilla_url>,
                            <product_name>,
                            auth=(<username>, <password>))

    # Create a ticket and perform some common ticketing operations.
    t = ticket.create(summary='Ticket summary',
                      description='Ticket description',
                      component='Test component',
                      priority='high',
                      severity='medium',
                      assignee='username@mail.com',
                      qa_contact='username@mail.com',
                      groups='beta')
    t = ticket.get_ticket_id()
    t = ticket.add_comment('Test Comment')
    t = ticket.edit(priority='medium',
                    qa_contact='username@mail.com')
    t = ticket.add_cc(['username1@mail.com', 'username2@mail.com'])
    t = ticket.remove_cc('username1@mail.com')
    t = ticket.change_status('Modified')

    # Close Requests session.
    ticket.close_requests_session()

Update existing Bugzilla tickets
--------------------------------

.. code:: python

    from ticketutil.bugzilla import BugzillaTicket

    # Create a ticket object and pass the url, product name, and ticket id in as strings.
    ticket = BugzillaTicket(<bugzilla_url>,
                            <product_name>,
                            auth=(<username>, <password>)
                            ticket_id=<ticket_id>)

    # Perform some common ticketing operations.
    t = ticket.add_comment('Test Comment')
    t = ticket.edit(priority='low',
                    severity='low',
                    groups='beta')

    t = ticket.add_attchment(file_name='test_attachment.patch',
                             data=<contents/file-location>,
                             summary=<summary describing attachment>)

    # Check the ticket content.
    t = ticket.get_ticket_id()
    returned_ticket_content = t.ticket_content

    # Work with a different ticket.
    t = ticket.set_ticket_id(<new_ticket_id>)
    t = ticket.change_status(status='CLOSED', resolution='NOTABUG')

    # Close Requests session.
    ticket.close_requests_session()

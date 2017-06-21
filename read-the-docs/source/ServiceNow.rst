Servicenow
==========

This document contains information on the methods available when working
with a ServiceNow object. A list of the ServiceNow fields that have been
tested when creating and editing tickets is included.

Note: Because each instance of ServiceNow can have custom fields and
custom values, some of the tested fields may not be applicable to
certain instances of ServiceNow. Additionally, your ServiceNow instance
may contain ticket fields that we have not tested. Keep in mind
different ServiceNow tables contain different fields with different
properties. Mandatory fields in one table may be optional or
non-existent in another table.

Custom field names and values can be passed in as keyword arguments when
creating and editing tickets. These are processed by the ServiceNow REST
API right afterwards. You can also use
`get\_ticket\_content <#content>`__ to get ticket content including
preset field names.

For more information about REST API and fields see ServiceNow's Wiki: -
`REST API <http://wiki.servicenow.com/index.php?title=REST_API>`__ -
`Introduction to
Fields <http://wiki.servicenow.com/index.php?title=Introduction_to_Fields>`__
-
`Dot-Walking <http://wiki.servicenow.com/index.php?title=Dot-Walking>`__


Methods
^^^^^^^

-  `set\_ticket\_id() <#set_ticket>`__
-  `create() <#create>`__
-  `get\_ticket\_content() <#content>`__
-  `edit() <#edit>`__
-  `add\_comment() <#comment>`__
-  `change\_status() <#status>`__
-  `add\_cc() <#add_cc>`__
-  `rewrite\_cc() <#rewrite_cc>`__
-  `remove\_cc() <#remove_cc>`__

set_ticket_id()
---------------

``set_ticket_id(self, ticket_id)``


Updates ticket content for the current ticket object. This ticket object
is assigned using ``ticket_id`` which is a string.

.. code:: python

    # switch to ticket 'ID0123456'
    t.set_ticket_id('ID0123456')

create()
--------

``create(self, short_description, description, category, item, **kwargs)``

Creates a ticket. The required parameters for ticket creation are short
description and description of the issue. Keyword arguments are used for
other ticket fields.

.. code:: python

    t.create(short_description='Ticket summary',
             description='Ticket description',
             category='Category',
             item='ServiceNow')

The following keyword arguments were tested and accepted by our
particular ServiceNow instance during ticket creation:

.. code:: python

    category = 'Category'
    item = 'ServiceNow'
    contact_type = 'Email'
    opened_for = 'dept'
    assigned_to = 'username'
    impact = '2'
    urgency = '2'
    priority = '2'
    email_from = 'username@domain.com'
    hostname_affected = '127.0.0.1'
    state = 'Work in Progress'
    watch_list = ['username@domain.com', 'user2@domain.com', 'user3@domain.com']
    comments = 'New comment to be added'

get_ticket_content()
--------------------

``get_ticket_content(self, ticket_id)``

Retrieves ticket content as a dictionary. Optional parameter ticket\_id
specifies which ticket should be retrieved this way. If not used, method
calls for ticket\_id provided by ServiceNowTicket constructor (or create
method).

.. code:: python

    # ticket content of the object t
    t.get_ticket_content()
    # ticket content of the ticket <ticket_id>
    t.get_ticket_content(ticket_id=<ticket_id>)

edit()
------

``edit(self, **kwargs)``

Edits fields in a ServiceNow ticket. Keyword arguments are used to
specify ticket fields. Most of the fields overwrite existing fields. One
known exception to that rule is 'comments' which adds new comment when
specified.

.. code:: python

    t.edit(short_description='Ticket summary')

The following keyword arguments were tested and accepted by our
particular ServiceNow instance during ticket editing:

.. code:: python

    category = 'Category'
    item = 'ServiceNow'
    contact_type = 'Email'
    opened_for = 'dept'
    assigned_to = 'username'
    impact = '2'
    urgency = '2'
    priority = '2'
    email_from = 'username@domain.com'
    hostname_affected = '127.0.0.1'
    state = 'Work in Progress'
    watch_list = ['username@domain.com', 'user2@domain.com', 'user3@domain.com']
    comments = 'New comment to be added'

add_comment()
-------------

``add_comment(self, comment)``

Adds a comment to a ServiceNow ticket. Note that comments cannot be
modified or deleted in the current implementation.

.. code:: python

    t.add_comment('Test comment')


change_status(self, status)
---------------------------

Changes status of a ServiceNow ticket.

.. code:: python

    t.change_status('Work in Progress')

add_cc()
--------

``add_cc(self, user)``

Adds watcher(s) to a ServiceNow ticket. Accepts email addresses in the
form of list of strings or one string representing one email address.

.. code:: python

    t.add_cc('username@domain.com')

rewrite_cc()
------------

``rewrite_cc(self, user)``

Rewrites current watcher list in the ServiceNow ticket. Accepts email
addresses in the form of list of strings or one string representing one
email address.

.. code:: python

    t.rewrite_cc(['username@domain.com', 'user2@domain.com', 'user3@domain.com'])

remove_cc()
-----------

``remove_cc(self, user)``

Removes users from the current watcher list in the ServiceNow ticket.
Accepts email addresses in the form of list of strings or one string
representing one email address.

.. code:: python

    t.remove_cc(['username@domain.com', 'user3@domain.com'])


Examples
^^^^^^^^

Create ServiceNowTicket object
------------------------------

Currently, ticketutil supports HTTP Basic Authentication for ServiceNow.
When creating a ServiceNowTicket object, pass in your username and
password as a tuple into the auth argument. The code then retrieves a
token that will be used as authentication for subsequent API calls. For
more details see `documentation <../docs/servicenow.md>`__.

.. code:: python

    >>> from ticketutil.servicenow import ServiceNowTicket
    >>> t = ServiceNowTicket(<servicenow_url>,
                             <table_name>,
                             auth=(<username>, <password>))

You should see the following response:

.. code:: python

    INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): <servicenow_url>
    INFO:root:Successfully authenticated to ServiceNow

You now have a ``ServiceNowTicket`` object that is associated with the
``<table_name>`` table.

Some example workflows are found below. Notice that the first step is to
create a ServiceNowTicket object with an url table name (and with a
ticket id when working with existing tickets), and the last step is
closing the Requests session with ``t.close_requests_session()``.

When creating a ServiceNow ticket, ``short_description``,
``description``, ``category`` and ``item`` are required parameters.
Also, the Reporter is automatically filled in as the current kerberos
principal or username supplied during authentication.


Create new ServiceNow ticket
----------------------------

.. code:: python

    from ticketutil.servicenow import ServiceNowTicket

    # Create a ticket object and pass the url and table name in as strings
    t = ServiceNowTicket(<servicenow_url>,
                         <table_name>,
                         auth=(<username>, <password>))

    # Create a ticket and perform some common ticketing operations
    t.create(short_description='TEST adding SNow API into ticketutil',
             description='Ticket description',
             category='Communication',
             item='ServiceNow')
    t.edit(assigned_to='pzubaty',
           priority='3')
    t.add_cc(['username1@mail.com', 'username2@mail.com'])
    t.remove_cc('username1@mail.com')
    t.change_status('Work in Progress')

    # Retrieve ticket content
    t.get_ticket_content()

    # Close Requests session
    t.close_requests_session()


Update existing ServiceNow tickets
----------------------------------

.. code:: python

    from ticketutil.servicenow import ServiceNowTicket

    t = ServiceNowTicket(<servicenow_url>,
                         <table_name>,
                         auth=(<username>, <password>),
                         ticket_id=<ticket_id>)
    t.add_comment('Test Comment')
    t.edit(priority='4',
           impact='4')

    # Work with a different ticket
    t.set_ticket_id(<new_ticket_id>)
    t.change_status('Pending')

    # Close Requests session
    t.close_requests_session()


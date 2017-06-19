RT
====

This document contains information on the methods available when working
with a RTTicket object. A list of the RT fields that have been tested
when creating and editing tickets is included. Because each instance of
RT can have custom fields and custom values, some of the tested fields
may not be applicable to certain instances of RT. Additionally, your RT
instance may contain ticket fields that we have not tested. Custom field
names and values can be passed in as keyword arguments when creating and
editing tickets, and the RT REST API should be able to process them. See
RT's REST API documentation for more information on custom fields:
https://rt-wiki.bestpractical.com/wiki/REST


Methods
^^^^^^^

-  `create() <#create>`__
-  `edit() <#edit>`__
-  `add\_comment() <#comment>`__
-  `change\_status() <#status>`__
-  `add\_attachment() <#add_attachment>`__


create()
--------

``create(self, subject, text, **kwargs)``

Creates a ticket. The required parameters for ticket creation are
subject and text. Keyword arguments are used for other ticket fields.

.. code:: python

    t.create(subject='Ticket subject',
             text='Ticket text')

The following keyword arguments were tested and accepted by our
particular RT instance during ticket creation:

.. code:: python

    subject='Ticket subject'
    text='Ticket text'
    priority='5'
    owner='username@mail.com'
    cc='username@mail.com'
    admincc=['username@mail.com', 'username2@mail.com']

NOTE: cc and admincc accept a string representing one user's email
address, or a list of strings for multiple users.


edit()
------

``edit(self, **kwargs)``

Edits fields in a RT ticket. Keyword arguments are used to specify
ticket fields.

.. code:: python

    t.edit(owner='username@mail.com')

The following keyword arguments were tested and accepted by our
particular RT instance during ticket editing:

.. code:: python

    priority='5'
    owner='username@mail.com'
    cc='username@mail.com'
    admincc=['username@mail.com', 'username2@mail.com']

NOTE: cc and admincc accept a string representing one user's email
address, or a list of strings for multiple users.


add_comment()
-------------

``add_comment(self, comment)``

Adds a comment to a RT ticket.

.. code:: python

    t.add_comment('Test comment')


change_status
-------------

``change_status(self, status)``

Changes status of a RT ticket.

.. code:: python

    t.change_status('Resolved')


add_attachment()
----------------

``add_attachment(self, file_name)``

Attaches a file to a RT ticket.

.. code:: python

    t.add_attachment('filename.txt')


Examples
^^^^^^^^

Create RTTicket object
----------------------

Authenticate through HTTP Basic Authentication:

.. code:: python

    >>> from ticketutil.rt import RTTicket
    >>> t = RTTicket(<rt_url>,
                     <project_queue>,
                     auth=('username', 'password'))

Authenticate through Kerberos after running ``kinit``:

.. code:: python

    >>> from ticketutil.rt import RTTicket
    >>> t = RTTicket(<rt_url>,
                     <project_queue>,
                     auth='kerberos')

You should see the following response:

::

    INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): <rt_url>
    INFO:root:Successfully authenticated to RT

You now have a ``RTTicket`` object that is associated with the
``<project_queue>`` queue.

Some example workflows are found below. Notice that the first step is to
create a RTTicket object with a url and project queue (and with a ticket
id when working with existing tickets), and the last step is closing the
Requests session with ``t.close_requests_session()``.

When creating a RT ticket, ``subject`` and ``text`` are required
parameters. Also, the Reporter is automatically filled in as the current
kerberos principal.

Note: The tested parameters for the create() and edit() methods are
found in the docstrings in the code and in the docs folder. Any other
ticket field can be passed in as a keyword argument, but be aware that
the value for non-tested fields or custom fields may be in a
non-intuitive format. See RT's REST API documentation for more
information: https://rt-wiki.bestpractical.com/wiki/REST

Create and update RT ticket
---------------------------

.. code:: python

    from ticketutil.rt import RTTicket

    # Create a ticket object and pass the url and project queue in as strings.
    t = RTTicket(<rt_url>,
                 <project_queue>,
                 auth='kerberos')

    # Create a ticket and perform some common ticketing operations.
    t.create(subject='Ticket subject',
             text='Ticket text',
             priority='5',
             owner='username@mail.com',
             cc='username@mail.com,
             admincc=['username@mail.com', 'username2@mail.com'])
    t.add_comment('Test Comment')
    t.edit(priority='4',
           cc='username1@mail.com')
    t.add_attachment('file_to_attach.txt')
    t.change_status('Resolved')

    # Close Requests session.
    t.close_requests_session()


Update existing RT tickets
--------------------------

.. code:: python

    from ticketutil.rt import RTTicket

    # Create a ticket object and pass the url, project queue, and ticket id in as strings.
    t = RTTicket(<rt_url>,
                 <project_queue>,
                 auth='kerberos',
                 ticket_id=<ticket_id>)

    # Perform some common ticketing operations.
    t.add_comment('Test Comment')
    t.edit(priority='4',
           cc='username@mail.com')

    # Work with a different ticket.
    t.set_ticket_id(<new_ticket_id>)
    t.change_status('Resolved')

    # Close Requests session.
    t.close_requests_session()


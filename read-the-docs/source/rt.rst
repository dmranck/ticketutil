ticketutil.rt
=============

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


Table of contents
^^^^^^^^^^^^^^^^^

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


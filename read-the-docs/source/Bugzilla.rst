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
-------

-  `create() <#create>`__
-  `edit() <#edit>`__
-  `add_comment() <#comment>`__
-  `change_status() <#status>`__
-  `remove_cc() <#remove_cc>`__
-  `add_cc() <#add_cc>`__
-  `add_attachment() <#add_attachment>`__

create()
~~~~~~~~

``create(self, summary, description, \*\*kwargs)``

Creates a ticket. The required parameters for ticket creation are
summary and description. Keyword arguments are used for other ticket
fields.

.. code:: python

    t.create(summary='Ticket summary',
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
~~~~~~

``edit(self, \*\*kwargs)``

Edits fields in a Bugzilla ticket. Keyword arguments are used to specify
ticket fields.

.. code:: python

    t.edit(summary='Ticket summary')

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
~~~~~~~~~~~~~

``add_comment(self, comment,\*\*kwargs )``

Adds a comment to a Bugzilla ticket. Keyword arguments are used to
specify comment options.

.. code:: python

    t.add_comment('Test comment')

change_status()
~~~~~~~~~~~~~~~

``change\_status(self, status, \*\*kwargs)``

Changes status of a Bugzilla ticket. Some status changes require a
secondary field (i.e. resolution). Specify this as a keyword argument. A
resolution of Duplicate requires dupe\_of keyword argument with a valid
bug ID.

.. code:: python

    t.change_status('NEW')
    t.change_status('CLOSED', resolution='DUPLICATE', dupe_of='<bug_id>')

remove_cc()
~~~~~~~~~~~

``remove_cc(self, user)``

Removes user(s) from CC List of a Bugzilla ticket. Accepts a string
representing one user's email address, or a list of strings for multiple
users.

.. code:: python

    t.remove_cc('username@mail.com')

add_cc()
~~~~~~~~

``add_cc(self, user)``

Adds user(s) to CC List of a Bugzilla ticket. Accepts a string
representing one user's email address, or a list of strings for multiple
users.

.. code:: python

    t.add_cc(['username1@mail.com', 'username2@mail.com'])

add_attachment()
~~~~~~~~~~~~~~~~

``add_attachment(self, file\_name, data, summary, \*\*kwargs )``

Add attachment in a Bugzilla ticket. Keyword arguments are used to
specify additional attachment options.

.. code:: python

    t.add_attachment(file_name='Name to be displayed on UI',
                     data='Location(path) or contents of the attachment',
                     summary='A short string describing the attachment.')


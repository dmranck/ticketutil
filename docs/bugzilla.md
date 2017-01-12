# ticketutil.bugzilla

This document contains information on the methods available when working
with a BugzillaTicket object. A list of the Bugzilla fields that have 
been tested when creating and editing tickets will be included. Because 
each instance of Bugzilla can have custom fields and custom values, some 
of the tested fields may not be applicable to certain instances of 
Bugzilla. Additionally, your Bugzilla instance may contain ticket fields
that we have not tested. Custom field names and values can be passed in
as keyword arguments when creating and editing tickets, and the Bugzilla
REST API should be able to process them. See Bugzilla's REST API 
documentation for more information on custom fields: 
http://bugzilla.readthedocs.io/en/latest/api/index.html

## Table of contents
- [create()](#create)
- [edit()](#edit)
- [add_comment()](#comment)
- [change_status()](#status)

### create(self, summary, description, \*\*kwargs) <a name="create"></a>

Creates a ticket. The required parameters for ticket creation are
summary and description. Keyword arguments are used for other ticket
fields.

```python
t.create(summary='Ticket summary',
         description='Ticket description')
```

Tested create() ticket fields:

```python
summary='Ticket summary'
description='Ticket description'
assignee='username@mail.com'
qa_contact='username@mail.com'
component='Test component'
version='version'
priority='high'
severity='medium'
alias='SomeAlias'
```

### edit(self, \*\*kwargs) <a name="edit"></a>

Edits fields in a Bugzilla ticket. Keyword arguments are used to 
specify ticket fields.

```python
t.edit(summary='Ticket summary')
```

Tested edit() ticket fields:

```python
summary='Ticket summary'
assignee='username@mail.com'
qa_contact='username@mail.com'
component='Test component'
version='version'
priority='high'
severity='medium'
alias='SomeAlias'
```

### add_comment(self, comment) <a name="comment"></a>

Adds a comment to a Bugzilla ticket.

```python
t.add_comment('Test comment')
```

### change_status(self, status, \*\*kwargs) <a name="status"></a>

Changes status of a Bugzilla ticket. Some status changes require a 
secondary field (i.e. resolution). Specify this as a keyword argument.
A resolution of Duplicate requires dupe_of keyword argument with a valid 
bug ID.

```python
t.change_status('NEW')
t.change_status('CLOSED', resolution='DUPLICATE', dupe_of='<bug_id>')
```

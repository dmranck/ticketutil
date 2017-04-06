# ticketutil.bugzilla

This document contains information on the methods available when working
with a BugzillaTicket object. A list of the Bugzilla fields that have 
been tested when creating and editing tickets is included. Because 
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
- [remove_cc()](#remove_cc)
- [add_cc()](#add_cc)

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

### add_comment(self, comment,\*\*kwargs ) <a name="comment"></a>

Adds a comment to a Bugzilla ticket. Keyword arguments are used to 
specify comment options.

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

### remove_cc(self, user) <a name="remove_cc"></a>

Removes user(s) from CC List of a Bugzilla ticket. Accepts a string 
representing one user's email address, or a list of strings for multiple 
users.

```python
t.remove_cc('username@mail.com')
```

### add_cc(self, user) <a name="add_cc"></a>

Adds user(s) to CC List of a Bugzilla ticket. Accepts a string 
representing one user's email address, or a list of strings for multiple 
users.

```python
t.add_cc(['username1@mail.com', 'username2@mail.com'])
```

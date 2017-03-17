# ticketutil.servicenow

This document contains information on the methods available when working
 with a ServiceNow object. A list of the ServiceNow fields that have been
 tested when creating and editing tickets will be included. Because each
 instance of ServiceNow can have custom fields and custom values, some
 of the tested fields may not be applicable to certain instances of ServiceNow.
 Additionally, your ServiceNow instance may contain ticket fields that we have
 not tested. Keep in your mind different ServiceNow tables contain different
 fields with different properties. Mandatory field of one table is optional
 in another table (or it doesn't exist at all).

Custom field names and values can be passed in as keyword arguments when
 creating and editing tickets, and the ServiceNow REST API should be able
 to process them. For more information see ServiceNow's REST API Wiki page:
 http://wiki.servicenow.com/index.php?title=REST_API

## Table of contents
- [create()](#create)
- [get_ticket_content()](#content)
- [edit()](#edit)
- [add_comment()](#comment)
- [change_status()](#status)
- [add_cc()](#add_cc)
- [rewrite_cc()](#rewrite_cc)
- [remove_cc()](#remove_cc)

### create(self, short_description, description, category, item, \*\*kwargs) <a name="create"></a>

Creates a ticket. The required parameters for ticket creation are
short description and description of the issue. Keyword arguments are used
 for other ticket fields.

```python
t.create(short_description='Ticket summary',
         description='Ticket description')
```

Tested create() ticket fields:

```python
category = 'Category',
item = 'ServiceNow'
contact_type = 'Email',
opened_for = 'dept',
assigned_to = 'username',
impact = '2',
urgency = '2',
priority = '2',
email_from = 'username@domain.com',
hostname_affected = '127.0.0.1',
state = 'Work in Progress',
watch_list = 'username@domain.com, user2@domain.com, user3@domain.com'
comments = 'New comment to be added'
```

### get_ticket_content(self, ticket_id) <a name="content"></a>

Retrieves ticket content inside a dictionary. Optional parameter ticket_id
 specifies which ticket should be retrieved this way. If not used, method calls
 for ticket_id provided by ServiceNowTicket constructor (or create method).

```python
# ticket content of the object t
t.get_ticket_content()
# ticket content of the ticket 'ID0123456'
t.get_ticket_content(ticket_id='ID0123456')
```

### edit(self, \*\*kwargs) <a name="edit"></a>

Edits fields in a ServiceNow ticket. Keyword arguments are used to
 specify ticket fields. Most of the fields overwrite existing fields.
 One known exception to that rule is 'comments' which adds new comment when
 specified.

```python
t.edit(short_description='Ticket summary')
```

Tested edit() ticket fields:

```python
category = 'Category',
item = 'ServiceNow'
contact_type = 'Email',
opened_for = 'dept',
assigned_to = 'username',
impact = '2',
urgency = '2',
priority = '2',
email_from = 'username@domain.com',
hostname_affected = '127.0.0.1',
state = 'Work in Progress',
watch_list = 'username@domain.com, user2@domain.com, user3@domain.com'
comments = 'New comment to be added'
```

### add_comment(self, comment) <a name="comment"></a>

Adds a comment to a ServiceNow ticket. Note that comments cannot be modified
 or deleted in the current implementation.

```python
t.add_comment('Test comment')
```

### change_status(self, status) <a name="status"></a>

Changes status of a ServiceNow ticket.

```python
t.change_status('Work in Progress')
```

### add_cc(self, user) <a name="add_cc"></a>

Adds watcher(s) to a ServiceNow ticket. Accepts emails in the form of string
 with ',' as the separator.

```python
t.add_cc('username@domain.com')
```

### rewrite_cc(self, user) <a name="rewrite_cc"></a>

Rewrites current watcher list in the ServiceNow ticket. Accepts emails
 in the form of string with ',' as the separator.

```python
# new CC list
t.rewrite_cc('username@domain.com, user2@domain.com, user3@domain.com')
```

### remove_cc(self, user) <a name="remove_cc"></a>

Removes users from the current watcher list in the ServiceNow ticket. Accepts
 emails in the form of string with ',' as the separator.

```python
# new CC list
t.rewrite_cc('username@domain.com, user3@domain.com')
```

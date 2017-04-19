# ticketutil.servicenow

This document contains information on the methods available when working
with a ServiceNow object. A list of the ServiceNow fields that have been
tested when creating and editing tickets is included. Because each
instance of ServiceNow can have custom fields and custom values, some
of the tested fields may not be applicable to certain instances of ServiceNow.
Additionally, your ServiceNow instance may contain ticket fields that we have
not tested. Keep in mind different ServiceNow tables contain different
fields with different properties. Mandatory fields in one table may be optional
or non-existent in another table.

Custom field names and values can be passed in as keyword arguments when
creating and editing tickets. These are processed by the ServiceNow REST API
right afterwards. You can also use [get_ticket_content](#content) to get ticket
content including preset field names.

For more information about REST API and fields see ServiceNow's Wiki:
- [REST API](http://wiki.servicenow.com/index.php?title=REST_API)
- [Introduction to Fields](http://wiki.servicenow.com/index.php?title=Introduction_to_Fields)
- [Dot-Walking](http://wiki.servicenow.com/index.php?title=Dot-Walking)


## Table of contents
- [set_ticket_id()](#set_ticket)
- [create()](#create)
- [get_ticket_content()](#content)
- [edit()](#edit)
- [add_comment()](#comment)
- [change_status()](#status)
- [add_cc()](#add_cc)
- [rewrite_cc()](#rewrite_cc)
- [remove_cc()](#remove_cc)
- [devops_one_url()](#devops_one)

### set_ticket_id(self, ticket_id)

Updates ticket content for the current ticket object. This ticket object is
assigned using `ticket_id` which is a string.

```python
# switch to ticket 'ID0123456'
t.set_ticket_id('ID0123456')
```

### create(self, short_description, description, category, item, \*\*kwargs) <a name="create"></a>

Creates a ticket. The required parameters for ticket creation are
short description and description of the issue. Keyword arguments are used
for other ticket fields.

```python
t.create(short_description='Ticket summary',
         description='Ticket description',
         category='Category',
         item='ServiceNow')
```

Tested create() ticket fields:

```python
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
```

### get_ticket_content(self, ticket_id) <a name="content"></a>

Retrieves ticket content inside a dictionary. Optional parameter ticket_id
specifies which ticket should be retrieved this way. If not used, method calls
for ticket_id provided by ServiceNowTicket constructor (or create method).

```python
# ticket content of the object t
t.get_ticket_content()
# ticket content of the ticket <ticket_id>
t.get_ticket_content(ticket_id=<ticket_id>)
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

Adds watcher(s) to a ServiceNow ticket. Accepts email addresses in the form
of list of strings or one string representing one email address.

```python
t.add_cc('username@domain.com')
```

### rewrite_cc(self, user) <a name="rewrite_cc"></a>

Rewrites current watcher list in the ServiceNow ticket. Accepts email addresses
in the form of list of strings or one string representing
one email address.

```python
t.rewrite_cc(['username@domain.com', 'user2@domain.com', 'user3@domain.com'])
```

### remove_cc(self, user) <a name="remove_cc"></a>

Removes users from the current watcher list in the ServiceNow ticket. Accepts
email addresses in the form of list of strings or one string representing
one email address.

```python
t.remove_cc(['username@domain.com', 'user3@domain.com'])
```

### devops_one_url(server, table, sys_id) <a name="devops_one"></a>

This function is not part of the ServiceNowTicket, but it's related. It creates
DevOps One URL of the existing ticket supplied by server name, table name and
ticket sys_id.

```python
url = devops_one_url(server, table, sys_id)
```

# ticketutil.redmine

This document contains information on the methods available when working
with a RedmineTicket object. A list of the Redmine fields that have 
been tested when creating and editing tickets is included. Because 
each instance of Redmine can have custom fields and custom values, some 
of the tested fields may not be applicable to certain instances of 
Redmine. Additionally, your Redmine instance may contain ticket fields
that we have not tested. Custom field names and values can be passed in
as keyword arguments when creating and editing tickets, and the Redmine
REST API should be able to process them. See Redmine's REST API 
documentation for more information on custom fields: 
http://www.redmine.org/projects/redmine/wiki/Rest_api

Note: Redmine's REST API requires that you refer to many fields using 
their 'id' values instead of their 'name's, including Project, Status, 
Priority, and User. For these four fields, we have `_get_<field>_id()`
methods, so you can use the name instead of having to look up the id.

## Table of contents
- [create()](#create)
- [edit()](#edit)
- [add_comment()](#comment)
- [change_status()](#status)
- [remove_watcher()](#remove_watcher)
- [add_watcher()](#add_watcher)
- [add_attachment()](#add_attachment)

### create(self, subject, description, \*\*kwargs) <a name="create"></a>

Creates a ticket. The required parameters for ticket creation are
subject and description. Keyword arguments are used for other ticket
fields.

```python
t.create(subject='Ticket subject',
         description='Ticket description')
```

The following keyword arguments were tested and accepted by our
particular Redmine instance during ticket creation:

```python
subject='Ticket subject'
description='Ticket description'
priority='Urgent'
start_date='2017-01-20'
due_date='2017-01-25'
done_ratio='70'
assignee='username@mail.com'
```

### edit(self, \*\*kwargs) <a name="edit"></a>

Edits fields in a Redmine ticket. Keyword arguments are used to 
specify ticket fields.

```python
t.edit(subject='Ticket subject')
```

The following keyword arguments were tested and accepted by our
particular Redmine instance during ticket editing:

```python
subject='Ticket subject'
description='Ticket description'
priority='Urgent'
start_date='2017-01-20'
due_date='2017-01-25'
done_ratio='70'
assignee='username@mail.com'
```

### add_comment(self, comment) <a name="comment"></a>

Adds a comment to a Redmine ticket.

```python
t.add_comment('Test comment')
```

### change_status(self, status) <a name="status"></a>

Changes status of a Redmine ticket.

```python
t.change_status('Resolved')
```

### remove_watcher(self, watcher) <a name="remove_watcher"></a>

Removes watcher from a Redmine ticket. Accepts an email or username.

```python
t.remove_watcher('username')
```

### add_watcher(self, watcher) <a name="add_watcher"></a>

Adds watcher to a Redmine ticket. Accepts an email or username.

```python
t.add_watcher('username')
```

### add_attachment(self, file_name) <a name="add_attachment"></a>

Attaches a file to a Redmine ticket.

```python
t.add_attachment('filename.txt')
```

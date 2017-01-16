# ticketutil.jira

This document contains information on the methods available when working
with a JiraTicket object. A list of the JIRA fields that have 
been tested when creating and editing tickets will be included. Because 
each instance of JIRA can have custom fields and custom values, some 
of the tested fields may not be applicable to certain instances of 
JIRA. Additionally, your JIRA instance may contain ticket fields
that we have not tested. Custom field names and values can be passed in
as keyword arguments when creating and editing tickets, and the JIRA
REST API should be able to process them. See JIRA's REST API 
documentation for more information on custom fields: 
https://docs.atlassian.com/jira/REST/cloud/

## Table of contents
- [create()](#create)
- [edit()](#edit)
- [add_comment()](#comment)
- [change_status()](#status)
- [remove_all_watchers()](#remove_all_watchers)
- [remove_watcher()](#remove_watcher)
- [add_watcher()](#add_watcher)
- [add_attachment()](#add_attachment)

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
priority='Major'
type='Task'
assignee='username'
reporter='username'
environment='Environment Test'
duedate='2017-01-13'
parent='KEY-XX'
customfield_XXXXX='Custom field text'
```

### edit(self, \*\*kwargs) <a name="edit"></a>

Edits fields in a JIRA ticket. Keyword arguments are used to 
specify ticket fields.

```python
t.edit(summary='Ticket summary')
```

Tested edit() ticket fields:

```python
summary='Ticket summary'
description='Ticket description'
priority='Major'
type='Task'
assignee='username'
reporter='username'
environment='Environment Test'
duedate='2017-01-13'
parent='KEY-XX'
customfield_XXXXX='Custom field text'
```

### add_comment(self, comment) <a name="comment"></a>

Adds a comment to a JIRA ticket.

```python
t.add_comment('Test comment')
```

### change_status(self, status) <a name="status"></a>

Changes status of a JIRA ticket.

```python
t.change_status('In Progress')
```

### remove_all_watchers(self) <a name="remove_all_watchers"></a>

Removes all watchers from a JIRA ticket.

```python
t.remove_all_watchers()
```

### remove_watcher(self, watcher) <a name="remove_watcher"></a>

Removes watcher from a JIRA ticket. Accepts an email or username.

```python
t.remove_watcher('username')
```

### add_watcher(self, watcher) <a name="add_watcher"></a>

Adds watcher to a JIRA ticket. Accepts an email or username.

```python
t.add_watcher('username')
```

### add_attachment(self, file_name) <a name="add_attachment"></a>

Attaches a file to a JIRA ticket.

```python
t.add_attachment('filename.txt')
```

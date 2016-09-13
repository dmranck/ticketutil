# TicketUtil

TicketUtil is a utility that allows you to easily interact with various 
ticketing tools using their REST APIs. Currently, the supported tools
are JIRA, RT, and Redmine, with future plans to support Bugzilla and 
Trac. Kerberos authentication is supported for JIRA and 
RT while HTTP Basic authentication is supported for Redmine.

This module allows you to create, update, and resolve tickets in each
tool. Along with these three core functions, lower-level tool-specific
functions are supported - adding and removing watchers in JIRA, 
transitioning tickets through a project's workflow in JIRA, adding 
comments in JIRA and RT, etc.

## Table of contents
- [Installation](#installation)
- [Usage](#usage)
- [JIRA](#jira) 
- [RT](#rt) 
- [Redmine](#redmine)
- [Comments? / Questions? / Coming Soon](#comments)

### Installation

TicketUtil requires Python 3 and a short list of packages defined in the
requirements.txt file. 

To install the required packages, simply type:

```
pip install -r ticket_util_requirements.txt
```

Then, copy TicketUtil.py into your codebase, or add it as a submodule
and you're all set!

### Usage

The general usage workflow for creating new tickets is:

 - Create a JiraTicket or RTTicket object with `<url>` and 
 `<project_key>`. This verifies that you are able to properly 
 authenticate to the ticketing tool.
 - Create a ticket with the `create()` method. This sets the `ticket_id`
 instance variable, allowing you to perform more tasks on the ticket.
 - Add comments, edit ticket fields, add watchers, etc on the ticket.
 - Close ticket Requests session with `close_requests_session()`.
 
To work on existing tickets, you can also pass in a third parameter when
creating a Ticket object: `<ticket_id>`. The general workflow for
working with existing tickets is as follows:

 - Create a JiraTicket or RTTicket object with `<url>`, `<project_key>`, 
 and `<ticket_id>`. This verifies that you are able to properly 
 authenticate to the ticketing tool.
 - Update a ticket with the `update()` method, or resolve a ticket with
 `resolve()`. You can also add comments, edit ticket fields, add 
 watchers, etc.
 - Close ticket Requests session with `close_requests_session()`.
 
There is also a `set_ticket_id()` method for a Ticket object. This is
useful if you are working with a Ticket object that already has the 
`<ticket_id>` instance variable set, but would like to begin working
on a separate ticket. Instead of creating a new Ticket object, you can
simply pass an existing `<ticket_id>` in to the `set_ticket_id()`
method to begin working on another ticket.

See the docstrings in the code for more information and examples.

### JIRA

Currently, TicketUtil supports Kerberos authentication for JIRA. 
Authenticate through kerberos using `kinit` and then 
execute the following in Python:

```python
>>> from TicketUtil import JiraTicket
>>> t = JiraTicket(<jira_url>, <project_key>)
```

You should see the following response:

```
INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): <jira_url>
INFO:root:Successfully authenticated to JIRA
```

You now have a `JiraTicket` object that is associated with the 
`<project_key>` project.

Some example workflows are found below. Notice that they all start
with creating a JiraTicket object with a project key (and with a ticket
id when updating / resolving tickets). The last step is always closing
the Requests session with `t.close_requests_session()`.

#### Create JIRA ticket
```python
import TicketUtil

# Create a ticket object and pass the url and project key in as strings.
t = TicketUtil.JiraTicket(<jira_url>, <project_key>)

# Create our params for ticket creation.
params = {'summary': 'Ticket Title',
          'description': 'Ticket Description',
          'issuetype': {'name': 'Task'}}

# Create our ticket.
t.create(params)

# After creating the ticket, the ticket_id and ticket_url instance vars have been set, so you can continue working with it.
t.add_comment("Test Comment")
t.edit_ticket_fields({'description': 'New Description', 'assignee': {'name': 'dranck'}})
t.remove_watchers()
t.add_watchers('<email_address_1>, <email_address_2>')

# Close Requests session.
t.close_requests_session()
```

#### Update JIRA ticket
```python
import TicketUtil

# Create a ticket object and pass the url, project key, and ticket id in as strings.
t = TicketUtil.JiraTicket(<jira_url>, <project_key>, <ticket_id>)

# Update ticket.
t.update('Update ticket with this comment')

# Because update() simply adds a comment to the ticket, you could also use add_comment():
t.add_comment('Add a second comment to ticket')

# Close Requests session.
t.close_requests_session()
```

#### Resolve JIRA ticket
```python
import TicketUtil

# Create a ticket object and pass the url, project key, and ticket id in as strings.
t = TicketUtil.JiraTicket(<jira_url>, <project_key>, <ticket_id>)

# Resolve ticket with transition id of '3'.
t.resolve('3')

# Close Requests session.
t.close_requests_session()
```

### RT

Currently, TicketUtil supports Kerberos authentication for JIRA. 
Authenticate through kerberos using `kinit` and then 
execute the following in Python:

```python
>>> from TicketUtil import RTTicket
>>> t = RTTicket(<rt_url>, <project_queue>)
```

You should see the following response:

```
INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): <rt_url>
INFO:root:Successfully authenticated to RT
```

You now have a `RTTicket` object that is associated with the 
`<project_queue>` queue.

Some example workflows are found below. Notice that they all start
with creating a RTTicket object associated with a queue (and with a 
ticket id when updating / resolving tickets). The last step is always 
closing the Requests session with `t.close_requests_session()`.

#### Create RT ticket
```python
import TicketUtil

# Create a ticket object and pass the url and project queue in as strings.
t = TicketUtil.RTTicket(<rt_url>, <project_queue>)

# Create our params for ticket creation.
params = {'Subject': 'Ticket Title',
          'Text': 'Ticket Description',
          'CC': '<email_address_1>, <email_address_2>'}

# Create our ticket.
t.create(params)

# After creating the ticket, the ticket_id and ticket_url instance vars have been set, so you can continue working with it.
t.add_comment("Test Comment")

# Close Requests session.
t.close_requests_session()
```

#### Update RT ticket
```python
# Create a ticket object and pass the url, project queue, and ticket id in as strings.
t = TicketUtil.RTTicket(<rt_url>, <project_queue>, <ticket_id>)

# Update ticket.
t.update('Update ticket with this comment')

# Because update() simply adds a comment to the ticket, you could also use add_comment():
t.add_comment('Add a second comment to ticket')

# Close Requests session.
t.close_requests_session()
```

#### Resolve RT ticket
```python
import TicketUtil

# Create a ticket object and pass the url, project queue, and ticket id in as strings.
t = TicketUtil.RTTicket(<rt_url>, <project_queue>, <ticket_id>)

# Resolve ticket.
t.resolve()

# Close Requests session.
t.close_requests_session()
```

### Redmine

Currently, TicketUtil supports HTTP Basic authentication for Redmine. 
When creating a RedmineTicket object, pass in your username
and password as a tuple into the auth argument. You can also use an API 
key passed in as a username with a random password for <password>. For 
more details, see http://www.redmine.org/projects/redmine/wiki/Rest_api#Authentication.

```python
>>> from TicketUtil import RTTicket
>>> t = RedmineTicket(<redmine_url>, <project_name>, auth=(<username>, <password>))
```

You should see the following response:

```
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): <redmine_url>
INFO:root:Successfully authenticated to Redmine
```

You now have a `RedmineTicket` object that is associated with the 
`<project_name>` project.

Some example workflows are found below. Notice that they all start
with creating a RedmineTicket object associated with a project (and with 
a ticket id when updating / resolving tickets). The last step is always 
closing the Requests session with `t.close_requests_session()`.

#### Create Redmine ticket
```python
import TicketUtil

# Create a ticket object and pass the url and project name in as strings.
t = RedmineTicket(<redmine_url>, <project_name>, auth=(<username>, <password>))

# Create our params for ticket creation.
params = {'subject': 'Ticket Subject',
          'description': 'Ticket Description'}

# Create our ticket.
t.create(params)

# After creating the ticket, the ticket_id and ticket_url instance vars have been set, so you can continue working with it.
t.add_comment("Test Comment")

# Close Requests session.
t.close_requests_session()
```

#### Update Redmine ticket
```python
import TicketUtil

# Create a ticket object and pass the url, project name, and ticket id in as strings.
t = RedmineTicket(<redmine_url>, <project_name>, <ticket_id>, auth=(<username>, <password>))

# Update ticket.
t.update('Update ticket with this comment')

# Because update() simply adds a comment to the ticket, you could also use add_comment():
t.add_comment('Add a second comment to ticket')

# Close Requests session.
t.close_requests_session()
```

#### Resolve Redmine ticket
```python
import TicketUtil

# Create a ticket object and pass the url, project name, and ticket id in as strings.
t = RedmineTicket(<redmine_url>, <project_name>, <ticket_id>, auth=(<username>, <password>))

# Resolve ticket with status id of '3'.
t.resolve('3')

# Close Requests session.
t.close_requests_session()
```

### Comments? / Questions? / Coming Soon <a name="comments"></a>

For questions / comments, email dranck@redhat.com.

The plan for TicketUtil is to support more ticketing tools in the near 
future. Please let me know if there are any suggestions / requests.
Thanks!

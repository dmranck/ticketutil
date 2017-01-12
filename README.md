# ticketutil

ticketutil is a Python module that allows you to easily interact with 
various ticketing tools using their REST APIs. Currently, the supported 
tools are JIRA, RT, Redmine and Bugzilla.
Kerberos authentication is supported for JIRA and RT, while
HTTP Basic authentication is supported for Redmine and Bugzilla.

This module allows you to create tickets, add comments, edit ticket
fields, and change the status of tickets in each tool. Additional 
lower-level tool-specific functions are supported - adding and removing 
watchers in JIRA, adding attachments in JIRA, etc.

## Table of contents
- [Installation](#installation)
- [Usage](#usage)
- [JIRA](#jira) 
- [RT](#rt) 
- [Redmine](#redmine)
- [Bugzilla](#bugzilla)
- [Comments? / Questions? / Coming Soon](#comments)

### Installation

ticketutil is compatible with both Python 2 and Python 3. 

A short list of packages defined in the requirements.txt file need to be 
installed. To install the required packages, simply type:

```
pip install -r requirements.txt
```

Then, copy the ticketutil folder into your codebase, or add it as a 
submodule and you're all set!

### Usage

The general usage workflow for creating new tickets is:

 - Create a JiraTicket, RTTicket, RedmineTicket, or BugzillaTicket
 object with `<url>`, `<project>` and `<auth>`. This verifies that you 
 are able to properly authenticate to the ticketing tool. For tools that 
 require HTTP Basic Authentication (Redmine and Bugzilla), the `<auth>` 
 parameter should contain the username and password specified as a 
 tuple. For tools that support kerberos authentication (JIRA and RT), 
 the `<auth>` parameter should contain 'kerberos'.
 - Create a ticket with the `create()` method. This sets the `ticket_id`
 instance variable, allowing you to perform more tasks on the ticket.
 - Add comments, edit ticket fields, add watchers, change the ticket
 status, etc on the ticket.
 - Close ticket Requests session with `close_requests_session()`.
 
To work on existing tickets, you can also pass in a fourth parameter 
when creating a Ticket object: `<ticket_id>`. The general workflow for
working with existing tickets is as follows:

 - Create a JiraTicket, RTTicket, RedmineTicket, or BugzillaTicket
 object with `<url>`, `<project_key>`, `<auth>` and `<ticket_id>`.
 - Add comments, edit ticket fields, add watchers, change the ticket
 status, etc on the ticket.
 - Close ticket Requests session with `close_requests_session()`.
 
There is also a `set_ticket_id()` method for a Ticket object. This is
useful if you are working with a Ticket object that already has the 
`<ticket_id>` instance variable set, but would like to begin working
on a separate ticket. Instead of creating a new Ticket object, you can
simply pass an existing `<ticket_id>` in to the `set_ticket_id()`
method to begin working on another ticket.

See the docstrings in the code or the tool-specific files in the docs
folder for more information and examples.

### JIRA

Currently, ticketutil supports Kerberos authentication for JIRA. 
Authenticate through kerberos using `kinit` and then execute the 
following in Python:

```python
>>> from ticketutil.jira import JiraTicket
>>> t = JiraTicket(<jira_url>, 
                   <project_key>,
                   auth='kerberos')
```

You should see the following response:

```
INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): <jira_url>
INFO:root:Successfully authenticated to JIRA
```

You now have a `JiraTicket` object that is associated with the 
`<project_key>` project.

Some example workflows are found below. Notice that the first step is to
create a JiraTicket object with a url and project key (and with a ticket
id when working with existing tickets), and the last step is closing the 
Requests session with `t.close_requests_session()`.

When creating a JIRA ticket, `summary` and `description` are 
required parameters. Also, the Reporter is automatically filled in as
the current kerberos principal.

Note: The tested parameters for the create() and edit() methods are
found in the docstrings in the code and in the docs folder. Any other 
ticket field can be passed in as a keyword argument, but be aware that
the value for non-tested fields or custom fields may be in a 
non-intuitive format. See JIRA's REST API documentation for more 
information: 
https://docs.atlassian.com/jira/REST/cloud/

#### Create and update JIRA ticket
```python
from ticketutil.jira import JiraTicket

# Create a ticket object and pass the url and project key in as strings.
t = JiraTicket(<jira_url>, 
               <project_key>,
               auth='kerberos')

# Create a ticket and perform some common ticketing operations.
t.create(summary='Ticket summary',
         description='Ticket description',
         issuetype='Task',
         priority='Major',
         assignee='username')
t.add_comment("Test Comment")
t.edit(priority='Critical',
       issuetype='Bug')
t.remove_all_watchers()
t.add_watcher('username')
t.add_attachment('file_to_attach.txt')
t.change_status('In Progress')

# Close Requests session.
t.close_requests_session()
```

#### Update existing JIRA tickets
```python
from ticketutil.jira import JiraTicket

# Create a ticket object and pass the url, project key, and ticket id in as strings.
t = JiraTicket(<jira_url>,
               <project_key>, 
               auth='kerberos',
               ticket_id=<ticket_id>)

# Perform some common ticketing operations.
t.add_comment("Test Comment")
t.edit(priority='Critical',
       issuetype='Bug')
       
# Work with a different ticket.
t.set_ticket_id(<new_ticket_id>)
t.remove_watcher('username')
t.add_watcher('username')
t.change_status('Done')

# Close Requests session.
t.close_requests_session()
```

### RT

Currently, ticketutil supports Kerberos authentication for RT. 
Authenticate through kerberos using `kinit` and then execute the 
following in Python:

```python
>>> from ticketutil.rt import RTTicket
>>> t = RTTicket(<rt_url>, 
                 <project_queue>,
                 auth='kerberos')
```

You should see the following response:

```
INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): <rt_url>
INFO:root:Successfully authenticated to RT
```

You now have a `RTTicket` object that is associated with the 
`<project_queue>` queue.

Some example workflows are found below. Notice that the first step is to
create a RTTicket object with a url and project queue (and with a ticket
id when working with existing tickets), and the last step is closing the 
Requests session with `t.close_requests_session()`.

When creating a RT ticket, `subject` and `text` are required
parameters. Also, the Reporter is automatically filled in as the current
kerberos principal.

Note: The tested parameters for the create() and edit() methods are
found in the docstrings in the code and in the docs folder. Any other 
ticket field can be passed in as a keyword argument, but be aware that
the value for non-tested fields or custom fields may be in a 
non-intuitive format. See RT's REST API documentation for more 
information: 
https://rt-wiki.bestpractical.com/wiki/REST

#### Create and update RT ticket
```python
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
         admincc='username@mail.com, username2@mail.com')
t.add_comment("Test Comment")
t.edit(priority='4',
       cc='username@mail.com')
t.change_status('Resolved')

# Close Requests session.
t.close_requests_session()
```

#### Update existing RT tickets
```python
from ticketutil.rt import RTTicket

# Create a ticket object and pass the url, project queue, and ticket id in as strings.
t = RTTicket(<rt_url>, 
             <project_queue>, 
             auth='kerberos',
             ticket_id=<ticket_id>)

# Perform some common ticketing operations.
t.add_comment("Test Comment")
t.edit(priority='4',
       cc='username@mail.com')
       
# Work with a different ticket.
t.set_ticket_id(<new_ticket_id>)
t.change_status('Resolved')

# Close Requests session.
t.close_requests_session()
```

### Redmine

Currently, ticketutil supports HTTP Basic authentication for Redmine. 
When creating a RedmineTicket object, pass in your username
and password as a tuple into the auth argument. You can also use an API 
key passed in as a username with a random password for `<password>`. For 
more details, see http://www.redmine.org/projects/redmine/wiki/Rest_api#Authentication.

```python
>>> from ticketutil.redmine import RedmineTicket
>>> t = RedmineTicket(<redmine_url>, 
                      <project_name>, 
                      auth=(<username>, <password>))
```

You should see the following response:

```
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): <redmine_url>
INFO:root:Successfully authenticated to Redmine
```

You now have a `RedmineTicket` object that is associated with the 
`<project_name>` project.

Some example workflows are found below. Notice that the first step is to
create a RedmineTicket object with a url and project key (and with a 
ticket id when working with existing tickets), and the last step is 
closing the Requests session with `t.close_requests_session()`.

When creating a JIRA ticket, `subject` and `description` are 
required parameters. Also, the Reporter is automatically filled in as
the current username.

Note: The tested parameters for the create() and edit() methods are
found in the docstrings in the code and in the docs folder. Any other 
ticket field can be passed in as a keyword argument, but be aware that
the value for non-tested fields or custom fields may be in a 
non-intuitive format. See Redmine's REST API documentation for more 
information: 
http://www.redmine.org/projects/redmine/wiki/Rest_api

#### Create and update Redmine ticket
```python
from ticketutil.redmine import RedmineTicket

# Create a ticket object and pass the url and project name in as strings.
t = RedmineTicket(<redmine_url>, 
                  <project_name>,
                  auth=(<username>, <password>))

# Create a ticket and perform some common ticketing operations.
t.create(subject='Ticket subject',
         description='Ticket description',
         priority='Urgent',
         start_date='2017-01-20',
         due_date='2017-01-25',
         done_ratio='70',
         assignee='username@mail.com')
t.add_comment("Test Comment")
t.edit(priority='Normal',
       due_date='2017-02-25')
t.change_status('Closed')

# Close Requests session.
t.close_requests_session()
```

#### Update existing Redmine tickets
```python
from ticketutil.redmine import RedmineTicket

# Create a ticket object and pass the url, project name, and ticket id in as strings.
t = RedmineTicket(<redmine_url>, 
                  <project_name>, 
                  auth=(<username>, <password>),
                  ticket_id=<ticket_id>)

# Perform some common ticketing operations.
t.add_comment("Test Comment")
t.edit(priority='High',
       done_ratio='90')
       
# Work with a different ticket.
t.set_ticket_id(<new_ticket_id>)
t.change_status('Resolved')

# Close Requests session.
t.close_requests_session()
```

### Bugzilla

Currently, ticketutil supports HTTP Basic authentication for Bugzilla. 
When creating a BugzillaTicket object, pass in your username
and password as a tuple into the auth argument. The code then retrieves
a token that will be used as authentication for subsequent API calls. 
For more details, see: 
http://bugzilla.readthedocs.io/en/latest/api/index.html.

The examples below use basic authentication. For kerberos, set 
`auth='kerberos'` when creating a BugzillaTicket object.

```python
>>> from ticketutil.bugzilla import BugzillaTicket
>>> t = BugzillaTicket(<bugzilla_url>, 
                       <product_name>, 
                       auth=(<username>, <password>))
```

You should see the following response:
```python
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): <bugzilla_url>
INFO:root:Successfully authenticated to Bugzilla with token: <token-id>
```
You now have a `BugzillaTicket` object that is associated with the 
`<product_name>` product.

Some example workflows are found below. Notice that the first step is to
create a BugzillaTicket object with a url and product name (and with a 
ticket id when working with existing tickets), and the last step is 
closing the Requests session with `t.close_requests_session()`.

When creating a RT ticket, `summary` and `description` are required
parameters. Also, the Reporter is automatically filled in as the current
kerberos principal or username supplied during authentication.

Note: The tested parameters for the create() and edit() methods are
found in the docstrings in the code and in the docs folder. Any other 
ticket field can be passed in as a keyword argument, but be aware that
the value for non-tested fields or custom fields may be in a 
non-intuitive format. See Bugzilla's REST API documentation for more 
information: 
http://bugzilla.readthedocs.io/en/latest/api/index.html

#### Create and update Bugzilla ticket
```python
from ticketutil.bugzilla import BugzillaTicket

# Create a ticket object and pass the url and product name in as strings.
t = BugzillaTicket(<bugzilla_url>, 
                   <product_name>,
                   auth=(<username>, <password>))

# Create a ticket and perform some common ticketing operations.
t.create(summary='Ticket summary',
         description='Ticket description',
         component='Test component',
         priority='high',
         severity='medium',
         assignee='username@mail.com',
         qa_contact='username@mail.com)
t.add_comment("Test Comment")
t.edit(priority='medium',
       qa_contact='username@mail.com')
t.change_status('Modified')

# Close Requests session.
t.close_requests_session()
```

#### Update existing Bugzilla tickets
```python
from ticketutil.bugzilla import BugzillaTicket

# Create a ticket object and pass the url, product name, and ticket id in as strings.
t = BugzillaTicket(<bugzilla_url>, 
                   <product_name>, 
                   auth=(<username>, <password>)
                   ticket_id=<ticket_id>)

# Perform some common ticketing operations.
t.add_comment("Test Comment")
t.edit(priority='low',
       severity='low')
       
# Work with a different ticket.
t.set_ticket_id(<new_ticket_id>)
t.change_status(status='CLOSED', resolution='NOTABUG')

# Close Requests session.
t.close_requests_session()
```

### Comments? / Questions? / Coming Soon <a name="comments"></a>

For questions / comments, email dranck@redhat.com. 
For anything specific to Bugzilla, email kshirsal@redhat.com.

The plan for ticketutil is to support more ticketing tools in the near 
future and to support more ticketing operations for the currently
supported tools. Please let us know if there are any suggestions / requests.
Thanks!

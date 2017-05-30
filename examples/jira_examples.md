# ticketutil.jira code examples

Authenticate through Basic HTTP Authentication

```python
>>> from ticketutil.jira import JiraTicket
>>> t = JiraTicket(<jira_url>,
                   <project_key>,
                   auth=('username', 'password'))
```

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
         type='Task',
         priority='Major',
         assignee='username')
t.add_comment('Test Comment')
t.edit(priority='Critical',
       type='Bug')
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
t.add_comment('Test Comment')
t.edit(priority='Critical',
       type='Bug')
       
# Work with a different ticket.
t.set_ticket_id(<new_ticket_id>)
t.remove_watcher('username')
t.add_watcher('username')
t.change_status('Done')

# Close Requests session.
t.close_requests_session()
```

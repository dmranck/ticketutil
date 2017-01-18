# ticketutil.redmine code examples

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
t.add_comment('Test Comment')
t.edit(priority='Normal',
       due_date='2017-02-25')
t.add_watcher('username1')
t.remove_watcher('username2')
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
t.add_comment('Test Comment')
t.edit(priority='High',
       done_ratio='90')
       
# Work with a different ticket.
t.set_ticket_id(<new_ticket_id>)
t.change_status('Resolved')

# Close Requests session.
t.close_requests_session()
```

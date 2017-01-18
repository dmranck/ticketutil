# ticketutil.bugzilla code examples

Currently, ticketutil supports HTTP Basic authentication for Bugzilla. 
When creating a BugzillaTicket object, pass in your username
and password as a tuple into the auth argument. The code then retrieves
a token that will be used as authentication for subsequent API calls. 
For more details, see: 
http://bugzilla.readthedocs.io/en/latest/api/index.html.

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
t.add_comment('Test Comment')
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
t.add_comment('Test Comment')
t.edit(priority='low',
       severity='low')
       
# Work with a different ticket.
t.set_ticket_id(<new_ticket_id>)
t.change_status(status='CLOSED', resolution='NOTABUG')

# Close Requests session.
t.close_requests_session()
```

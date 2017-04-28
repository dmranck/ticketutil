# ticketutil.servicenow code examples

Currently, ticketutil supports HTTP Basic Authentication for ServiceNow.
When creating a ServiceNowTicket object, pass in your username
and password as a tuple into the auth argument. The code then retrieves
a token that will be used as authentication for subsequent API calls.
For more details see [documentation](../docs/servicenow.md).

```python
>>> from ticketutil.servicenow import ServiceNowTicket
>>> t = ServiceNowTicket(<servicenow_url>,
                         <table_name>,
                         auth=(<username>, <password>))
```

You should see the following response:
```python
INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): <servicenow_url>
INFO:root:Successfully authenticated to ServiceNow
```
You now have a `ServiceNowTicket` object that is associated with the
`<table_name>` table.

Some example workflows are found below. Notice that the first step is to
create a ServiceNowTicket object with an url table name (and with a ticket id
when working with existing tickets), and the last step is closing the Requests
session with `t.close_requests_session()`.

When creating a ServiceNow ticket, `short_description`, `description`,
`category` and `item` are required parameters. Also, the Reporter is
automatically filled in as the current kerberos principal or username supplied
during authentication.

#### Create new ServiceNow ticket
```python
from ticketutil.servicenow import ServiceNowTicket

# Create a ticket object and pass the url and table name in as strings
t = ServiceNowTicket(<servicenow_url>,
                     <table_name>,
                     auth=(<username>, <password>))

# Create a ticket and perform some common ticketing operations
t.create(short_description='TEST adding SNow API into ticketutil',
         description='Ticket description',
         category='Communication',
         item='ServiceNow')
t.edit(assigned_to='pzubaty',
       priority='3')
t.add_cc(['username1@mail.com', 'username2@mail.com'])
t.remove_cc('username1@mail.com')
t.change_status('Work in Progress')

# Retrieve ticket content
t.get_ticket_content()

# Close Requests session
t.close_requests_session()
```

#### Update existing ServiceNow tickets
```python
from ticketutil.servicenow import ServiceNowTicket

t = ServiceNowTicket(<servicenow_url>,
                     <table_name>,
                     auth=(<username>, <password>),
                     ticket_id=<ticket_id>)
t.add_comment('Test Comment')
t.edit(priority='4',
       impact='4')

# Work with a different ticket
t.set_ticket_id(<new_ticket_id>)
t.change_status('Pending')

# Close Requests session
t.close_requests_session()
```

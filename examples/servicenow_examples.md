# ticketutil.servicenow code examples

Currently, ticketutil supports HTTP Basic Authentication for ServiceNow.
The user needs to provide username and password. Class ServiceNowTicket allows
to create and edit ServiceNow tickets. Field names and possible values can be
found when Inspecting elements of the ticket creation webpage in the ServiceNow
WebUI. Some of them can be found in the examples below. More details will be
added later.

#### Create new ServiceNow ticket
```python
from ticketutil.servicenow import ServiceNowTicket

table = <table_name>
server = <servicenow_url>
user = <user>
pwd = <password>
auth = (user,pwd)

t = ServiceNowTicket(server, table, auth)
description = ('This is just a simple test for ticketutil library. Calling '
                'ServiceNowTicket class you are able to create tickets in '
                'the ServiceNow automatically. You need however to provide '
                'username and password (at the moment only basic auth is '
                'supported. Module created by pzubaty@redhat.com')

t.create(short_description='TEST adding SNow API into ticketutil',
         description=description,
         category='Communication',
         item='ServiceNow')
t.close_requests_session()
```

Provided `user` and `pwd` are replaced with valid values, similar response
should be seen:

```
INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): <servicenow_url>
INFO:root:Successfully authenticated to ServiceNow
INFO:root:Created issue <number> - <ticket_url>
```

#### Create new comment, edit ticket and change status
```python
from ticketutil.servicenow import ServiceNowTicket

table = <table_name>
server = <servicenow_url>
user = <user>
pwd = <password>
auth = (user,pwd)

t = ServiceNowTicket(server, table, auth, ticket_id)
t.add_comment('Lorem ipsum dolor TEST')
ticket.edit(assigned_to = 'pzubaty', priority = '3',
            email_from = 'pzubaty@redhat.com',
            hostname_affected = '127.0.0.1')
t.change_status('Pending')
t.close_requests_session()
```

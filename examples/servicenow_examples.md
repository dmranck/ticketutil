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

table = '/x_redha_pnt_devops_table'
server = 'https://envqa.service-now.com'
user = 'test_servicenow'
pwd = 'passwordString'
auth = (user,pwd)

ticket = ServiceNowTicket(server, table, auth)
description = ('This is just a simple test for ticketutil library. Calling '
                'ServiceNowTicket class you are able to create tickets in '
                'the ServiceNow automatically. You need however to provide '
                'username and password (at the moment only basic auth is '
                'supported. Module created by pzubaty@redhat.com')

ticket.create(short_description='TEST adding SNow API into ticketutil',
                description=description,
                u_category='Communication',
                u_item='ServiceNow')
ticket.close_requests_session()
```

Provided `user` and `pwd` are replaced with valid values, similar response
should be seen:

```
INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): redhatqa.service-now.com
INFO:root:Successfully authenticated to ServiceNow
INFO:root:Created issue <number> - <service_now_url>
```

#### Create new comment, edit ticket and change status
```python
from ticketutil.servicenow import ServiceNowTicket

table = '/x_redha_pnt_devops_table'
server = 'https://envqa.service-now.com'
user = 'test_servicenow'
pwd = 'passwordString'
auth = (user,pwd)

ticket = ServiceNowTicket(server, table, auth, ticket_id)
ticket.add_comment('Lorem ipsum dolor TEST')
fields = {'assigned_to':'pzubaty', 'priority':'3'}
ticket.edit(**fields)
ticket.change_status('Pending')
ticket.close_requests_session()
```

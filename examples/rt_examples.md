# ticketutil.rt code examples

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
         admincc=['username@mail.com', 'username2@mail.com'])
t.add_comment('Test Comment')
t.edit(priority='4',
       cc='username1@mail.com')
t.add_attachment('file_to_attach.txt')
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
t.add_comment('Test Comment')
t.edit(priority='4',
       cc='username@mail.com')
       
# Work with a different ticket.
t.set_ticket_id(<new_ticket_id>)
t.change_status('Resolved')

# Close Requests session.
t.close_requests_session()
```

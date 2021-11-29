Release History
---------------

1.5.0 (11-29-2021)
++++++++++++++++++

* Added support for personal access tokens in Jira.

1.4.5 (07-07-2020)
++++++++++++++++++

* Fixed RuntimeError in Python 3.8.
* Added support for trailing slash in URLs.
* Made verify requests to Jira tickets configurable.

1.4.4 (04-25-2019)
++++++++++++++++++

* Updated HTTP Basic Auth in ticket.py to disable SSL cert verification.

1.4.3 (01-08-2019)
++++++++++++++++++

* Added get_ticket_content() method to jira.py, rt.py, redmine.py, and
  bugzilla.py.
* Added add_attachment() method to servicenow.py.
* Added unit tests for ticket.py, jira.py, rt.py, redmine.py, and bugzilla.py.
* Added module-level loggers throughout all files.
* Added components support to Jira.
* Added support for creating subtasks in Jira.

1.3.0 (06-29-2017)
++++++++++++++++++

* New documentation has been created at http://ticketutil.readthedocs.io.
* All main user-accessible ticketutil methods now have useful return
  statements containing the request status (Success or Failure), the error
  message if the status is a Failure, and the URL of the ticket. See
  http://ticketutil.readthedocs.io/en/latest/Usage.html#return-statements
  for more details.
* HTTP Basic Auth support has been added to JIRA.

1.2.0 (04-28-2017)
++++++++++++++++++

* ServiceNow support has been added to ticketutil!

  - ticketutil/servicenow.py has been created, supporting main ticketing
    functions found in other tools.
  - tests/test_servicenow.py has been created, containing unit tests for
    servicenow.py.
  - Two new documentation files have been created: docs/servicenow.md and
    examples/servicenow_examples.md.

1.1.0 (04-18-2017)
++++++++++++++++++

* JIRA, Bugzilla, RT, Redmine

  - Added get_ticket_url() method to return ticket url for Ticket object.
  - Added get_ticket_id() method to return ticket id for Ticket object.
  - Added _verify_project() and _verify_ticket_id() methods to all tools.
    These methods are called when a new Ticket object is created to verify
    that the project and optional ticket_id parameters are valid.
  - Created TicketException class, which is raised if the url passed in
    during creation of a Ticket object can not be accessed. This exception
    is also raised if project or ticket_id can not be verified.
  - The environment variable TICKETUTIL_DEBUG has been replaced with
    TICKETUTIL_LOG_LEVEL, with a default value of 'INFO'. This allows you to
    turn on debug logging by setting this variable to 'DEBUG' and effectively
    turn off logging by setting it to 'CRITICAL'.

* JIRA

  - Modified _get_status_id() in jira.py to return the status_id
    corresponding to the state you are transitioning to, instead of the
    status_id corresponding to the transition itself.

* Bugzilla

  - Added add_attachment() method.
  - Added support for api_key authentication.
  - Added support for adding groups to ticket in create() and edit().

* RT

  - Added add_attachment() method.

* Redmine

  - Added add_attachment() method.

1.0.6 (01-20-2017)
++++++++++++++++++
- Trying to fix more PyPI issues.

1.0.5 (01-20-2017)
++++++++++++++++++
- Fixing README on PyPI.

1.0.4 (01-20-2017)
++++++++++++++++++
- Updated JIRA example and docstring to clarify that 'type' (and not
  'issuetype') is a supported create() and edit() field. No code changes.

1.0.3 (01-19-2017)
++++++++++++++++++
- First publish to PyPI!

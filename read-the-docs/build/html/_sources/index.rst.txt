
Welcome to ticketutil's documentation!
======================================

.. image:: https://img.shields.io/badge/python-2.7%2C%203.3%2C%203.4%2C%203.5%2C%203.6-blue.svg
    :target: https://pypi.python.org/pypi/ticketutil/1.2.0

.. image:: https://img.shields.io/badge/pypi-v1.2.0-blue.svg
    :target: https://pypi.python.org/pypi/ticketutil/1.2.0

ticketutil is a Python module that allows you to easily interact with
various ticketing tools using their REST APIs. Currently, the supported
tools are **JIRA**, **RT**, **Redmine**, **Bugzilla**, and **ServiceNow**. All tools support
HTTP Basic authentication, while JIRA and RT also support Kerberos
authentication.

This module allows you to create tickets, add comments, edit ticket
fields, and change the status of tickets in each tool. Additional
lower-level tool-specific functions are supported - adding and removing
watchers in JIRA, adding attachments in JIRA, etc.

Simplify all of your ticketing operations with ticketutil:

.. code-block:: python

    from ticketutil.jira import JiraTicket
    t = JiraTicket(<jira_url>, <project_key>, auth='kerberos')

    # Create a ticket and perform some common ticketing operations.
    t.create(summary='Ticket summary',
             description='Ticket description')
    t.add_comment('Test Comment')
    t.change_status('Done')

    # Close Requests session.
    t.close_requests_session()


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Installation
   Usage
   Bugzilla



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

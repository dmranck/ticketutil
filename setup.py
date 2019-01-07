#!/usr/bin/env python
"""Setup for ticketutil."""

from setuptools import setup

with open('README.rst') as file:
    long_description = file.read()
with open('HISTORY.rst') as file:
    long_description += '\n{0}'.format(file.read())

setup(
    name='ticketutil',
    packages=['ticketutil'],
    version='1.4.0',
    description='Python ticketing utility supporting JIRA, RT, Redmine, Bugzilla, and ServiceNow',
    long_description=long_description,
    author='Danny Ranck',
    author_email='dmranck@gmail.com',
    url='https://github.com/dmranck/ticketutil',
    download_url='https://github.com/dmranck/ticketutil/tarball/1.4.0',
    keywords=['jira', 'bugzilla', 'rt', 'redmine', 'servicenow', 'ticket', 'rest'],
    install_requires=['gssapi>=1.2.0', 'requests>=2.6.0', 'requests-kerberos>=0.8.0']
)

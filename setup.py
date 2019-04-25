#!/usr/bin/env python
"""Setup for ticketutil."""

from os import path
from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst')) as f:
    long_description = f.read()
with open(path.join(this_directory, 'HISTORY.rst')) as f:
    long_description += '\n{0}'.format(f.read())

setup(
    name='ticketutil',
    packages=['ticketutil'],
    version='1.4.4',
    description='Python ticketing utility supporting JIRA, RT, Redmine, Bugzilla, and ServiceNow',
    long_description=long_description,
    author='Danny Ranck',
    author_email='dmranck@gmail.com',
    url='https://github.com/dmranck/ticketutil',
    download_url='https://github.com/dmranck/ticketutil/tarball/1.4.4',
    keywords=['jira', 'bugzilla', 'rt', 'redmine', 'servicenow', 'ticket', 'rest'],
    install_requires=['gssapi>=1.2.0', 'requests>=2.6.0', 'requests-kerberos>=0.8.0'],
    data_files=[('.', ['HISTORY.rst'])]
)

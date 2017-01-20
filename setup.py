#!/usr/bin/env python
"""Setup for ticketutil."""

from setuptools import setup

setup(
    name='ticketutil',
    packages=['ticketutil'],
    version='1.0.4',
    description='Python ticketing utility supporting JIRA, RT, Redmine, and Bugzilla',
    author='Danny Ranck',
    author_email='dmranck@gmail.com',
    url='https://github.com/dmranck/ticketutil',
    download_url='https://github.com/dmranck/ticketutil/tarball/1.0.4',
    keywords=['jira', 'bugzilla', 'rt', 'redmine', 'ticket', 'rest'],
    install_requires=['gssapi>=1.2.0', 'requests>=2.9.1', 'requests-kerberos>=0.8.0']
)

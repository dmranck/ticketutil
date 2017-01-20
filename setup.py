#!/usr/bin/env python
"""Setup for ticketutil."""

from setuptools import setup

with open('README.rst', 'r') as f:
    readme = f.read()
with open('HISTORY.rst', 'r') as f:
    history = f.read()

setup(
    name='ticketutil',
    packages=['ticketutil'],
    version='1.0.5',
    description='Python ticketing utility supporting JIRA, RT, Redmine, and Bugzilla',
    author='Danny Ranck',
    author_email='dmranck@gmail.com',
    url='https://github.com/dmranck/ticketutil',
    download_url='https://github.com/dmranck/ticketutil/tarball/1.0.5',
    keywords=['jira', 'bugzilla', 'rt', 'redmine', 'ticket', 'rest'],
    install_requires=['gssapi>=1.2.0', 'requests>=2.9.1', 'requests-kerberos>=0.8.0'],
    long_description=readme + '\n\n' + history,
)

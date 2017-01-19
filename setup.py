#!/usr/bin/env python
"""Setup for ticketutil."""

from setuptools import setup


def _get_requirements(file_name):
    requirements = []
    for line in open(file_name).readlines():
        requirements.append(line)
    return requirements

setup(
    name='ticketutil',
    packages=['ticketutil'],
    version='1.0.2',
    description='Python ticketing utility supporting JIRA, RT, Redmine, and Bugzilla',
    author='Danny Ranck',
    author_email='dmranck@gmail.com',
    url='https://github.com/dmranck/ticketutil',
    download_url='https://github.com/dmranck/ticketutil/tarball/1.0.2',
    keywords=['jira', 'bugzilla', 'rt', 'redmine', 'ticket', 'rest'],
    install_requires=_get_requirements('requirements.txt')
)

# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='discovery-client',
    version='0.1',
    author='tomwei7',
    url='https://github.com/tomwei7/discovery-client',
    author_email='tomwei7g@gmail.com',
    description='python client for discovery a registry for resilient mid-tier load balancing and failover. https://github.com/bilibili/discovery',
    python_requires='>=3.5',
    packages=find_packages(exclude=["tests"]),
)

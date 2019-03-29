# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


def readme():
    """print long description"""
    with open('README.md') as f:
        return f.read()


setup(
    name='python-discovery-client',
    version='0.2',
    license="MIT",
    author='tomwei7',
    url='https://github.com/tomwei7/discovery-client',
    author_email='tomwei7g@gmail.com',
    description='python client for discovery a registry for resilient mid-tier load balancing and failover. https://github.com/bilibili/discovery',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
    ],
    long_description=readme(),
    long_description_content_type='text/markdown',
    python_requires='>=3.5',
    packages=find_packages(exclude=["tests"]),
)

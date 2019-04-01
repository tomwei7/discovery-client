# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


def readme():
    """print long description"""
    with open('README.md') as f:
        return f.read()


setup(
    name='python-discovery-client',
    version='0.5',
    license="MIT",
    author='tomwei7',
    url='https://github.com/tomwei7/discovery-client',
    author_email='tomwei7g@gmail.com',
    description='python client for discovery a registry for resilient mid-tier load balancing and failover. https://github.com/bilibili/discovery',
    install_requires=[
        'future',
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    long_description=readme(),
    long_description_content_type='text/markdown',
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
)

#!/usr/bin/python

from setuptools import setup, find_packages

from distutils.util import convert_path
from fnmatch import fnmatchcase
import os
import sys

try:
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

setup(
    name='vmm',
    version='1',

    description='A utility for managing libvirt virtual instances',
    long_description=long_description,

    author='Lars Kellogg-Stedman',
    author_email='lars@seas.harvard.edu',

    install_requires=open('requirements.txt').readlines(),

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'vmm = vmm.main:main'
            ],
        },
    )


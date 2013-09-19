#!/usr/bin/env python

from distutils.core import setup

setup(
    name='gz-spell',
    version='0.5',
    author='group-zero',
    author_email='',
    url='',
    package_dir={'': 'src'},
    packages=['gzspell'],
    scripts=['src/bin/gzserver'],
)

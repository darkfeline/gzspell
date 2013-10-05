#!/usr/bin/env python

from distutils.core import setup

setup(
    name='gz-spell',
    version='0.1',
    author='group-zero',
    author_email='',
    url='',
    package_dir={'': 'src'},
    packages=['gzspell'],
    scripts=['src/bin/' + x for x in [
        'gzserver', 'gzcli', 'gzshell',
        'make_graph', 'import_lexicon', 'dumbserver', 'add_corpus',
        ]],
)

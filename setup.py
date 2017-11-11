#!/usr/bin/env python

from setuptools import setup, find_packages

EXCLUDED = ['*.tests', '*.tests.*', 'tests.*', 'tests']

setup(name                 ='zamia-prolog',
      version              ='0.1.0',
      description          ='Embeddable Prolog dialect implemented in pure Python. Stores its knowlegdebase using SQLAlchemy for scalability.',
      long_description     = open('README.md').read(),
      author               = 'Guenter Bartsch',
      author_email         = 'guenter@zamia.org',
      maintainer           = 'Guenter Bartsch',
      maintainer_email     = 'guenter@zamia.org',
      url                  = 'https://github.com/gooofy/zamia-prolog',
      classifiers          = [
                              'Topic :: Software Development :: Interpreters',
                              'Topic :: Software Development :: Compilers',
                              'Intended Audience :: Developers',
                              'Operating System :: POSIX :: Linux',
                              'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
                              'Programming Language :: Python :: 2',
                              'Programming Language :: Python :: 2.7',
                              'Programming Language :: Python :: 3',
                              'Programming Language :: Python :: 3.4',
                              'Programming Language :: Prolog',
                             ],
      platforms            = 'Linux',
      license              = 'LGPLv3',
      package_dir          = {'zamiaprolog': 'zamiaprolog'},
      test_suite           = 'tests',
      packages             = find_packages('.', EXCLUDED),
      )


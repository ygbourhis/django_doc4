#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
import os

here = os.path.abspath(os.path.dirname(__file__))

setup(name='doc4',
    version='0.1',
    author='Yves-Gwenael Bourhis',
    author_email='ybourhis at mandriva.com',
    description = "a rpm package database with it's api",
    license = 'GNU General Public License version 2.0',
    url = 'https://rnd.mandriva.com/xwiki/bin/view/wiki/Doc4',
    download_url = 'http://svn.mandriva.com/svn/soft/lab/doc4/django_doc4/',
    requires = ['django (>=1.3)', 'django_piston', 'cheetah', 'rpm', 'chardet', 'pygments', 'yaml'],
    packages = [
        'doc4',
        'doc4.management',
        'doc4.management.commands',
        'doc4.templatetags',
        'doc4.utils',
        'doc4.tools',
        'doc4.api',
        'doc4.migrations',
        ],
    package_dir = {'doc4': os.path.join(here, 'doc4')},
    package_data = {'doc4': [ 'templates/*.html',
                              'templates/doc4/*.html',
                              'templates/doc4/tags/*.html',
                              'static/css/*.css',
                              'static/js/*.js',
                              'static/img/*',
                              'utils/*.xml',
                              'fixtures/*.json',
                              'fixtures/*.csv',
                              'locale/*/LC_MESSAGES/*.po',
                              'locale/*/LC_MESSAGES/*.mo',
                              'management/commands/*template*',
                            ]},
    )

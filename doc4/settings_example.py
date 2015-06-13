#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
    Doc4 - Main configuration

    Package database

    @copyright: 2011 by Yves-Gwenael Bourhis <ybourhis@mandriva.com>
    @license: GNU GPL, see COPYING for details.
"""

import os
import logging

# Doc4 settings
ONLY_NEW_PACKAGES = True
EXTRACTION_DIR = '/var/doc4/upmi/'
SKIP_IF_EXTRACTED = False
KEEP_RPM_FILES = False
KEEP_EXTRACTED_XML = False
REPLACE_PACKAGES = True
DO_EXTRACT = False
DO_DECOMPRESS_SRC = False
DO_ANALYSE = False

#because of http://code.djangoproject.com/ticket/9176 django bug, you have to chose between using:
DOC4_BASE_URL = ''
#DOC4_BASE_URL = 'doc4'
#or:
#ABSOLUTE_URL_OVERRIDES = {'doc4.repository' : lambda o: '/doc4/repository/%s/%s/%s/%s/%s/' % (o.provider, o.distribution, o.architecture, o.branch, o.section),}


# Django settings

# Change this to something secret
SECRET_KEY = '<SECRET>'

PROJECT_DIR = os.path.dirname(__file__)

DEV = True
DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOG_PATH = 'logs'
LOG_LEVEL = logging.DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

if DEV:
    DATABASES = {
        'default': {
            #'ENGINE': 'django.db.backends.postgresql_psycopg2',
            #'ENGINE': 'django.db.backends.mysql',
            # If you use MySQL, MySQL REQUIRES using InnoDB tables because
            # Doc4 makes use of transactions and MyISAM does not handle them:
            #'OPTIONS': {'init_command': 'SET storage_engine=INNODB',},
            #'NAME': '',
            #'USER': '',
            #'PASSWORD': '',
            #'PORT': '3306', # Set to empty string for default. Not used with sqlite3.
            #'HOST': 'localhost',
        }
    }
else:
    DATABASES = {
        'default': {
            #'ENGINE': 'django.db.backends.postgresql_psycopg2',
            #'ENGINE': 'django.db.backends.mysql',
            # If you use MySQL, MySQL REQUIRES using InnoDB tables because
            # Doc4 makes use of transactions and MyISAM does not handle them:
            #'OPTIONS': {'init_command': 'SET storage_engine=INNODB',},
            #'NAME': '',
            #'USER': '',
            #'PASSWORD': '',
            #'PORT': '3306', # Set to empty string for default. Not used with sqlite3.
            #'HOST': 'localhost',
        }
    }

logging.basicConfig(
    level = LOG_LEVEL,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
    filename = os.path.join(PROJECT_DIR, LOG_PATH, 'doc4.log'),
    filemode = 'a+'
)
logging.getLogger('django.db.backends').setLevel(logging.INFO)

TIME_ZONE = 'Europe/Paris'
LANGUAGE_CODE = 'en'
gettext = lambda s: s
LANGUAGES = (('fr', gettext('French')),
             ('en', gettext('English')),
            )

LOCALE_PATHS = (
    os.path.join(PROJECT_DIR, 'locale'),
)

SITE_ID = 1

USE_I18N = True
USE_L10N = True

MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')
STATIC_URL = '/static/'

ADMIN_MEDIA_PREFIX = '/static/admin/'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'doc4.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    )


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.staticfiles',
    'doc4',
    'piston',
    'south',
)

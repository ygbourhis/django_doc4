#!/usr/bin/python
import os
import sys

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PROJECT_PATH)
PROJECT_NAME = os.path.basename(PROJECT_PATH.split(PROJECT_ROOT)[1])

#If not using virtual environment, comment the two following lines:
activate_this = os.path.join(PROJECT_ROOT, 'bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

sys.path.insert(0, PROJECT_PATH)
sys.path.insert(0, PROJECT_ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = '%s.settings' % PROJECT_NAME

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

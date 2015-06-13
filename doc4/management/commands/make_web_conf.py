# -*- coding: utf-8 -*-

## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE included in the packaging of
## this file. 
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
## See the NOTICE file distributed with this work for additional
## information regarding copyright ownership.

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.template import Context, Template, loader
from django.conf import settings
from django.contrib.auth.models import User
import os

CURDIR = os.path.realpath(os.path.dirname(__file__))

context = Context()
context['PROJECT_PATH'] = os.path.realpath(settings.PROJECT_DIR)
context['PROJECT_ROOT'] = os.path.dirname(context['PROJECT_PATH'])
context['STATIC_PATH'] = os.path.realpath(settings.STATIC_ROOT)
context['PROJECT_DIR_NAME'] = os.path.basename(context['PROJECT_PATH'].split(context['PROJECT_ROOT'])[1])
context['PROJECT_NAME'] = context['PROJECT_DIR_NAME']
context['VIRTUAL_ENV'] = os.environ.get('VIRTUAL_ENV')
context['HOSTNAME'] = os.environ.get('HOSTNAME')
VHOSTNAME = context['HOSTNAME'].split('.')
VHOSTNAME[0] = context['PROJECT_NAME']
if len(VHOSTNAME) >1:
    context['DOMAINNAME'] = '.'.join(VHOSTNAME[1:])
else:
    context['DOMAINNAME'] = 'mandriva.com'
VHOSTNAME = '.'.join(VHOSTNAME)
context['VHOSTNAME'] = VHOSTNAME
context['activate_this'] = os.path.join(context['PROJECT_ROOT'], 'bin/activate_this.py')

adminusers = User.objects.filter(is_superuser=True, is_staff=True, is_active=True).order_by('pk')
if adminusers.count():
    context['ADMIN'] = adminusers[0].email
else:
    context['ADMIN'] = 'webmaster@%' % context['DOMAINNAME']

cmd_name = __name__.split('.')[-1]

class Command(BaseCommand):
    
    args = ''
    help = """create apache.wsgi and/or %s_vhost.conf
    examples:
    manage.py %s --wsgi
    manage.py %s --apache
    manage.py %s --apache --mail=%s --project=%s --hostname=%s
    """ % (context['PROJECT_NAME'], 
        cmd_name,
        cmd_name,
        cmd_name, context['ADMIN'], context['PROJECT_NAME'], context['VHOSTNAME'],
    )
    
    option_list = BaseCommand.option_list + (
        make_option("-A", "--apache", default=False, action="store_true", dest="apache", help="generate apache vhost configuration"),
        make_option("-W", "--wsgi", default=False, action="store_true", dest="wsgi", help="generate apache.wsgi file"),
        make_option("-M", "--mail", dest="mail", help="web site administrator's email (default : %s)" % context['ADMIN'], metavar="MAIL"),
        make_option("-P", "--project", dest="project", help="project name (default : %s)" % context['PROJECT_NAME'], metavar="PROJECT"),
        make_option("-H", "--hostname", dest="hostname", help="server hostname (default : %s)" % context['VHOSTNAME'], metavar="HOSTNAME"),
        )
    
    def handle(self, *args, **options):
        if options.get('mail'):
            context['ADMIN'] = options.get('mail')
        if options.get('project'):
            context['PROJECT_NAME'] = options.get('project')
        if options.get('hostname'):
            context['VHOSTNAME'] = options.get('hostname')
        if options.get('wsgi'):
            with open(os.path.join(CURDIR, 'apache.wsgi.template'), 'r') as fp:
                wsgi_template = Template(fp.read())
            print wsgi_template.render(context)
        elif options.get('apache'):
            with open(os.path.join(CURDIR, 'apache_vhost.conf.template'), 'r') as fp:
                wsgi_template = Template(fp.read())
            print wsgi_template.render(context)
        else:
            self.print_help('manage.py', cmd_name)


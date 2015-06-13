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
from doc4.models import Repository
#from doc4.utils.commandwrapper import WrapCommand
#import os
#from django.conf import settings

import logging
log = logging.getLogger(__name__)

cmd_name = __name__.split('.')[-1]


class Command(BaseCommand):

    args = ''
    help = """Sync the selected repos to local file storage
    Example:
    %s -i NUM
    Or:
    %s --provider=mandriva  --distribution=mes5 --architecture=i586
    OR:
    %s -A
    """ % (cmd_name, cmd_name, cmd_name)

    option_list = BaseCommand.option_list + (
        make_option("-i", "--id", dest="id", type="int", help="id", metavar="ID"),
        make_option("-p", "--provider", dest="provider", help="provider", metavar="PROVIDER"),
        make_option("-d", "--distribution", dest="distribution", help="distribution", metavar="DISTRIBUTION"),
        make_option("-u", "--url", dest="url", help="url", metavar="FILTER"),
        make_option("-t", "--port", dest="port", help="port", metavar="PORT"),
        make_option("-l", "--login", dest="login", help="login", metavar="LOGIN"),
        make_option("-X", "--password", dest="password", help="password", metavar="PASSWORD"),
        make_option("-a", "--architecture", dest="architecture", help="architecture", metavar="ARCHITECTURE"),
        make_option("-b", "--branch", dest="branch", help="branch", metavar="BRANCH"),
        make_option("-s", "--section", dest="section", help="section", metavar="SECTION"),
        make_option("-P", "--path", dest="path", help="path", metavar="PATH"),
        make_option("-A", "--all", default=False, action="store_true", dest="all", help="all"),
        )

    def handle(self, *args, **options):

        if options.get('all'):
            repos = Repository.objects.all()
            for repo in repos:
                repo.rsync(self.stdout)

        elif not options.get('all'):
            opts = ['id', 'provider','distribution','url','port','login','password','architecture','branch','section','path',]
            query_dict = {}
            for opt in options.keys():
                if opt in opts and options.get(opt) is not None:
                    query_dict[opt] = options[opt]
            if len(query_dict):
                repos = Repository.objects.filter(**query_dict)
                if repos:
                    for repo in repos:
                        repo.rsync(self.stdout)
                else:
                    log.error("No repositories found in DB. Load some with : manage.py load_repository_csvdata")
            else:
                self.print_help('manage.py', cmd_name)

        else :
            self.print_help('manage.py', cmd_name)

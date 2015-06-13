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
from csv import DictReader

class Command(BaseCommand):
    
    args = '-f CSV_FILE'
    help = 'imports csv data in the Reopsitory model (doc4_repositories database table)'
    
    option_list = BaseCommand.option_list + (
        make_option("-f", "--file", dest="filename", help="import from CSV_FILE", metavar="CSV_FILE"),
        )
    
    def handle(self, *args, **options):
        if options.get('filename') is not None:
            with open(options['filename'], 'r') as fp:
                fields = ['provider', 'distribution', 'url', 'port', 'login', 'password', 'architecture', 'branch', 'section', 'path']
                csv = DictReader(fp, fieldnames=fields)
                count = 0
                for row in csv:
                    count += 1
                    repository = Repository(**row)
                    repository.save()
                self.stdout.write('imported %s repositories in database\n' % count)
        else :
            self.print_help('manage.py', __name__.split('.')[-1])

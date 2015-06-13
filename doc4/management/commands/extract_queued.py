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
from doc4.models import Repository, Snapshot, Queue, maxsize, state
from doc4.utils.rpmextractor import RpmExtractor
from doc4.utils.util import *
import traceback
import shutil
import os

from django.conf import settings
extractionskip = settings.SKIP_IF_EXTRACTED
keep_rpm_files = settings.KEEP_RPM_FILES

cmd_name = __name__.split('.')[-1]

queue_query = """
select distinct(name), doc4_queue.snapshot_id
from  doc4_queue,  doc4_snapshots
where doc4_queue.action='extraction' and doc4_queue.state='queued' and doc4_queue.snapshot_id = doc4_snapshots.id
and doc4_snapshots.repository_id='14'
order by name;
"""

class Command(BaseCommand):

    args = ''
    help = """goes through the queue of packages to be extracted and extracts them
    Example:
    %s -m=0 -i NUM
    Or:
    %s --id=14
    %s --provider=mandriva  --distribution=mes5 --architecture=i586
    OR:
    %s -A
    """ % (cmd_name, cmd_name, cmd_name, cmd_name)

    option_list = BaseCommand.option_list + (
        make_option("-m", "--maxsize", dest="maxsize", type="int", help="maxsize of files to extract, bigger files will not be treated", metavar="MAXSIZE"),
        make_option("-S", "--state", dest="state", help="state of packages to extract", metavar="STATE"),
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

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.processed_packages = []

    def handle(self, *args, **options):
        global maxsize
        global state
        if options.get('maxsize') is not None:
            maxsize = options['maxsize']
        if options.get('state') is not None:
            state = options['state']

        if options.get('all'):
            repos = Repository.objects.all()
            self.process_extraction_queue(repos)

        elif not options.get('all'):
            opts = ['id', 'provider','distribution','url','port','login','password','architecture','branch','section','path',]
            query_dict = {}
            for opt in options.keys():
                if opt in opts and options.get(opt) is not None:
                    query_dict[opt] = options[opt]
            if len(query_dict):
                repos = Repository.objects.filter(**query_dict)
                self.process_extraction_queue(repos)
            else:
                self.print_help('manage.py', cmd_name)

        else :
            self.print_help('manage.py', cmd_name)

    def process_extraction_queue(self, repos):
        #uncomment the next line and set a primary key (pk) to test only with one repository:
        #repos = Repository.objects.filter(pk=14)
        for repo in repos:
            snapshots = Snapshot.objects.filter(repository=repo)
            queues = Queue.objects.filter(action='extraction', state=state, snapshot__in=snapshots).distinct()
            self.stdout.write("====================== Repository %s\n" % repo)
            for queue in queues:
                queue.extract_package(repo, self.processed_packages, self.stdout)



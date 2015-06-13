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
from doc4.models import Repository, Snapshot, Queue, TargetRepos, state, maxsize
#import extract_queued

from django.conf import settings
replace = settings.REPLACE_PACKAGES

cmd_name = __name__.split('.')[-1]

class Command(BaseCommand):
    
    args = ''
    help = 'Fully process repositories in TargetRepos table'
    
    option_list = BaseCommand.option_list
    
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.processed_packages = []
    
    def handle(self, *args, **options):
        global state
        global replace
        output=self.stdout
        
        target_repos = TargetRepos.objects.values_list('repository')
        repos = Repository.objects.filter(pk__in=target_repos)
        
        if repos.count():
            for repo in repos:
                #Sync repo:
                repo.rsync(self.stdout)
                #Queue the repo:
                repo.compute_queue()
                #Extract queue:
                snapshots = Snapshot.objects.filter(repository=repo)
                queues = Queue.objects.filter(action='extraction', state=state, snapshot__in=snapshots).distinct()
                self.stdout.write("====================== Repository %s\n" % repo)
                for queue in queues:
                    #self.extract_package(queue, repo)
                    queue.extract_package(repo, self.processed_packages, self.stdout)
                #Store extracted metadata:
                repo.process_store_queue(replace=replace, output=output)
                #Process history queue:
                repo.process_history_queue()
        else:
            log.error("No repositories selected, select repositories via the admin interface")



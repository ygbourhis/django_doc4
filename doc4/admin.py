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

from django.contrib import admin
from models import *

class LicenseAdmin(admin.ModelAdmin):
    list_display = ('abbreviation',)
    list_filter = ('abbreviation',)

class LicenseDefinitionAdmin(admin.ModelAdmin):
    list_display = ('abbreviation', 'description')
    list_filter = ('abbreviation', 'description')

class QueueAdmin(admin.ModelAdmin):
    list_display = ('name', 'action', 'state', 'start_time', 'end_time')
    list_filter = ('state',)
    search_fields = ['name',]

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('show_with_id',)
    def show_with_id(self, obj):
        return '%s (%d)' %(obj, obj.id)
    show_with_id.short_description = 'Repository'

class TargetReposAdmin(admin.ModelAdmin):
    list_display = ('repository_id',)
    raw_id_fields = ('repository',)
    def repository_id(self, obj):
        return '%s (%d)' %(obj.repository, obj.repository.id)
    repository_id.short_description = 'Repository'


admin.site.register(License, LicenseAdmin)
admin.site.register(LicenseDefinition, LicenseDefinitionAdmin)
admin.site.register(Bugstat)
admin.site.register(Changelog)
admin.site.register(Conflict)
admin.site.register(Contributor)
admin.site.register(File)
admin.site.register(RepositoryHistory)
admin.site.register(InstallabilityViolationEntry)
admin.site.register(Obsolete)
admin.site.register(PackageLicense)
admin.site.register(Package)
admin.site.register(Provide)
admin.site.register(Queue, QueueAdmin)
admin.site.register(Repository, RepositoryAdmin)
admin.site.register(Require)
admin.site.register(InUnScript)
admin.site.register(SlocStat)
admin.site.register(Snapshot)
admin.site.register(Suggest)
admin.site.register(TargetRepos, TargetReposAdmin)

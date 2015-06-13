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

from django.db import models, transaction
from django.db.models import Count
from django.conf import settings
from django.core.urlresolvers import reverse

from subprocess import PIPE
from utils.commandwrapper import WrapCommand
import xml.etree.cElementTree as ET
from Cheetah.Template import Template
from xml.sax.saxutils import escape
from doc4.utils.rpmextractor import RpmExtractor
from doc4.utils.util import *
import os
import sys
import traceback
import codecs
import re
import shutil

from datetime import datetime
from time import localtime, gmtime

from django.conf import settings
only_new_packages = settings.ONLY_NEW_PACKAGES
extractiondir = settings.EXTRACTION_DIR
extractionskip = settings.SKIP_IF_EXTRACTED
keep_rpm_files = settings.KEEP_RPM_FILES
keep_extracted_xml = settings.KEEP_EXTRACTED_XML
replace = settings.REPLACE_PACKAGES
maxsize = 0
state = "queued"

REPOSITORY_PACKAGE_SEARCH_URL = 'packages/repository/'

import logging

log = logging.getLogger(__name__)
app_name = 'doc4'
db_prefix = '%s_' % app_name

def makeIntOrNone(value):
    if not value:
        return None
    elif isinstance(value, str) and len(value) and value.isdigit():
        return int(value)
    elif isinstance(value, int):
        return value
    elif isinstance(value, float):
        return int(value)
    elif isinstance(value, long):
        return value
    else :
        return None

def makeStrWhatever(value):
    if isinstance(value, str):
        return value
    else:
        return ''

class DateModel(models.Model):
    def now(self):
        return datetime.now()
        #return datetime(*(gmtime()[:6]))
    class Meta:
        abstract = True

class License(models.Model):
    abbreviation = models.CharField(max_length=25, unique=True)
    def __unicode__(self):
        return '%s' % self.abbreviation

    class Meta:
        app_label = app_name
        db_table = u'%slicenses' % db_prefix


class LicenseDefinition(models.Model):
    abbreviation = models.ForeignKey(License)
    description = models.CharField(max_length=765)

    @classmethod
    def get_package_license(cls, license):
        licenses = license.split()
        query = cls.objects
        for l in licenses:
            query = query.filter(description__icontains=l)
        res = query.aggregate(Count('abbreviation', distinct='True'))
        if res['abbreviation__count'] == 1:
            return query[0].abbreviation.abbreviation
        else:
            return license

    def __unicode__(self):
        if self.id:
            return '%s : %s' % (self.abbreviation, self.description)
        else:
            return u'%s.%s object' % (__name__, self.__class__.__name__)

    class Meta:
        app_label = app_name
        db_table = u'%slicense_definition' % db_prefix

class Repository(models.Model):
    #id_repository = models.AutoField(primary_key=True)
    provider = models.CharField(max_length=765, blank=True)
    distribution = models.CharField(db_index=True, max_length=765)
    url = models.CharField(max_length=765, blank=True)
    port = models.IntegerField(null=True, blank=True)
    login = models.CharField(max_length=765, blank=True)
    password = models.CharField(max_length=765, blank=True)
    architecture = models.CharField(max_length=765, blank=True)
    branch = models.CharField(max_length=765, blank=True)
    section = models.CharField(max_length=765, blank=True)
    path = models.CharField(max_length=765, blank=True)

    repositorydir = os.path.join(settings.EXTRACTION_DIR, 'mirrors')
    
    lsline = re.compile(r'^(?P<permissions>[-ldrwx]{10})\s+'
        '(?P<numlinks>[0-9]*)\s+'
        '(?P<user>[a-z0-9_-]*)\s+'
        '(?P<group>[a-z0-9_-]*)\s+'
        '(?P<size>[0-9BKGTPEZYk,.]+)\s+'
        '(?P<date>[-/0-9]+)\s+'
        '(?P<time>[0-9:]+)\s+'
        '(?P<name>[+a-zA-Z0-9_.-]+\.rpm)\s*$')

    def __unicode__(self):
        return u"%s %s %s %s %s" % (self.provider, self.distribution, self.architecture, self.branch, self.section)
    
    #@models.permalink
    def get_absolute_url(self):
        #according to django doc, this should work, if this method has the permalink decorator.
        #BUT it fails because of this http://code.djangoproject.com/ticket/9176:
        """
        return ('repository_packages', (), {'Model' : self.__class__,
                                            'provider' : str(self.provider),
                                            'distribution' : str(self.distribution),
                                            'architecture' : str(self.architecture),
                                            'branch' : str(self.branch),
                                            'section' : str(self.section),
                                           })
        """
        #so quick workaround with permalink decorator commented out because of Django BUG:
        if hasattr(settings, 'DOC4_BASE_URL'):
            DOC4_BASE_URL = settings.DOC4_BASE_URL
        else:
            DOC4_BASE_URL = ''
        return os.path.join('/', DOC4_BASE_URL, REPOSITORY_PACKAGE_SEARCH_URL ,self.provider, self.distribution, self.architecture, self.branch, self.section)
        #problem : needs rewriting if urls.py changes for this url...
    
    def get_path(self):
        return "%s/%s/%s/%s/%s/" % (self.provider, self.distribution, self.architecture, self.branch, self.section)
    
    def rsync_command(self, list_only=False, package=None, files_from=None):
        if list_only:
            listonly = '--list-only'
            target = ''
        else:
            listonly = ''
            target = '--delete %s' % (os.path.join(self.repositorydir, self.provider, self.distribution, self.architecture, self.branch, self.section))
        
        if package:
            source = os.path.join(self.url, package)
        else:
            source = os.path.join(self.url, '')
        
        if files_from:
            filesfrom = '--files-from=%s' % files_from
        else:
            filesfrom = ''
        
        if self.login is not None and len(self.login.strip()) > 0:
            cmd = "export RSYNC_PASSWORD=%s; rsync -auvH --port=%s %s %s %s@%s %s" % (self.password, self.port, listonly, filesfrom, self.login, source, target)
        else:
            cmd = "rsync -auvH --port=%s %s %s %s %s" % (self.port, listonly, filesfrom, source, target)
        
        return cmd
    
    
    def list_remote_rpms(self):
        cmdlist = self.rsync_command(list_only=True)
        rsynclist = WrapCommand(cmdlist, shell=True)
        rsynclist.run()
        remote_packages = []
        lines = rsynclist.results[0].split('\n')
        for line in lines:
            rpm = self.lsline.search(line)
            if rpm:
                remote_packages.append(rpm.groupdict())
        remote_names = [remote_package['name'] for remote_package in remote_packages]
        stored_packages = self.package_set.filter(fullname__in=remote_names).order_by('pk').values('fullname','size')
        stored_packages = [(stored_package['fullname'], stored_package['size']) for stored_package in stored_packages]
        stored_packages = dict(stored_packages)
        for remote_package in remote_packages:
            if stored_packages.get(remote_package['name']):
                remote_package['stored'] = True
                if int(remote_package['size']) != stored_packages[remote_package['name']]:
                    remote_package['changed'] = True
                else:
                    remote_package['changed'] = False
            else:
                remote_package['stored'] = False
        return remote_packages
    
    def rsync(self, stdout=PIPE):
        remote_packages = self.list_remote_rpms()
        target = os.path.join(self.repositorydir, self.provider, self.distribution, self.architecture, self.branch, self.section)
        if not os.path.exists(target):
            os.makedirs(target)
        log.debug("Sync target : %s" % target)
        files_to_rsync = []
        for remote_package in remote_packages:
            if not remote_package['stored']:
                log.debug('%s is new, it will be rsynced' % remote_package['name'])
                files_to_rsync.append(remote_package['name'])
            elif remote_package.get('changed'):
                log.debug('%s has changed, it will be rsynced' % (remote_package['name']))
                files_to_rsync.append(remote_package['name'])
        if len(files_to_rsync):
            cmd = self.rsync_command(files_from='-')
            stdin = '\n'.join(files_to_rsync)
            rsyncer = WrapCommand(cmd, shell=True, stdin=stdin, stdout=stdout)
            rsyncer.run()
            return rsyncer.results
        else:
            log.debug('Nothing to rsync')
            return (None,None)

    def compute_queue(self):
        snapshot = Snapshot(repository=self, is_last=True)
        snapshot.save()
        packages = Package.objects.distinct().order_by('fullname')
        pkgs = [package.fullname for package in packages]
        files_dir = os.path.join(self.repositorydir, self.get_path())
        files = [x for x in os.listdir(files_dir) if x.endswith('.rpm')]
        for file in files:
            queue = Queue(snapshot=snapshot, name=file, action='history-store', state='queued')
            queue.save()
            if (only_new_packages and file not in pkgs) or not (only_new_packages):
            #if (only_new_packages and Package.objects.filter(fullname=file).count()==0) or not (only_new_packages):
                queue = Queue(snapshot=snapshot, name=file, action='extraction', state='queued')
                queue.save()
                queue = Queue(snapshot=snapshot, name=file, action='extraction-store', state='queued')
                queue.save()

    @classmethod
    def compute_queues(cls, **query_dict):
        target_repositories = cls.objects.filter(**query_dict)
        for repo in target_repositories:
            repo.compute_queue()

    def process_store_queue(self, replace=settings.REPLACE_PACKAGES, output=sys.stdout):
        """Goes through the queue table. For each entry having an action
        'extraction-store' set to 'queued', store the extracted metadata"""
        snapshots = Snapshot.objects.filter(repository=self)
        queues = Queue.objects.filter(action='extraction-store', state='queued', snapshot__in=snapshots).distinct()
        for queue in queues:
            try:
                #package_file, id_snapshot, id_repository = queue.name, queue.snapshot, repo
                outputdir = queue.package_dir()
                metadatafile = queue.package_xml_file()
                output.write("Storing data for %s\n" % outputdir)
                if os.path.exists(metadatafile):
                    result = queue.check_and_store_package(replace, output)
                    if not keep_extracted_xml and result is 0:
                        os.remove(metadatafile)
                else:
                    output.write("No metadata found for %s\n" % queue.name)
                    #self.set_package_state(queue.name, queue.snapshot, "extraction-store", "end_time", "failed", "No metadata found for %s" % queue.name)
                    queue.state="failed"
                    queue.error_message = "No metadata found for %s" % queue.name
                    queue.end_time = queue.now()
                    queue.save()
            except Exception, e:
                traceback.print_exc(file=output)
                #self.set_package_state(queue.name, queue.snapshot, "extraction-store", "end_time", "failed", str(e))
                queue.state="failed"
                queue.error_message = str(e)
                queue.end_time = queue.now()
                queue.save()
                output.write("process_store_queue Error: %s\n" % str(e))

    def process_history_queue(self):
        snapshots = Snapshot.objects.filter(repository=self)
        queues = Queue.objects.filter(action='history-store', state='queued', snapshot__in=snapshots).distinct()
        for queue in queues:
            packages = Package.objects.filter(fullname=queue.name)
            for package in packages:
                history = RepositoryHistory(snapshot=queue.snapshot, package=package)
                history.save()
            queue.delete()
        latest_snapshot = snapshots.latest('snapshot_time')
        not_latest_snapshots = snapshots.exclude(pk=latest_snapshot.pk)
        if not_latest_snapshots.count():
            not_latest_snapshots.update(is_last = False)
        latest_snapshot.is_last = True
        latest_snapshot.save()

    class Meta:
        app_label = app_name
        db_table = u'%srepositories' % db_prefix
        verbose_name_plural = "Repositories"


class TargetRepos(models.Model):
    repository = models.ForeignKey(Repository)

    class Meta:
        app_label = app_name
        db_table = u'%starget_repositories' % db_prefix
        verbose_name = "Target Repositories"
        verbose_name_plural = "Target Repositories"


class Snapshot(DateModel):
    #id_snapshot = models.AutoField(primary_key=True)
    #id_repository = models.IntegerField(null=True, blank=True) #generated by inspectdb
    repository = models.ForeignKey(Repository)
    snapshot_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=True, blank=True)
    #is_last = models.IntegerField(null=True, blank=True) #generated by inspectdb
    is_last = models.NullBooleanField(db_index=True, null=True, blank=True)
    sloc_count = models.IntegerField(null=True, blank=True)
    package_count = models.IntegerField(null=True, blank=True)
    file_count = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'%ssnapshots' % db_prefix


class Bugstat(DateModel):
    #id_bugcount = models.AutoField(primary_key=True)
    distribution = models.CharField(db_index=True, max_length=765)
    date = models.DateTimeField(db_index=True)
    property = models.CharField(max_length=765)
    value = models.FloatField(null=True, blank=True)
    class Meta:
        app_label = app_name
        db_table = u'%sbugstats' % db_prefix

class Package(DateModel):

    commonns = "{http://purl.org/doc4/0.1}"

    #id_package = models.AutoField(primary_key=True)
    id_maintainer = models.IntegerField(db_index=True, null=True, blank=True)
    repos = models.ManyToManyField(Repository)
    fullname = models.CharField(db_index=True, max_length=765, blank=True)
    name = models.CharField(db_index=True, max_length=765, blank=True)
    summary = models.TextField(blank=True)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=765, blank=True)
    category = models.CharField(db_index=True, max_length=765, blank=True)
    top_category = models.CharField(db_index=True, max_length=765, blank=True)
    license = models.CharField(max_length=765, blank=True)
    version = models.CharField(max_length=765, blank=True)
    releas = models.CharField(max_length=765, blank=True)
    epoch = models.IntegerField(null=True, blank=True)
    arch = models.CharField(db_index=True, max_length=765, blank=True)
    build_host = models.CharField(max_length=765, blank=True)
    #build_time = models.IntegerField(null=True, blank=True) # created by inspectdb
    build_time = models.DateTimeField(null=True, blank=True)
    sha1 = models.CharField(max_length=765, blank=True)
    checksum = models.CharField(db_index=True, max_length=765, blank=True)
    size = models.IntegerField(null=True, blank=True)
    installed_size = models.IntegerField(null=True, blank=True)
    archive_size = models.IntegerField(null=True, blank=True)
    source = models.CharField(max_length=765, blank=True)
    is_source = models.IntegerField(null=True, blank=True)
    author = models.CharField(max_length=765, blank=True)
    author_email = models.EmailField(max_length=765, blank=True)
    file_count = models.IntegerField(null=True, blank=True)
    sloc_count = models.IntegerField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(Package, self).__init__(*args, **kwargs)
        self.prein = ''
        self.postin = ''
        self.preun = ''
        self.postun = ''
        self.maintainer = ''
        self.top_category = ''
        self.requires = []
        self.provides = []
        self.conflicts = []
        self.obsoletes = []
        self.suggests = []
        self.files = []
    
    def author_has_email(self):
        if len(self.author_email)> 4:
            return True
        else:
            return False
    
    def obfuscated_author_email(self):
        obfuscated = ''
        for char in self.author_email:
            obfuscated += '&#%s;' % ord(char)
        return obfuscated
    
    def __unicode__(self):
        app_label = app_name
        return u"<Package(%s,%s, %s-%s-%s)>" % (self.fullname, self.name, self.version, self.releas, self.epoch)

    def get_repos(self):
        pckg_rephists = self.repositoryhistory_set.all()
        return [pckg_rephist.snapshot.repository for pckg_rephist in pckg_rephists]

    def read_xml_file(self, metadata_file):
        with open(metadata_file, "rb") as xml_file:
            data = xml_file.read()
        return self.read_xml(data)

    def read_xml(self, xmldata):
        entries = ET.fromstring((u"%s" % xmldata).encode("utf-8"))
        self.xmldata = xmldata
        for package_elt in entries:
            self.read_xml_main(package_elt)
            self.read_xml_scripts(package_elt)
            self.read_xml_changelog(package_elt)
            self.read_xml_files(package_elt)


    def read_xml_main(self, package_elt):
        self.name = u"%s" % package_elt.findtext("%sname" % self.commonns)
        self.arch = package_elt.findtext("%sarch" % self.commonns)
        self.rpmversion = package_elt.find("%stype" % self.commonns).get("version")
        version = package_elt.find("%sversion" % self.commonns)
        self.epoch = makeIntOrNone(version.get("epoch"))
        self.version = version.get("ver")
        self.releas = version.get("rel")
        #checksum_type = checksum_elt.get("type")
        self.checksum = package_elt.find("%schecksum" % self.commonns).text
        self.summary = u"%s" % package_elt.findtext("%ssummary" % self.commonns)
        self.description = u"%s" % package_elt.findtext("%sdescription" % self.commonns)
        pkger = package_elt.find("%spackager" % self.commonns)
        self.author = pkger.get("name")
        self.author_email = pkger.get("email")
        self.url = package_elt.findtext("%surl" % self.commonns)

        self.fullname = package_elt.findtext("%sfilename" % self.commonns)

        build_elt = package_elt.find("%sbuild" % self.commonns)

        build_time = makeIntOrNone(build_elt.get("time"))
        if build_time is not None:
            self.build_time = datetime.fromtimestamp(build_time)
        else:
            self.build_time = None
        self.build_host = build_elt.get("host")
        #package.file_time = file_time

        size_elt = package_elt.find("%ssize" % self.commonns)
        self.size = makeIntOrNone(size_elt.get("package"))
        self.installed_size = makeIntOrNone(size_elt.get("installed"))
        self.archive_size = makeIntOrNone(size_elt.get("archive"))

        #package.archive_size = archive_size

        self.license = package_elt.findtext("%slicense" % self.commonns)
        vendor = u"%s" % package_elt.findtext("%svendor" % self.commonns)
        self.category = u"%s" % package_elt.findtext("%sgroup" % self.commonns)
        top_category = self.category
        idx = self.category.find("/")
        if idx > 0:
            top_category = self.category[0:idx]

        self.top_category = top_category

        self.source = package_elt.findtext("%ssource-package" % self.commonns)
        if self.fullname is not None and self.fullname.find(".src.rpm") > 0:
            self.is_source = True

        provides_elt = package_elt.find("%sprovides" % self.commonns)
        self.read_xml_constraints(provides_elt, "provide")

        requires_elt = package_elt.find("%srequires" % self.commonns)
        self.read_xml_constraints(requires_elt, "require")

        conflicts_elt = package_elt.find("%sconflicts" % self.commonns)
        self.read_xml_constraints(conflicts_elt, "conflict")

        obsoletes_elt = package_elt.find("%sobsoletes" % self.commonns)
        self.read_xml_constraints(obsoletes_elt, "obsolete")

        suggests_elt = package_elt.find("%ssuggests" % self.commonns)
        self.read_xml_constraints(suggests_elt, "suggest")


    def read_xml_constraints(self, constraint_elt, constraint_type):
        if constraint_elt is not None:
            entries = constraint_elt.findall("%sentry" % self.commonns)
            for entry in entries:
                obj = entry.get("name")
                version = entry.get("version")
                release = entry.get("release")
                flags = entry.get("flags")
                epoch = makeIntOrNone(entry.get("epoch"))
                pre = makeIntOrNone(entry.get("pre"))
                if constraint_type == "require":
                    require = Require(package=self, object=obj, flags=flags, epoch=epoch, version=version, releas=release, pre=pre)
                    require.type = constraint_type
                    self.requires.append(require)
                elif constraint_type == "provide":
                    provide = Provide(package=self, object=obj, flags=flags, epoch=epoch, version=version, releas=release, pre=pre)
                    provide.type = constraint_type
                    self.provides.append(provide)
                elif constraint_type == "conflict":
                    conflict = Conflict(package=self, object=obj, flags=flags, epoch=epoch, version=version, releas=release, pre=pre)
                    conflict.type = constraint_type
                    self.conflicts.append(conflict)
                elif constraint_type == "obsolete":
                    obsolete = Obsolete(package=self, object=obj, flags=flags, epoch=epoch, version=version, releas=release, pre=pre)
                    obsolete.type = constraint_type
                    self.obsoletes.append(obsolete)
                elif constraint_type == "suggest":
                    suggest = Suggest(package=self, object=obj, flags=flags, epoch=epoch, version=version, releas=release, pre=pre)
                    suggest.type = constraint_type
                    self.suggests.append(suggest)


    def read_xml_files(self, file_list_pkg_elt):
        #filens = "{http://linux.duke.edu/metadata/filelists}"
        self.files = []
        entries = file_list_pkg_elt.findall("%sfile" % self.commonns)

        for entry in entries:
            type = entry.get("type")
            if type is None:
                type = "file"
            path = u"%s" % entry.text
            if path is not None:
                filename = os.path.basename(path)
                size = makeIntOrNone(entry.get("size"))
                cat = makeStrWhatever(entry.get("cat"))
                extra = makeIntOrNone(entry.get("extra"))
                if extra is None:
                    extra = 0
                file = File(package=self, path=path, name=filename, type=type, cat=cat, size=size, extra=extra)
                self.files.append(file)


    def read_xml_changelog(self, pkg_elt):
        changelog = u'%s' % pkg_elt.findtext("%schangelog" % self.commonns).strip()
        self.changelog = Changelog(package=self, log=changelog)

    def read_xml_scripts(self, pkg_elt):
        #otherns = "{http://linux.duke.edu/metadata/other}"
        prein = u'%s' % pkg_elt.findtext("%sscripts/%sprein" % (self.commonns, self.commonns))
        postin = u'%s' % pkg_elt.findtext("%sscripts/%spostin" % (self.commonns, self.commonns))
        preun = u'%s' % pkg_elt.findtext("%sscripts/%spreun" % (self.commonns, self.commonns))
        postun = u'%s' % pkg_elt.findtext("%sscripts/%spostun" % (self.commonns, self.commonns))
        self.inun_script = InUnScript(package=self, prein=prein, postin=postin, preun=preun, postun=postun)


    def to_xml(self):
        info = self.get_template('package-template.xml')
        info.name = escape(self.name)
        info.checksum = self.checksum
        info.arch = self.arch
        info.version = self.version
        info.release = self.releas
        info.epoch = self.epoch
        info.rpmversion = self.rpmversion

        info.fullname = self.fullname
        info.summary = escape(self.summary)
        info.description = escape(self.description)
        info.url = self.url
        info.license = escape(self.license)
        info.srpm = self.source
        info.size = self.size
        info.archivesize = self.archive_size
        info.group = self.category

        info.copyright = self.license

        if self.author is not None:
            info.packager = escape(self.author)
        else:
            info.packager = ""

        if self.author_email is not None:
            info.packager_email = escape(self.author_email)
        else:
            info.packager_email = ""

        info.buildtime = self.build_time
        info.buildhost = self.build_host

        info.prein = escape_list(self.inun_script.prein)
        info.postin = escape_list(self.inun_script.postin)
        info.preun = escape_list(self.inun_script.preun)
        info.postun = escape_list(self.inun_script.postun)

        info.changelog = escape(self.changelog.log)

        info.requires = self.format_constraints_for_export(self.requires)

        info.provides = self.format_constraints_for_export(self.provides)
        info.obsoletes = self.format_constraints_for_export(self.obsoletes)
        info.conflicts = self.format_constraints_for_export(self.conflicts)
        info.suggests = self.format_constraints_for_export(self.suggests)

        info.files = []
        info.extra_files = {}
        info.tfiles = []
        for file in self.files:
            if file.extra == "1":
                if len(info.extra_files) == 0:
                    info.extra_files[0] = []
                info.extra_files[0].append({'path': escape(file.path), 'data': File(0, file.path, file.path, file.type, file.cat, file.size, file.extra)})
            else:
                info.files.append({'path': escape(file.path), 'data': File(0, file.path, file.path, file.type, file.cat, file.size, file.extra)})

        return '' + str(info)


    def get_template(self, file_name):
        #TODO: port this to use Django Templating system instead of Cheetah, and move template to the Django template dir(s)
        #path = os.path.abspath(os.path.dirname(sys.argv[0])) + '/' + file_name
        path = os.path.join(os.path.dirname(__file__), 'utils', file_name)
        tmpl = Template(file=path, filter='EncodeUnicode')
        return tmpl

    def format_constraints_for_export(self, constraints):
        list = []
        for constraint in constraints:
            list.append([constraint.object, constraint.flags, constraint.epoch, constraint.version, constraint.releas])
        return list

    @transaction.commit_on_success
    def store_package_data(self, repo=None, output=sys.stdout):
        #store package licenses
        self.save()
        if repo and repo not in self.repos.all():
            self.repos.add(repo)
        license = LicenseDefinition.get_package_license(self.license)
        package_license = PackageLicense(package=self, license=license)
        output.write('storing %s\n' % str(package_license))
        package_license.save()

        if True:
            for attrs in [self.provides, self.requires, self.conflicts, self.suggests, self.obsoletes, self.files]:
                for elt in attrs:
                    output.write('storing %s\n' % str(elt))
                    elt.package = self
                    elt.save()

            for elt in [self.inun_script, self.changelog]:
                output.write('storing %s\n' % str(elt))
                elt.package = self
                elt.save()


    def delete_package_data(self):
        for type in [Changelog, InUnScript, Provide, Require, Conflict, Obsolete, Suggest, File]:
            #entries = session.query(type).filter_by(id_package=package.id_package).all()
            entries = type.objects.filter(package=self).all()
            for entry in entries:
                entry.delete()
        self.repos.clear()
        self.delete()

    def get_histories(self):
        return RepositoryHistory.objects.filter(package=self)

    def get_snapshots(self, as_QuerySet=False):
        if as_QuerySet:
            return Snapshot.objects.filter(pk__in=[history_values['snapshot'] for history_values in self.get_histories().values('snapshot')])
        else:
            return [hist.snapshot for hist in self.get_histories()]

    class Meta:
        app_label = app_name
        db_table = u'%spackages' % db_prefix


class RepositoryHistory(models.Model):
    #id_snapshot = models.IntegerField() #generated by inspectdb
    snapshot = models.ForeignKey(Snapshot)
    #id_package = models.IntegerField() #generated by inspectdb
    package = models.ForeignKey(Package)

    def __unicode__(self):
        if self.id:
            return u"%s %s" % (self.snapshot, self.package)
        else:
            return u'%s.%s object' % (__name__, self.__class__.__name__)

    class Meta:
        app_label = app_name
        db_table = u'%shistory' % db_prefix
        verbose_name_plural = "Repository History"
    

class Changelog(models.Model):
    #id_changelog = models.AutoField(primary_key=True)
    #id_package = models.IntegerField(null=True, blank=True) #generated by inspectdb
    #package = models.ForeignKey(Package, null=True, blank=True)
    package = models.ForeignKey(Package, null=True, blank=True, on_delete=models.SET_NULL) # Django > 1.3
    author = models.CharField(max_length=765, blank=True)
    date = models.IntegerField(null=True, blank=True)
    log = models.TextField(blank=True)

    def __unicode__(self):
        if self.id:
            #return "<Changelog('%s','%s', '%s')>" % (self.author, self.date)
            return u"%s" % self.log
        else:
            return u'%s.%s object' % (__name__, self.__class__.__name__)

    class Meta:
        app_label = app_name
        db_table = u'%schangelogs' % db_prefix


class Conflict(models.Model):
    #id_constraint = models.AutoField(primary_key=True)
    #id_package = models.IntegerField() #generated by inspectdb
    package = models.ForeignKey(Package)
    object = models.CharField(max_length=765, blank=True)
    flags = models.CharField(max_length=765, blank=True)
    epoch = models.IntegerField(null=True, blank=True)
    version = models.CharField(max_length=765, blank=True)
    releas = models.CharField(max_length=765, blank=True)
    pre = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        if self.id:
            return u"<Conflict (%s, %s)>" % (self.package, self.object)
        else:
            return u'%s.%s object' % (__name__, self.__class__.__name__)

    class Meta:
        app_label = app_name
        db_table = u'%sconflicts' % db_prefix


class Contributor(models.Model):
    #id_contributor = models.AutoField(primary_key=True)
    id_mymandriva = models.CharField(max_length=765, blank=True)
    name = models.CharField(max_length=765, blank=True)
    pseudo = models.CharField(max_length=765, blank=True)
    email = models.CharField(max_length=765, blank=True)

    def __unicode__(self):
        return u"%s,%s,%s,%s,%s" % (self.id_contributor, self.id_mymandriva, self.email, self.pseudo, self.name)

    class Meta:
        app_label = app_name
        db_table = u'%scontributor' % db_prefix


class File(models.Model):
    #id_file = models.AutoField(primary_key=True)
    #id_package = models.IntegerField() #generated by inspectdb
    package = models.ForeignKey(Package)
    path = models.CharField(db_index=True, max_length=12000)
    name = models.CharField(db_index=True, max_length=765)
    type = models.CharField(max_length=765, blank=True)
    cat = models.CharField(max_length=765, blank=True)
    size = models.IntegerField(null=True, blank=True)
    extra = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=765, blank=True)

    def __unicode__(self):
        return u"<File(%s, %s, %s)>" % (self.path, self.type, self.size)

    class Meta:
        app_label = app_name
        db_table = u'%sfiles' % db_prefix
    

class InstallabilityViolationEntry(DateModel):
    #id_check = models.AutoField(primary_key=True)
    distribution = models.CharField(db_index=True, max_length=765)
    architecture = models.CharField(db_index=True, max_length=765)
    date = models.DateTimeField(db_index=True, null=True, blank=True)
    name = models.CharField(db_index=True, max_length=765)
    version = models.CharField(max_length=765, blank=True)
    object_name = models.CharField(max_length=765, blank=True)
    object_cstr = models.CharField(max_length=765, blank=True)
    dependency_name = models.CharField(max_length=765, blank=True)
    dependency_cstr = models.CharField(max_length=765, blank=True)
    dependency_avl = models.CharField(max_length=765, blank=True)
    conflict = models.CharField(max_length=765, blank=True)
    conflict_file = models.CharField(max_length=765, blank=True)
    cstr = models.TextField(blank=True)

    class Meta:
        app_label = app_name
        db_table = u'%sinstallability' % db_prefix
        verbose_name_plural = "Installability Violation Entries"

class Obsolete(models.Model):
    #id_constraint = models.AutoField(primary_key=True)
    #id_package = models.IntegerField() #generated by inspectdb
    package = models.ForeignKey(Package)
    object = models.CharField(max_length=765, blank=True)
    flags = models.CharField(max_length=765, blank=True)
    epoch = models.IntegerField(null=True, blank=True)
    version = models.CharField(max_length=765, blank=True)
    releas = models.CharField(max_length=765, blank=True)
    pre = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        if self.id:
            return u"<Obsolete (%s, %s)>" % (self.package, self.object)
        else:
            return u'%s.%s object' % (__name__, self.__class__.__name__)

    class Meta:
        app_label = app_name
        db_table = u'%sobsoletes' % db_prefix


class PackageLicense(models.Model):
    #id_package = models.IntegerField(primary_key=True)#generated by inspectdb
    package = models.ForeignKey(Package)
    #license = models.CharField(max_length=765, primary_key=True) #generated by inspectdb
    license = models.CharField(max_length=765)

    def __unicode__(self):
        if self.id:
            return u"<PackageLicense(%s, %s)>" % (self.package, self.license)
        else:
            return u'%s.%s object' % (__name__, self.__class__.__name__)

    class Meta:
        app_label = app_name
        db_table = u'%spackage_licenses' % db_prefix


class Provide(models.Model):
    #id_constraint = models.AutoField(primary_key=True) #generated by inspectdb
    #id_package = models.IntegerField() #generated by inspectdb
    package = models.ForeignKey(Package)
    object = models.CharField(db_index=True, max_length=765, blank=True)
    flags = models.CharField(max_length=765, blank=True)
    epoch = models.IntegerField(null=True, blank=True)
    version = models.CharField(max_length=765, blank=True)
    releas = models.CharField(max_length=765, blank=True)
    pre = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        if self.id:
            return u"<Provides (%s, %s)>" % (self.package, self.object)
        else:
            return u'%s.%s object' % (__name__, self.__class__.__name__)

    class Meta:
        app_label = app_name
        db_table = u'%sprovides' % db_prefix


class Queue(DateModel):
    #id_snapshot = models.IntegerField() #generated by inspectdb
    snapshot = models.ForeignKey(Snapshot)
    name = models.CharField(db_index=True, max_length=765)
    hash = models.CharField(max_length=765, blank=True)
    hash_type = models.CharField(max_length=765, blank=True)
    action = models.CharField(max_length=765, blank=True)
    state = models.CharField(max_length=765, blank=True)
    error_message = models.CharField(max_length=765, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def package_dir(self):
        i = self.string_to_integer()
        outputdir = os.path.join(extractiondir, str(i), self.name)
        return outputdir

    def string_to_integer(self):
        #SQL: floor(length(package) / ASCII(package) * 1000)
        length = len(self.name)
        code = ord(self.name[0])
        value = length * 1000 / code
        return value

    def package_xml_file(self):
        return os.path.join(self.package_dir(), self.name + ".doc4.xml")


    def check_and_store_package(self, replace=settings.REPLACE_PACKAGES, output=sys.stdout):
        #package_file, snapshot = self.name, self.snapshot
        metadata_file = self.package_xml_file()
        package = Package()
        package.read_xml(codecs.open(metadata_file, "r", "utf-8").read())
        result = 0

        try:
            packages_stored = Package.objects.filter(checksum=package.checksum)
            repo = self.snapshot.repository

            if packages_stored.count() == 0:
                package.store_package_data(repo=repo, output=output)

            else:
                output.write("  Package %s was stored previously.\n" % (package.fullname))
                if replace:
                    output.write("  Deleting data related to %s...\n" % (package.fullname))
                    for package_stored in packages_stored:
                        package_stored.delete_package_data()
                    output.write("  Storing new data for %s...\n" % (package.fullname))
                    package.store_package_data(repo=repo, output=output)
                else:
                    output.write("  Adding %s repository to %s...\n" % (package.fullname))
                    for package_stored in packages_stored:
                        if repo not in package_stored.repos.all():
                            package_stored.repos.add(repo)

        except Exception, e:
            output.write("check_and_store_package Error 1: %s\n" % str(e))
            try:
                #self.set_package_state(package_file, id_snapshot, "extraction-store", "end_time", "failed", str(e))
                self.state="failed"
                self.error_message = str(e)
                self.end_time = self.now()
                self.save()
                result = -1
            except Exception, e:
                output.write("check_and_store_package Error 2: %s\n" % str(e))
                #self.set_package_state(package_file, id_snapshot, "extraction-store", "end_time", "failed", "")
                self.state="failed"
                self.end_time = self.now()
                self.save()
                result = -1

        if result is 0:
            self.state="finished"
            self.end_time = self.now()
            self.save()

        return result

    def extract_package(self, repo, processed_packages, output=sys.stdout):
        global maxsize
        global state
        #package_file, id_snapshot, repository = self.name, self.snapshot, repo
        output.write("Processing: %s\n" % self.name)
        mirror_dir = os.path.join(repo.repositorydir, repo.get_path())
        #useful for debugging purpose: only package smaller than maxsize will be processed
        flag = False
        if maxsize > 0:
            try:
                if (os.path.exists(os.path.join(mirror_dir, self.name))):
                    size = os.path.getsize(os.path.join(mirror_dir, self.name))
                    big = size > maxsize
                    flag = processed_packages.__contains__(self.name) or big
            except Exception, e:
                output.write("Error: %s\n" % str(e))
                flag = False
                traceback.print_exc(file=output)
        else:
            flag = processed_packages.__contains__(self.name)
        if not flag:
            outputDir = self.package_dir()
            if os.path.exists(outputDir):
                if (extractionskip):
                    try:

                        if os.path.exists(os.path.join(outputDir, self.name + ".xml")):
                            output.write("Doc4 metadata file found, skipping...\n")
                            #self.set_package_state(self.name, id_snapshot, "extraction", "end_time", "skipped", "")
                            self.state = "skipped"
                            self.end_time = self.now()
                            self.save()
                        else:
                            output.write("No metadata file found, -> removing dir\n")
                            result = shutil.rmtree(outputDir)

                    except Exception, e:
                        output.write("Error: %s\n" % str(e))
                        #self.set_package_state(self.name, id_snapshot, "extraction", "end_time", "failed", str(e))
                        self.state = "failed"
                        self.error_message = str(e)
                        self.end_time = self.now()
                        self.save()
                        traceback.print_exc(file=output)

                else:
                    result = shutil.rmtree(outputDir)
                    output.write("Removing dir %s... Result: %s\n" % (outputDir, result))
                    #self.logger.info("deletion of %s: %s" % (outputDir, result))

            if not os.path.exists(outputDir):
                    try:
                        pacx = RpmExtractor()
                        #self.set_package_state(self.name, id_snapshot, "extraction", "start_time", "started", "")
                        self.state = "started"
                        self.start_time = self.now()
                        self.save()
                        output.write("Extracting: %s into %s...\n" % (self.name, outputDir))
                        do_extract = settings.DO_EXTRACT
                        do_decompress_src = settings.DO_DECOMPRESS_SRC
                        do_analyse = settings.DO_ANALYSE

                        """
                        if repo.provider == "mandriva":
                            do_extract = False
                            do_decompress_src = False
                            do_analyse = False
                        else:
                            do_extract = True
                            do_analyse = True
                        """

                        metadata = pacx.to_xml(os.path.join(mirror_dir, self.name), outputDir, do_extract, do_decompress_src, do_analyse)
                        metadata = unicode(metadata, "utf-8", "ignore")
                        metadataFile = self.package_xml_file()
                        write_string(metadata, metadataFile, "utf-8", False)
                        #self.set_package_state(self.name, id_snapshot, "extraction", "end_time", "finished", "")
                        self.state = "finished"
                        self.end_time = self.now()
                        self.save()
                        if not keep_rpm_files:
                            os.remove(os.path.join(mirror_dir, self.name))

                    except Exception, e:
                        output.write("Error: %s\n" % str(e))
                        #self.set_package_state(self.name, id_snapshot, "extraction", "end_time", "failed", str(e))
                        self.state = "failed"
                        self.error_message = str(e)
                        self.end_time = self.now()
                        self.save()
                        traceback.print_exc(file=output)

            processed_packages.append(self.name)
        else:
            if maxsize > 0:
                output.write("%s is larger than the maxsize parameter, or it has been processed in the same run already.\n" % (self.name))
            else:
                output.write("%s has been processed in the same run already.\n" % (self.name))

    class Meta:
        app_label = app_name
        db_table = u'%squeue' % db_prefix


class Require(models.Model):
    #id_constraint = models.AutoField(primary_key=True)
    #id_package = models.IntegerField() #generated by inspectdb
    package = models.ForeignKey(Package)
    object = models.CharField(db_index=True, max_length=765, blank=True)
    flags = models.CharField(max_length=765, blank=True)
    epoch = models.IntegerField(null=True, blank=True)
    version = models.CharField(max_length=765, blank=True)
    releas = models.CharField(max_length=765, blank=True)
    pre = models.IntegerField(null=True, blank=True)

    type = ''

    def __unicode__(self):
        if self.id:
            return u"<Require (%s, %s)>" % (self.package, self.object)
        else:
            return u'%s.%s object' % (__name__, self.__class__.__name__)

    class Meta:
        app_label = app_name
        db_table = u'%srequires' % db_prefix


class InUnScript(models.Model):
    #id_package = models.IntegerField(primary_key=True) #generated by inspectdb
    package = models.ForeignKey(Package)
    prein = models.TextField(blank=True)
    postin = models.TextField(blank=True)
    preun = models.TextField(blank=True)
    postun = models.TextField(blank=True)
    class Meta:
        app_label = app_name
        db_table = u'%sscripts' % db_prefix
        verbose_name_plural = "Install/Uninstall Scripts"

class SlocStat(models.Model):
    #id_sloc = models.AutoField(primary_key=True)
    #id_package = models.IntegerField() #generated by inspectdb
    package = models.ForeignKey(Package)
    #package = models.CharField(max_length=765)
    language = models.CharField(max_length=765)
    sloccount = models.IntegerField(null=True, blank=True)
    percent = models.FloatField()

    def __unicode__(self):
        if self.id:
            return u"<SlocStat (%s, %s, %s, %s)>" % (self.package, language, self.sloccount, self.percent)
        else:
            return u'%s.%s object' % (__name__, self.__class__.__name__)

    class Meta:
        app_label = app_name
        db_table = u'%ssloccount' % db_prefix


class Suggest(models.Model):
    #id_constraint = models.AutoField(primary_key=True)
    #id_package = models.IntegerField() #generated by inspectdb
    package = models.ForeignKey(Package)
    object = models.CharField(max_length=765, blank=True)
    flags = models.CharField(max_length=765, blank=True)
    epoch = models.IntegerField(null=True, blank=True)
    version = models.CharField(max_length=765, blank=True)
    releas = models.CharField(max_length=765, blank=True)
    pre = models.IntegerField(null=True, blank=True)
    class Meta:
        app_label = app_name
        db_table = u'%ssuggests' % db_prefix


def escape_list(list):
    if (list == None):
        return ""
    tmp = ''.join(list)
    #tmp = escape(tmp)
    #tmp = escape(tmp.encode("utf-8"))
    return escape(tmp)


class Category(object):
    __slots__ = ['name', 'nb_pkgs']
    def __init__(self, name):
        self.name = name
        self.nb_pkgs = 0
    def __unicode__(self):
        return self.name
    def __cmp__(self, other):
        if self.name > other.name:
            return 1
        if self.name == other.name:
            return 0
        if self.name < other.name:
            return -1
    @classmethod
    def get_categories(cls, package_queryset, category_query=None):
        #What categories are in the package_queryset:
        packages_categories = package_queryset.values('id', 'category').distinct()
        if category_query:
            #Curent Category is category_query, and sub_categories have to be listed:
            cat_nums = len(category_query.split('/'))
            sub_categories_set = set([category['category'].split('/')[cat_nums] for category in packages_categories if len(category['category'].split('/')) > cat_nums])
            category = category_query
            sub_categories = [ cls("%s/%s" % (category, sub_category)) for sub_category in sub_categories_set]
        else:
            #Curent Category is None, and sub_categories are the Categories' list:
            categories_set = set([category['category'].split('/')[0] for category in packages_categories if len(category['category'].split('/')) > 0])
            sub_categories = [cls(category) for category in categories_set]
            category = None
        for sub_cat in sub_categories:
            #sub_cat.nb_pkgs = Package.objects.filter(category = sub_cat.name).count()
            #sub_cat.nb_pkgs = package_queryset.filter(category__icontains = sub_cat.name).distinct().count()
            for cat in packages_categories:
                if sub_cat.name.lower() in cat['category'].lower():
                    sub_cat.nb_pkgs += 1
        sub_categories.sort()
        if not len(sub_categories):
            sub_categories = None
        if category and category_query:
            category = cls(category_query)
            #category.nb_pkgs = package_queryset.filter(category__icontains = category.name).distinct().count()
            for cat in packages_categories:
                if category.name.lower() in cat['category'].lower():
                    category.nb_pkgs += 1
        return (category, sub_categories)

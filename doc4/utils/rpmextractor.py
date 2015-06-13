#! /usr/bin/env python
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

import getopt
import locale
import os
import re
import rpm
import subprocess
import sys
import time
import logging
from optparse import OptionParser
from Cheetah.Template import Template
from xml.sax.saxutils import escape, quoteattr
from urllib import quote
from languages import *
from util import *
import chardet

#from threadpool import *

locale.setlocale(locale.LC_ALL, 'C')

log = logging.getLogger(__name__)
rpm2cpio = "/usr/bin/rpm2cpio"
cpio = "/bin/cpio"

##############################
# Classes
##############################
class File:
    def __init__(self, file, output_file, cat):

        self.file = file
        self.output_file = output_file
        self.path = os.path.split(self.file)[0]
        self.output_path = os.path.split(self.output_file)[0]
        self.name = os.path.split(self.file)[1]
        self.output_name = os.path.split(self.output_file)[1]
        self.ext = os.path.splitext(self.output_name)[1]
        self.cat = cat

        if os.path.isfile(self.output_file):
            self.size = os.path.getsize(os.path.join(self.output_path, self.name))
            self.rsize = os.path.getsize(self.output_file)
        else:
            self.size = 0
            self.rsize = 0

        # get type of file
        if os.path.isdir(self.output_file):
            # set permissions
            os.chmod(self.output_file, 0755)
            self.type = 'dir'
        elif os.path.islink(self.output_file):
            self.type = 'link'
        elif os.path.isfile(self.output_file):
            # set permissions
            os.chmod(self.output_file, 0644)
            self.ext_to_type()
        else:
            self.type = 'unknown'
            try:
                os.unlink(self.output_file)
            except OSError:
                pass
            log.debug("Not a regular file : " + self.file)


    def ext_to_type(self):
        """Converts a file extension to a string representing the file type, e.g. 'man', 'code', 'translation' etc."""

        # man file #
        if self.ext in ('.1', '.2', '.3', '.4', '.5', '.6', '.7', '.8', '.9') and 'man' in self.output_file:
            self.type = 'man'
        # info file #
        elif self.ext == '.info':
            self.type = 'info'
        # html file #
        elif self.ext == '.html' or self.ext == '.htm':
            self.type = 'html'
        # translation file #
        elif self.ext == '.mo' or self.ext == '.po':
            self.type = 'translation'
            self.cat = 'translation'
        # docbook #
        elif self.ext == '.docbook':
            self.type = 'docbook'
        # code #
        elif self.ext in ('.ada', '.awk', '.c', '.css', '.h', '.lua', '.cpp', '.c++', '.h++', '.cc', '.cxx', '.hxx', '.asm', '.groff', '.php', '.java', '.js', '.lisp', '.el', '.cl', '.erl', '.hrl', '.hs', '.m4', '.pas', '.patch', '.diff', '.pm', '.pod', '.pl', '.pov', '.py', '.rb', '.sh', '.tcsh', '.csh', '.sql', '.ml', '.mli', '.mll', '.mly', '.scm', '.bat', '.cmd', '.plot', '.plt', '.xsl', '.xml', '.tex', '.aux', '.toc', '.as', '.rss', '.xslt', '.xsd', '.wsdl', '.pyw', '.sc', '.pytb', '.tcl', '.yaml', '.la', '.ui', '.hh', '.spec', '.dtd', '.xhtml', '.svn-base', '.shtml', '.idl', '.xul', '.json', '.sgml') or self.name in ('Makefile', 'Makefile.in', 'Makefile.am'):
            self.type = 'code'
        # image #
        elif self.ext in ('.svg', '.png', '.jpg', '.jpeg', '.bmp', '.gif'):
            self.type = 'image'
        # audio #
        elif self.ext in ('.ogg', '.wav', '.mp3'):
            self.type = 'audio'
        elif self.ext in ('.txt', '.desktop', '.conf', '.cfg', '.properties'):
            self.type = 'text'
        elif self.ext in ('.bz2'):
            self.type = 'binary'
        # text file #
        elif os.path.isfile(self.output_file) and subprocess.Popen("/usr/bin/file -i '" + self.output_file + "' | grep ':\ application'", shell=True, stdout=subprocess.PIPE).communicate()[0] == '':
            self.type = 'text'
            #if self.ext is not None and len(self.ext) > 0:
            #    print "Text file found - Extension: %s File: %s " % (self.ext, self.name)
        else:
            self.type = 'binary'

    def __str__(self):
        print 'file : ' + self.file
        print 'output file : ' + self.output_file
        print 'file path : ' + self.path
        print 'output file path : ' + self.output_path
        print 'file name : ' + self.name
        print 'output file name : ' + self.output_name
        print 'category : ' + self.cat
        print 'file ext : ' + self.ext
        print 'type : ' + self.type
        print 'metadatas : '
        print self.metadatas

        return ''

class Package:
    def __init__(self, source_path, output_path):
        self.source_path = os.path.abspath(source_path)
        self.output_path = os.path.abspath(output_path)
        self.fullname = os.path.basename(self.source_path)
        self.files = []
        self.checksum = sha1sum(source_path)


    def analyse_files(self):
        for file in self.filenames:
            file_info = self.analyse_file(file)
            self.files.append({'path': file, 'data': file_info})

        for archive, files in self.extra_files.items():
            counter = 0
            for file in files:
                file_info = self.analyse_file(file)
                self.extra_files[archive][counter] = {'path': unicode(escape(unempty(file)), encoding="utf-8", errors="ignore"), 'data': file_info}
                counter += 1

    def analyse_file(self, file):
        file_decomp = file

        if file_decomp.startswith('/'):
            file_decomp = file_decomp[1:]

        output_file = os.path.join(unicode(self.output_path), file_decomp)

        # test if file is a conf or doc file
        if file in self.documentation_files:
            cat = "documentation"
        elif file in self.configuration_files:
            cat = "configuration"
        else:
            cat = ""
        # create File object
        file_info = File(file, output_file, cat)

        return file_info

    def format_constraints(self, objects, flags, versions):
        objects_flags = flags_to_string(flags)
        objects_epochs, objects_versions, objects_releases = split_versions(versions)

        if (len(objects)) == 0:
            return []
        else:
            for i in range(0, len(objects)):
                objects[i] = escape(unempty(objects[i]))

            return zip(objects, objects_flags, objects_epochs, objects_versions, objects_releases)

class Rpm(Package):
    def __init__(self, source_path, output_path):
        Package.__init__(self, source_path, output_path)
        self.rpm_size = os.path.getsize(source_path)
        self.read_metadata(source_path)

    def read_metadata(self, path):

        if path.endswith('src.rpm'):
            self.type = 'srpm'
        else:
            self.type = 'rpm'

        ts = rpm.ts()
        ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
        fdno = os.open(path, os.O_RDONLY)
        # read RPM header
        rpm_header = ts.hdrFromFdno(fdno)
        os.close(fdno)

        # get some tags
        self.name = rpm_header[rpm.RPMTAG_NAME]
        self.sourcerpm = rpm_header[rpm.RPMTAG_SOURCERPM]
        self.summary = rpm_header[rpm.RPMTAG_SUMMARY]
        self.url = rpm_header[rpm.RPMTAG_URL]
        self.version = rpm_header[rpm.RPMTAG_VERSION]
        self.release = rpm_header[rpm.RPMTAG_RELEASE]
        self.epoch = rpm_header[rpm.RPMTAG_EPOCH]

        self.rpmversion = rpm_header[rpm.RPMTAG_RPMVERSION]
        self.os = rpm_header[rpm.RPMTAG_OS]
        self.distribution = rpm_header[rpm.RPMTAG_DISTRIBUTION]
        self.license = rpm_header[rpm.RPMTAG_LICENSE]

        if path.find(".src.rpm") > 0:
            self.arch = "src"
        elif path.find(".noarch.rpm") > 0:
            self.arch = "noarch"
        elif path.find("i586.rpm") > 0:
            self.arch = "i586"
        else:
            self.arch = rpm_header[rpm.RPMTAG_ARCH]


        self.size = rpm_header[rpm.RPMTAG_SIZE]
        self.archive_size = rpm_header[rpm.RPMTAG_ARCHIVESIZE]
        self.group = rpm_header[rpm.RPMTAG_GROUP]
        #The tag COPYRIGHT is not available in python-rpm 4.6
        #-> we consider COPYRIGHT=LICENSE for now
        #self.taglist['COPYRIGHT'] = rpm_header[rpm.RPMTAG_COPYRIGHT]
        self.copyright = rpm_header[rpm.RPMTAG_LICENSE]
        self.packager = rpm_header[rpm.RPMTAG_PACKAGER]
        self.author = str(rpm_header[rpm.RPMTAG_PACKAGER])
        self.author_email = ""

        if not_empty(self.author):
            idx = self.author.find("@")
            idxlt = self.author.find("<")
            idxgt = self.author.find(">")
            if idx > 0 and idxlt > 0 and idxgt > 0 and idxlt < idxgt:
                self.author_email = unempty(self.author[idxlt + 1:idxgt])
                self.author = unempty(self.author[0:idxlt].strip())
            else:
                self.author = self.author.strip()

        self.build_time = rpm_header[rpm.RPMTAG_BUILDTIME]
        self.build_host = rpm_header[rpm.RPMTAG_BUILDHOST]

        self.requires = rpm_header[rpm.RPMTAG_REQUIRES]
        self.requireflags = rpm_header[rpm.RPMTAG_REQUIREFLAGS]
        self.requireversion = rpm_header[rpm.RPMTAG_REQUIREVERSION]

        self.provides = rpm_header[rpm.RPMTAG_PROVIDES]
        self.provideflags = rpm_header[rpm.RPMTAG_PROVIDEFLAGS]
        self.provideversion = rpm_header[rpm.RPMTAG_PROVIDEVERSION]

        self.conflicts = rpm_header[rpm.RPMTAG_CONFLICTS]
        self.conflictflags = rpm_header[rpm.RPMTAG_CONFLICTFLAGS]
        self.conflictversion = rpm_header[rpm.RPMTAG_CONFLICTVERSION]

        self.obsoletes = rpm_header[rpm.RPMTAG_OBSOLETENAME]
        self.obsoleteflags = rpm_header[rpm.RPMTAG_OBSOLETEFLAGS]
        self.obsoleteversion = rpm_header[rpm.RPMTAG_OBSOLETEVERSION]

        self.suggests = rpm_header[rpm.RPMTAG_SUGGESTSNAME]
        self.suggestsflags = rpm_header[rpm.RPMTAG_SUGGESTSFLAGS]
        self.suggestsversion = rpm_header[rpm.RPMTAG_SUGGESTSVERSION]

        self.description = rpm_header[rpm.RPMTAG_DESCRIPTION]
        self.prein = rpm_header[rpm.RPMTAG_PREIN]
        self.postin = rpm_header[rpm.RPMTAG_POSTIN]
        self.preun = rpm_header[rpm.RPMTAG_PREUN]
        self.postun = rpm_header[rpm.RPMTAG_POSTUN]

        self.filenames = []
        for file in rpm_header[rpm.RPMTAG_FILENAMES]:
            # random encodings on file. Try to guess them
            if isinstance(file, str):
                encoding = chardet.detect(file).get('encoding', 'utf8')
                if not encoding:
                    encoding = 'utf8'
                self.filenames.append(unicode(file, encoding))
            elif isinstance(file, unicode):
                self.filenames.append(file)

        if rpm_header[rpm.RPMTAG_CHANGELOGTEXT] and rpm_header[rpm.RPMTAG_CHANGELOGNAME]:
            self.changelog = ""
            for clidx in range(0, len(rpm_header[rpm.RPMTAG_CHANGELOGTEXT])):
                # I've seen yum headers where changelogs with a single entry have the timestamp (but not the other stuff)
                # stored as a string instead of a list. Tres annoying. =:\
                try:
                    # Generates 'TypeError' exception on string
                    len(rpm_header[rpm.RPMTAG_CHANGELOGTIME])
                    timestamp = time.ctime(rpm_header[rpm.RPMTAG_CHANGELOGTIME][clidx])
                except TypeError:
                    timestamp = time.ctime(rpm_header[rpm.RPMTAG_CHANGELOGTIME])

                self.changelog = self.changelog + "* %s - %s\n%s\n\n" % (timestamp, rpm_header[rpm.RPMTAG_CHANGELOGNAME][clidx], rpm_header[rpm.RPMTAG_CHANGELOGTEXT][clidx])
        else:
            self.changelog = ''

        # 17 = conf
        # 2 = doc
        flags = rpm_header['fileflags']
        # get the conf & doc files from files list
        self.documentation_files = []
        self.configuration_files = []
        for file, flag in zip(self.filenames, flags):
            if flag == 17:
                self.configuration_files.append(file)
            if flag == 2:
                self.documentation_files.append(file)

        self.extra_files = {}

    def extract_files(self, do_decompress_src):

        if not os.path.exists(self.source_path):
            raise ExtractError("Source path doesn't exists : %s" % self.source_path)
        if not os.path.exists(rpm2cpio):
            raise ExtractError("Can't find %s" % rpm2cpio)
        if not os.path.exists(cpio):
            raise ExtractError("Can't find %s" % cpio)

        cmd1 = [ rpm2cpio, self.source_path]
        cmd2 = [ cpio, "-id", "--quiet"]
        p1 = subprocess.Popen(cmd1, cwd=self.output_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2 = subprocess.Popen(cmd2, cwd=self.output_path, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p2.communicate()
        if p2.returncode == 0:
            # we decompress files in src.rpm
            if do_decompress_src and self.type == 'srpm':
                for file in self.filenames:
                    #For bunzip2 and unzip: the overwrite option is passed, otherwise the extraction process stalls
                    #in case the archive contains several files with the same path.
                    #This is not needed for tar: "if the archive contains multiple entries corresponding to the same
                    #file, the last one extracted will overwrite all earlier versions." (tar's man page)
                    if file.endswith('.tgz') or file.endswith('.tar.gz'):
                        cmd = ["tar", "xvfz", self.output_path + "/" + file, "-C", self.output_path]
                        self.extract_extra_files(cmd, file)
                    elif file.endswith('.tar.bz2'):
                        cmd = ["tar", "xvfj", self.output_path + "/" + file, "-C", self.output_path]
                        self.extract_extra_files(cmd, file)
                    elif file.endswith('.tar.lzma'):
                        cmd = ["tar", "xvf", self.output_path + "/" + file, "-C", self.output_path, "--lzma"]
                        self.extract_extra_files(cmd, file)
                    elif file.endswith('.bz2'):
                        cmd = ["bunzip2", "-f", self.output_path + "/" + file]
                        self.extract_extra_files(cmd, file)
                    elif file.endswith('.zip') or file.endswith('.ear') or file.endswith('war') or file.endswith('jar'):
                        cmd = ["unzip","-o", self.output_path + "/" + file]
                        self.extract_extra_files(cmd, file)
        else:
            raise ExtractError(u"Extraction failed of %s : %s" % (self.source_path, output[1].decode('utf-8')))

    def extract_extra_files(self, cmd, file):
        p = subprocess.Popen(cmd, cwd=self.output_path, stdout=subprocess.PIPE)
        data = p.communicate()[0]
        lines = data.split("\n")
        # decompress ok
        self.extra_files[file] = []
        #handling files such as xxxx.patch.bz2
        if not file.endswith('.tar.bz2') and file.endswith('.bz2'):
            self.extra_files[file].append(file[0:file.find('.bz2')])
        else:
            for elt in lines:
                filename = elt.strip()
                #special handling of zipped files, since the filenames is preceded by "Archive: " or "inflating: " or "creating: "
                if cmd[0] == "unzip":
                    if filename.find(":") > 0:
                        #don't add the archive name itself to the file list
                        if filename.find("Archive:") == 0:
                            continue
                        filename = filename[filename.find(":")+1:].strip()

                self.extra_files[file].append(filename)

class RpmExtractor:

    def extract_package(self, source_path, output_path, do_extract=True, do_decompress_src=True, do_analyse=True):

        if not os.path.exists(output_path):
            os.makedirs(output_path, 0755)

        ttmp = source_path.split('/')
        package_fullname = source_path
        if (len(ttmp) > 0):
            package_fullname = ttmp[len(ttmp) - 1]

        begin_time = time.time()

        # we instantiate the rpm object
        package = Rpm(source_path, output_path)

        if do_extract:
            log.debug("Extracting files...")
            package.extract_files(do_decompress_src)
            total_extraction_time = time.time() - begin_time
            log.debug("Total extraction time: " + str(total_extraction_time))

            # detect package files types
            if do_analyse:
                begin_analysis_time = time.time()
                log.debug("Analysing files...")
                package.analyse_files()
                total_analysis_time = time.time() - begin_analysis_time
                log.debug("Total analysis time: " + str(total_analysis_time))

        return package

    def get_template(self, file_name):
        #TODO: port this to use Django Templating system instead of Cheetah, and move template to the Django template dir(s)
        #path = os.path.abspath(os.path.dirname(sys.argv[0])) + '/' + file_name
        path = os.path.join(os.path.dirname(__file__), file_name)
        tmpl = Template(file=path, filter='EncodeUnicode')
        return tmpl


    def to_xml(self, source_path, output_path, do_extract=True, do_decompress_src=True, do_analyse=True):

        package = self.extract_package(source_path, output_path, do_extract, do_decompress_src, do_analyse)

        info = self.get_template('package-template.xml')
        info.name = escape_it(package.name)
        info.checksum = escape_it(package.checksum)
        info.arch = escape_it(package.arch)
        info.version = quote_it(package.version)
        info.release = quote_it(package.release)
        info.epoch = quote_it(package.epoch)

        info.fullname = escape_it(package.fullname)
        info.summary = escape_it(package.summary)
        info.description = escape_it(package.description)

        info.url = escape_it(package.url)
        info.license = escape_it(package.license)
        info.srpm = escape_it(package.sourcerpm)
        info.rpmversion = quote_it(package.rpmversion)
        info.size = quote_it(package.size)
        info.archivesize = quote_it(package.archive_size)
        info.packagesize = quote_it(package.rpm_size)
        info.group = escape_it(package.group)

        info.copyright = escape_it(package.copyright)
        info.packager = quote_it(package.author)
        info.packager_email = quote_it(package.author_email)

        info.buildtime = quote_it(package.build_time)
        info.buildhost = quote_it(package.build_host)
        info.prein = escape_list(unempty(package.prein))
        info.postin = escape_list(unempty(package.postin))
        info.preun = escape_list(unempty(package.preun))
        info.postun = escape_list(unempty(package.postun))

        info.changelog = escape(unempty(package.changelog).strip())

        info.requires = package.format_constraints(package.requires, package.requireflags, package.requireversion)
        info.provides = package.format_constraints(package.provides, package.provideflags, package.provideversion)
        info.obsoletes = package.format_constraints(package.obsoletes, package.obsoleteflags, package.obsoleteversion)
        info.conflicts = package.format_constraints(package.conflicts, package.conflictflags, package.conflictversion)
        info.suggests = package.format_constraints(package.suggests, package.suggestsflags, package.suggestsversion)

        info.files = []
        info.extra_files = []
        info.tfiles = []

        if package.files:
            info.tfiles = None
            info.type = package.type
            info.files = package.files
            info.extra_files = package.extra_files
            info.columns = {}

        else:
            for filename in package.filenames:
                info.tfiles.append(escape(filename))

        return str(info)

class Error(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg.encode('utf-8')


class ExtractError(Error):
    pass


def unempty(st):
    try:
        if not st:
            return u''
        elif isinstance(st, str):
            encoding = chardet.detect(st).get('encoding', 'utf8')
            if not encoding:
                encoding = 'utf8'
            return unicode(st.strip(), encoding=encoding)
        elif isinstance(st, int) or isinstance(st, long):
            return unicode(st)
        elif isinstance(st, list) and not len(st):
            return u''
        elif isinstance(st, list) and len(st):
            return unicode(st)
        elif isinstance(st, unicode):
            return st.strip()
        else:
            return st
    except Exception, e:
        print(__file__ + ' function "unempty": *** Error: ' + str(e) + '\n')
        print('received as parameter:')
        print(st)
        #return u''

def quote_it(value):
    #return quoteattr(quote(str(unempty(value)), ' \'\\"&<>'))
    if isinstance(value, str):
        encoding = chardet.detect(value).get('encoding', 'utf8')
        if not encoding:
            encoding = 'utf8'
        ustr = unicode(value.strip(), encoding=encoding)
        return quoteattr(ustr)
    elif isinstance(value, unicode):
        return quoteattr(value.strip())
    else:
        return quoteattr(unicode(unempty(value)))

def escape_it(value):
    if isinstance(value, str):
        encoding = chardet.detect(value).get('encoding', 'utf8')
        if not encoding:
            encoding = 'utf8'
        ustr = unicode(value.strip(), encoding=encoding)
        return escape(ustr)
    elif isinstance(value, unicode):
        return escape(value.strip())
    else:
        return escape(unicode(unempty(value)))

def escape_list(list):
    if (list == None):
        return ""
    tmp = ''.join(list)
    #tmp = escape(tmp)
    #tmp = escape(tmp.encode("utf-8"))
    return escape(tmp)

def quoteattr_list(list):
    if (list == None):
        return ""
    tmp = ''.join(list)
    #tmp = escape(tmp)
    #tmp = escape(tmp.encode("utf-8"))
    return quoteattr(tmp)

def flags_to_string(flags):
    flags_str = ["" for i in flags]
    counter = 0
    for flag in flags:
        flags_str[counter] = flag_to_string(flag)
        counter += 1
    return flags_str

def flag_to_string(flag):
    """see yum.miscutils.py"""

    flags = flag & 0xf

    if flags == 0: return None
    elif flags == 2: return 'LT'
    elif flags == 4: return 'GT'
    elif flags == 8: return 'EQ'
    elif flags == 10: return 'LE'
    elif flags == 12: return 'GE'

    return flags

def split_versions(versions):

    epochs, vers, rels = [], [], []
    for version in versions:
        relIndex = version.rfind('-')
        if relIndex == -1:
            rel = ''
            relIndex = len(version)
        else:
            rel = version[relIndex + 1:]

        verIndex = version[:relIndex].rfind(':')
        if verIndex == -1:
            ver = version[:relIndex]
        else:
            ver = version[verIndex + 1:relIndex]

        epochIndex = version.find(':')
        if epochIndex == -1:
            epoch = ''
        else:
            epoch = version[:epochIndex]

        epochs.append(epoch)
        vers.append(ver)
        rels.append(rel)

    return epochs, vers, rels


def main(args):

    parser = OptionParser()
    # query options
    parser.add_option("-e", "--extract", default=False, action="store_true", dest="extract", help="extract package files")
    parser.add_option("-d", "--decompress", default=False, action="store_true", dest="decompress", help="decompress source archives")
    parser.add_option("-a", "--analyse", default=False, action="store_true", dest="analyse", help="analyses package files")

    (opts, argsleft) = parser.parse_args(args)

    if len(argsleft) == 2:
        extractor = RpmExtractor()
        to_extract = argsleft[0]
        output = argsleft[1]

        if not os.path.exists(to_extract):
            print "No file found named %s." % to_extract
            sys.exit(1)

        package_filename = os.path.basename(to_extract)
        output_dir = os.path.join(output, package_filename)

        print "Package file: %s. Output: %s. " % (to_extract, output_dir)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        metadata = extractor.to_xml(to_extract, output_dir, opts.extract, opts.decompress, opts.analyse)

        out = unicode(metadata, "utf-8", "ignore")

        write_string(out, output_dir + "/metadata.xml", "utf-8", False)

    else:
        parser.print_usage()


if __name__ == "__main__":
    main(sys.argv[1:])

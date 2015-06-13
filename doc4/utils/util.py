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

import os, re, sys, gzip
import codecs 
import hashlib
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_for_filename, get_lexer_for_mimetype
from pygments.formatters import HtmlFormatter
import collections, fileinput

# file handling
def compress(file):
    #if config.get('global', 'gzip') == True:
    r_file = open(file, 'r')
    w_file = gzip.GzipFile(file + '.gz', 'w', 9)
    w_file.write(r_file.read())
    w_file.flush()
    w_file.close()
    r_file.close()
    os.unlink(file) #We don't need the file now

def read_as_string(file):
    # read the file
    f=open(file, "r")
    content = f.read()
    f.close()
    return content

def write_string(content, file, encoding="utf-8", gzip=True):
    if os.path.exists(file):
        # ensure that we can write the file
        os.chmod(file, 0644)
    # write the string
    f=codecs.open(file, "w", encoding)
    #f = open(file,'a+')    
    f.write(content)
    f.close()
    if gzip:
        compress(file)
        
def set_text(content, file):
    if os.path.exists(file):
        # ensure that we can write the file
        os.chmod(file, 0644)
    f = open(file,'w')    
    f.write(content)
    f.close()
    
def find(directory,file):
    """find directory -name file"""
    #if nothing can be find, returns an empty string
    for root,dirs,files in os.walk(directory):
        for curr_file in files:
            if curr_file == file:
                res = os.path.join(root,curr_file)
                if res == None:
                    return ''
                else:
                    return res
    return ''

# manipulate lists of File object
def count_files_by_type(files, type):
    nb = 0
    for file in files:
        if file['data'].type == type:
            nb += 1

    return nb
def compare_file_lists(needles, files):
    result = []
    for file in files:
        for needle in needles:
            if file['path'] == needle:
                result.append(file)

    return result
def get_files_by_type(files, type):
    result = []
    for file in files:
        if file['data'].type == type:
            result.append(file)

    return result

# syntax hilighting helper
def highlight_by_mime_type(content, mimetype):
    try:
        #if config.get('global', 'syntax') == "1":
        lexer = get_lexer_for_mimetype(mimetype, encoding='chardet')
        #else:
        #lexer = get_lexer_for_mimetype('text/plain')
        formatter = HtmlFormatter(linenos="inline", cssclass="source", outencoding="utf-8")
        content = highlight(content, lexer, formatter)
    except Exception, e:
        #log_package('hilight error in extract_code : ' + str(e), log_path)
        content = '<p>An error occurred while formatting content: '+str(e)+'</p>' + content
    return content

def highlight_by_filename(file, content):
    formatter = HtmlFormatter(linenos="inline", cssclass="source", outencoding="utf-8")
    try:
        lexer = get_lexer_for_filename(file, encoding='chardet')
        #lexer = get_lexer_for_filename(file)
        #else:
        #lexer = get_lexer_for_mimetype('text/plain', encoding='chardet')
        try:
            content = highlight(content, lexer, formatter)
        except Exception, e:
            #log_package('highlight error in extract_code : ' + str(e), log_path)
            content = '<p class="error">An error occurred while formatting content: '+str(e)+'</p>' + content
    except Exception, e:
            #log_package('no lexer for ' + file + ' falling back on text/plain', log_path)
            try:
                content = highlight_by_mime_type(content, 'text/plain')
            except Exception,e:
                #log_package('highlight error in extract_code : ' + str(e), log_path)
                content = '<p class="error">An error while formatting content: '+str(e)+'</p>' + content
    return content

# logging function
def log_package(string, log_path):
    log = open(log_path,'a+')
    log.write(string )
    log.close()

def log_and_print(string, log_file_path):
    #prints the string on the screen and in the doc4.log file
    print "%s" % string
    log = open(log_file_path,'a+')
    log.write(string + '\n')
    log.close()
    #sys.stdout.write(string + '\n')

# html cleaning function
def clean_html(html):
    # lowercase all XML nodes
    def match_lower(matchobj):
        return matchobj.group(0).lower()
    html = re.sub('<([^> ]*)', match_lower, html)
    # remove all empty lines
    html = re.sub("\n\s*\n*", "\n", html)
    # clean html file
    html = re.sub('<!doctype.*>','',html)
    html = html.replace('Content-type: text/html', '')
    html = html.replace('<html>', '')
    html = html.replace('<head>', '')
    html = re.sub('<title[^>]*>[^<].*</title>','',html)
    html = re.sub('<body[^>]*>','',html)
    html = html.replace('</head>', '')
    html = html.replace('</body>', '')
    html = html.replace('</html>', '')
    # we just delete the following tags since they are not useful for any page and can lead to unexpected layout
    html = re.sub('<a[^/]*/>','',html)
    html = html.replace('<div/>','')
    html = re.sub('<link[^>]*>','',html)
    # correct image position
    html= html.replace('<img','<img style="position:static;"')

    return html

def unique(seq, keepstr=True):
    t = type(seq)
    if t in (str, unicode):
        t = (list, ''.join)[bool(keepstr)]
    seen = []
    return t(c for c in seq if not (c in seen or seen.append(c)))

def make_column(st, column_size):
    l = len(st)
    n = (column_size - l)
    
    col = ''
    zeroToN = range(0, n)
    for i in zeroToN:
        col += ' '
    return ''+col

def not_empty(st):
     return st is not None and len(str(st).strip()) > 0
 
 
def string_to_integer(str):
     #SQL: floor(length(package) / ASCII(package) * 1000)
    length = len(str)
    code = ord(str[0])
    value = length * 1000 / code
    return value 


def append(content, file):
    if os.path.exists(file):
        # ensure that we can write the file
        os.chmod(file, 0644)
    # write the string
    #f=open(file, "w")
    f = codecs.open(file, 'a+', encoding='utf-8')    
    f.write(content)
    f.close()

def compute_MD5(string):
    m = hashlib.md5()
    m.update(string)
    digest = m.hexdigest()
    return digest


def head(filename, lines_to_delete=1):
    queue = collections.deque()
    lines_to_delete = max(0, lines_to_delete) 
    for line in fileinput.input(filename, inplace=True, backup=None):
        queue.append(line)
        if lines_to_delete == 0:
            print queue.popleft(),
        else:
            lines_to_delete -= 1
    queue.clear()
    

def sha1_sumfile(fobj):
    '''Returns an sha1 hash for an object with read() method.'''
    m = hashlib.sha1()
    while True:
        d = fobj.read(8096)
        if not d:
            break
        m.update(d)
    return m.hexdigest()


def sha1sum(fname):
    '''Returns an md5 hash for file fname, or stdin if fname is "-".'''
    if fname == '-':
        ret = sha1_sumfile(sys.stdin)
    else:
        try:
            f = file(fname, 'rb')
        except:
            return 'Failed to open file'
        ret = sha1_sumfile(f)
        f.close()
    return ret

def md5_sumfile(fobj):
    '''Returns an md5 hash for an object with read() method.'''
    m = hashlib.md5()
    while True:
        d = fobj.read(8096)
        if not d:
            break
        m.update(d)
    return m.hexdigest()


def md5sum(fname):
    '''Returns an md5 hash for file fname, or stdin if fname is "-".'''
    if fname == '-':
        ret = md5_sumfile(sys.stdin)
    else:
        try:
            f = file(fname, 'rb')
        except:
            return 'Failed to open file'
        ret = md5_sumfile(f)
        f.close()
    return ret

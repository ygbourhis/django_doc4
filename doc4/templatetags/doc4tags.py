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

from __future__ import division
from django.utils import formats
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse, resolve
from django.utils.encoding import force_unicode
from django.utils.html import LEADING_PUNCTUATION, TRAILING_PUNCTUATION, punctuation_re, word_split_re
import re
email_url_re = re.compile(r'(?P<mailto>^href="mailto:)(?P<email1>[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)(?P<middle>"\>)(?P<email2>[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)(?P<trail>\</a\>.*$)')

from django import template
register = template.Library()

from pygments import highlight
from pygments.lexers import BashLexer
from pygments.formatters import HtmlFormatter

def obfuscate(s):
    new_s = ''
    for char in s:
        new_s += '&#%s;' % ord(char)
    return new_s

@register.filter
def code_highlight(code, lang='bash'):
    lexers = {
        'bash' : BashLexer,
        }
    lexer = lexers.get(lang, BashLexer)
    formatter = HtmlFormatter(lineos=True)
    result = highlight(code, lexer(), formatter)
    return result
code_highlight.is_safe = True
code_highlight.needs_autoescape = False

@register.filter
def auto_obfuscate_emails(text):
    words = word_split_re.split(force_unicode(text))
    for i, word in enumerate(words):
        match = None
        if '.' in word or '@' in word:
            match = email_url_re.match(word)
        if match:
            mailto, email1, middle, email2, trail = match.groups()
            email1 = obfuscate(email1)
            email2 = obfuscate(email2)
            neword = u''.join([mailto, email1, middle, email2, trail])
            words[i] = neword
    return u''.join(words)
auto_obfuscate_emails.is_safe=True
auto_obfuscate_emails.needs_autoescape = False

@register.filter
def doc4filesizeformat(bytes, kibi=True):
    """
    Formats the value like a 'human-readable' file size (i.e. 13 KiB, 4.1 MiB,
    102 bytes, etc).
    
    This does almost the same as django.template.defaultfilters.filesizeformat
    It fixes the International System of Units which is wrong in
    django.template.defaultfilters.filesizeformat, indeed, KB, MB, GB and TB
    should be KiB, MiB, GiB and TiB.
    """
    try:
        bytes = float(bytes)
    except (TypeError,ValueError,UnicodeDecodeError):
        
        return "%d %s" % (0, _('byte(s)'))

    number_format = lambda value: formats.number_format(round(value, 1), 1)
    
    sizes = [_('byte(s)'), _('KB'), _('MB'), _('GB'), _('TB'), _('PB'), _('EB'), _('ZB'), _('YB')]
    kibisizes = [_('byte(s)'), _('KiB'), _('MiB'), _('GiB'), _('TiB'), _('PiB'), _('EiB'), _('ZiB'), _('YiB')]
    
    if kibi is True or str(kibi) == 'True':
        power = 1024
        szes = kibisizes
    elif kibi is False or str(kibi) == 'False':
        power = 1000
        szes = sizes
    
    szes_pointer = 0
    
    while (int(bytes/power) > 0) and (szes_pointer < len(szes)-1):
        bytes = bytes/power
        szes_pointer += 1
    return "%s %s" % (number_format(bytes), szes[szes_pointer])

doc4filesizeformat.is_safe = True

def filter_get_elts(request, keep_page=False):
    get_elts = request.GET.copy()
    for key, value in get_elts.items():
        if not len(value):
            get_elts.pop(key)
    if get_elts.has_key('page') and not keep_page:
        get_elts.pop('page')
    return get_elts

@register.inclusion_tag('doc4/tags/paging.html', takes_context=True)
def show_paging(context, pages):
    request = context.get('request')
    get_dict = filter_get_elts(request).urlencode()
    return {'pages' : pages,
            'getdict' : get_dict,
            }

@register.simple_tag(takes_context=True)
def add_getrequest_to(context, url, keep_page=False):
    get_dict = None
    request = context.get('request')
    if request:
        get_dict = filter_get_elts(request, keep_page).urlencode()
    if get_dict and len(get_dict):
        newurl = '%s?%s' % (url, get_dict)
    else:
        newurl = url
    return newurl

@register.simple_tag(takes_context=True)
def apiurl(context, url, format=None, keep_page=False):
    #if url == 'api_view_name':
        #url = reverse(context.get('api_view_name'))
    get_elts = {}
    get_dict = None
    request = context.get('request')
    if request:
        get_elts = filter_get_elts(request, keep_page)
        if url == 'api_view_name':
            url = '/api' + request.path_info
    if format:
        get_elts['format'] = format
    if len(get_elts):
        get_dict = get_elts.urlencode()
    if get_dict:
        newurl = '%s?%s' % (url, get_dict)
    else:
        newurl = url
    return newurl
    

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

from django import forms
#from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _
from models import Repository, Package

import re
from copy import deepcopy

#repo_query = Repository.objects
repo_query = Repository.objects.filter(package__isnull=False).distinct()

category_query = Package.objects
package_query = Package.objects

class FilterChoiceField(forms.ChoiceField):
    def validate(self, value):
        if value not in self.choices:
            return ''
        else:
            return value

repo_filters = {
    'provider' : _('Provider'),
    'distribution' : _('Distribution'),
    'architecture' : _('Architecture (Repository)'),
    'branch' : _('Branch'),
    'section' : _('Section'),
}

category_filters = {
    'category' : _('Category'),
    'top_category' : _('Top Category'),
}

#repo_fields = repo_filters.keys() #Problem is : dictionaries are unordered and so are the returned keys
repo_fields = ['provider','distribution','architecture','branch','section']
#category_fields = category_filters.keys() #Problem is : dictionaries are unordered and so are the returned keys
category_fields = ['category','top_category']
# Whe create a Form model from the list above:
form_dict = {}
for field in repo_fields:
    choices_set = set([value[field] for value in repo_query.values(field).distinct()])
    choices = list(choices_set)
    choices.sort()
    choices.insert(0,'')
    form_dict[field] = FilterChoiceField(choices=zip(choices,choices), required=False, label=repo_filters[field])

for field in category_fields:
    choices_set = set([value[field] for value in category_query.values(field).distinct()])
    choices = list(choices_set)
    choices.sort()
    choices.insert(0,'')
    form_dict[field] = FilterChoiceField(choices=zip(choices,choices), required=False, label=category_filters[field])

arch_choices_set = set([value['arch'] for value in package_query.values('arch').distinct()])
arch_choices = list(arch_choices_set)
arch_choices.sort()
arch_choices.insert(0,'')
form_dict['arch'] = FilterChoiceField(choices=zip(arch_choices,arch_choices), required=False, label='Package Architecture')
#Now we create the FilterForm class:
FilterForm = type('FilterForm', (forms.Form,), form_dict)

search_fields = (
    ('nothing', ''),
    ('file', _('Containing files named')),
    ('path', _('Containing Path named')),
    ('name', _('Named')),
    ('fullname', _('With full name')),
    ('category', _('In Category')),
    ('repository', _('In Repository')),
    ('summary', _('Containing in Summary')),
    ('description', _('Containing in Description')),
    ('author', _("Who's author is")),
    ('author_email', _("Who's author's email is")),
    ('changelog', _("With in Changelog")),
)

class SearchForm(forms.Form):
    search_elt = forms.ChoiceField(choices=search_fields, required=False, label=_('Search for Packages'))
    search_value = forms.CharField(max_length=12000, required=False, label=_(': '))
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        #this below has to be defined as instance property. When declared as class property it doesn't work:
        self.label_suffix = ' '

class InstallForm(forms.Form):
    package_name = forms.CharField(widget=forms.HiddenInput, max_length=765)
    package_id = forms.IntegerField(widget=forms.HiddenInput)

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

from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response, redirect
from django.views.generic.list_detail import object_list, object_detail
#from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse, Http404, HttpResponseRedirect
#from django.template import Context
#from django.template.loader import get_template
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse, resolve
from django.utils.http import urlquote

from django.conf import settings
import os
if hasattr(settings, 'DOC4_BASE_URL'):
    DOC4_BASE_URL = os.path.join(settings.DOC4_BASE_URL, '')
else:
    DOC4_BASE_URL = ''

from models import Package, File, Repository, Category, RepositoryHistory, REPOSITORY_PACKAGE_SEARCH_URL
from forms import FilterForm, SearchForm, InstallForm

from copy import deepcopy
from forms import repo_fields, category_fields, search_fields

form_fields = [elt[0] for elt in search_fields]
form_fields.extend(['log'])

menus = [ 'menu_package',
          'menu_detail',
          'menu_file',
          'menu_provide',
          'menu_require',
          'menu_obsolete',
          'menu_conflict',
          'menu_suggest',
          'menu_inunscript',
          'menu_changelog',
        ]
menu_dict = {}.fromkeys(menus, 'unsel')

search_types = {
    'icontains' : '__icontains',
    'fuzzy' : '__icontains',
    'contains' : '__contains',
    'exact' : '',
    'match' : '',
}

#############################################################
#FUNCTIONS used by Views (by view functions)
#but which do not render views directly mappable by urls.py :
#############################################################

def get_searchtype(request, extra=None):
    search_type = request.GET.get('searchtype', 'icontains')
    default_search_type = search_types.get(search_type, '__icontains')
    if extra and isinstance(extra, str):
        search_type = request.GET.get(extra, search_type)
        search_type = search_types.get(search_type, default_search_type)
    return search_type

def paginate(request, object_list, qty=25):
    limit = request.GET.get('limit', '25')
    if limit.isdigit():
        limit = int(limit)
    else:
        limit = qty
    if limit > 100:
        limit = 100
    elif limit < 1:
        limit = qty
    paginator = Paginator(object_list, limit)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    
    # If page request (9999) is out of range, deliver last page of results.
    try:
        objects = paginator.page(page)
    except (EmptyPage, InvalidPage):
        objects = paginator.page(paginator.num_pages)
    
    return (paginator, objects)


def get_package_list(request, query=None, Model=None, field=None, provider=None, distribution=None, architecture=None, branch=None, section=None):
    search_type = get_searchtype(request, 'urlsearchtype')
    #For what related model do we want to display Packages:
    if Model is None:
        package_list = Package.objects.all()
    elif Model is Package:
        #query_dict = {field + '__icontains' : query}
        query_dict = {field + search_type : query}
        package_list = Package.objects.filter(**query_dict).order_by('fullname').distinct()
    elif Model is Repository:
        query_dict = {}
        if provider:
            #query_dict['provider'] = provider
            query_dict['provider' + search_type] = provider
        if distribution:
            #query_dict['distribution'] = distribution
            query_dict['distribution' + search_type] = distribution
        if architecture:
            #query_dict['architecture'] = architecture
            query_dict['architecture' + search_type] = architecture
        if branch:
            #query_dict['branch'] = branch
            query_dict['branch' + search_type] = branch
        if section:
            #query_dict['section'] = section
            query_dict['section' + search_type] = section
        repos = Repository.objects.filter(**query_dict).distinct()
        #rep_hist = RepositoryHistory.objects.filter(snapshot__repository__in=repos)
        #package_list = Package.objects.filter(repositoryhistory__in=rep_hist).order_by('fullname').distinct()
        package_list = Package.objects.filter(repos__in=repos).order_by('fullname').distinct()
    else:
        #query_dict = {field + '__icontains' : query}
        query_dict = {field + search_type : query}
        
        search_elts = Model.objects.filter(**query_dict).values('package').distinct()
        package_ids = [value['package'] for value in search_elts]
        """
        search_elts = Model.objects.filter(**query_dict).values('package')
        package_ids = set([value['package'] for value in search_elts])
        """
        package_list = Package.objects.filter(pk__in = package_ids).order_by('fullname').distinct()
    
    return package_list


def filter_by_repos_and_arch(request, object_list, only_repos=False):
    search_type = get_searchtype(request, 'getsearchtype')
    filter_repos = False
    pkg_query_dict = {}
    repo_query_dict = {}
    #repo_fields = ['provider','distribution','architecture','branch','section'] #imported from forms
    fields = deepcopy(repo_fields)
    arch = request.GET.get('arch')
    if arch:
        if only_repos:
            #object_list is a list of repositories
            repo_query_dict['package__arch' + search_type] = arch
        else:
            #object_list is a list of packages
            pkg_query_dict['arch' + search_type] = arch
        filter_repos = True

    for field in fields:
        if request.GET.get(field):
            repo_query_dict[field + search_type] = request.GET.get(field)
            filter_repos = True
    
    if filter_repos:
        if only_repos:
            #object_list is a list of repositories
            return object_list.filter(**repo_query_dict).distinct()
        else:
            #object_list is a list of packages
            for key, value in repo_query_dict.items():
                pkg_query_dict['repos__' + key]=value
    
    if not only_repos:
        #object_list is a list of packages
        return object_list.filter(**pkg_query_dict).distinct().order_by('fullname')
    else:
        return object_list


def filter_by_categories(request, object_list, only_packages=True):
    search_type = get_searchtype(request, 'getsearchtype')
    filter_categories = False
    category_query_dict = {}
    category_fields = ['category', 'top_category']
    for field in category_fields:
        if request.GET.get(field):
            category_query_dict[field + search_type] = request.GET.get(field)
            filter_categories = True
    if filter_categories:
        if only_packages:
            #object_list is a list of packages
            return object_list.filter(**category_query_dict).order_by('fullname').distinct()
        else:
            #object_list is a list of repositories
            packages_category_query_dict = {}
            for key, value in category_query_dict.items():
                packages_category_query_dict['package__' + key] = value
            return object_list.filter(**packages_category_query_dict).distinct()
    else:
        return object_list


def get_filters(request):
    #fill the filter form:
    if request.method == 'GET':
        filterform = FilterForm(request.GET)
    else:
        filterform = FilterForm()
    
    request_elts = request.path_info.split('/')
    base_url = os.path.join(DOC4_BASE_URL, REPOSITORY_PACKAGE_SEARCH_URL)
    base_url = base_url.strip('/')
    index = len(base_url.split('/'))
    if len(set(['repository','file','path','package','category']).intersection(set(request_elts))):
        try:
            filtersuggest_initial = {}
            if request_elts[index] == 'repository':
                for initial_elt, initial_value in zip(repo_fields,request_elts[index+1:]):
                    filtersuggest_initial[initial_elt] = initial_value.strip('/')
                filtersuggest = FilterForm(initial=filtersuggest_initial)
            elif request_elts[index] == 'category':
                filtersuggest_initial['top_category'] = unicode(request_elts[index+1])
                cat_elt = request.path_info.split('/', index+1)
                filtersuggest_initial['category'] = cat_elt[index+1].rstrip('/')
                filtersuggest = FilterForm(initial=filtersuggest_initial)
            else:
                #filtersuggest = FilterForm()
                filtersuggest = None
        except:
            #filtersuggest = FilterForm()
            filtersuggest = None
    else:
        #filtersuggest = FilterForm()
        filtersuggest = None
        
    return (filterform, filtersuggest)

def install_package(request, package):
    installform = InstallForm(request.POST)
    if installform.is_valid():
        if str(installform.cleaned_data['package_name']) == str(package.name) and str(installform.cleaned_data['package_id']) == str(package.id):
            response = HttpResponse(content_type='application/x-urpmi')
            response['Content-Disposition'] = 'attachment; filename=%s.urpmi' % package.name
            response['Content-Type'] = 'application/x-urpmi; name=%s.urpmi' % package.name
            response.write('%s' % package.name )
            return response
        else:
            raise Http404
    else:
        raise Http404


###################################################################
#View FUNCTIONS (Which render the views and are mapped by urls.py):
###################################################################

def list_packages(request, query=None, Model=None, field=None, provider=None, distribution=None, architecture=None, branch=None, section=None):
    repo_values = [provider, distribution, architecture, branch, section]
    view_name = resolve(request.path_info).url_name
    api_view_name = view_name + '_api'
    searched = False
    filtered = False
    #Are we called by a search query? How do we fill the search form?:
    if request.method == 'POST':
        #We are called by a request after the form was filled
        searchform = SearchForm(request.POST)
        if searchform.is_valid():
            search_elt = searchform.cleaned_data['search_elt']
            #search_value = searchform.cleaned_data['search_value'].strip().strip('/')
            search_value = searchform.cleaned_data['search_value'].strip()
            #search_value = urlquote(searchform.cleaned_data['search_value'].strip())
            search_values = search_value.split('/')
            #for index, elt in enumerate(search_values):
            #    search_values[index] = urlquote(elt)
            if len(search_values) and search_elt !='nothing':
                search_values.append('')
                url_elts = ['/', DOC4_BASE_URL, 'packages', search_elt]
                url_elts.extend(search_values)
                #redirect_url = os.path.join(*url_elts)
                redirect_url = '/'.join(url_elts)
            else:
                #redirect_url = os.path.join( '/', DOC4_BASE_URL, 'packages')
                redirect_url = os.path.join( '/', DOC4_BASE_URL)
            get_elts = request.GET.copy()
            for key, value in get_elts.items():
                if not len(value):
                    get_elts.pop(key)
            if get_elts.has_key('page'):
                get_elts.pop('page')
            get_dict = get_elts.urlencode()
            if get_dict:
                redirect_url = '%s?%s' % (redirect_url, get_dict) 
            return HttpResponseRedirect(redirect_url)
    else:
        search_elt = ''
        search_value = ''
        #We are called by a GET request
        if field in form_fields:
            search_elt = field
            if search_elt == 'log':
                search_elt = 'changelog'
            elif search_elt == 'name' and Model is File:
                search_elt = 'file'
        else:
            search_elt = 'name'
        if query:
            search_value = query
        elif repo_values.count(None) < len(repo_values):
            for index, value in enumerate(repo_values):
                if value is None:
                    repo_values[index] = ''
            search_value = '/'.join(repo_values)
            search_elt = 'repository'
        searchform = SearchForm(initial={'search_elt' : search_elt, 'search_value' : search_value})
    
    #Now fill the filter forms:
    filterform, filtersuggest = get_filters(request)
    
    #Get package_list:
    package_list = get_package_list(request, query, Model, field, provider, distribution, architecture, branch, section)
    
    total_packages_unfiltered = package_list.count()
    package_list = filter_by_repos_and_arch(request, package_list)
    package_list = filter_by_categories(request, package_list)
    
    #What categories do the packages list belong to:
    if field is not None and field == 'category':
        category, sub_categories = Category.get_categories(package_list, query)
    else:
        category, sub_categories = Category.get_categories(package_list)
    
    #Paginate output:
    paginator, packages = paginate(request, package_list, 25)
    
    total_packages = paginator.object_list.count()
    displayed_packages = packages.object_list.count()
    if total_packages < total_packages_unfiltered:
        filtered = total_packages_unfiltered - total_packages
    
    extra_context = {
        'filterform' : filterform,
        'filtersuggest' : filtersuggest,
        'searchform' : searchform,
        'packages' : packages,
        'total_packages' : total_packages,
        'total_packages_unfiltered' : total_packages_unfiltered,
        'displayed_packages' : displayed_packages,
        'category' : category,
        'sub_categories' : sub_categories,
        'searched' : searched,
        'filtered' : filtered,
        'view_name' : view_name,
        'api_view_name' : api_view_name,
        }
    
    return object_list(request,
                       queryset = package_list,
                       extra_context = extra_context
                      )


def detail_package_object(request, Model, package_id=None, package_fullname=None):
    #search_type = get_searchtype(request)
    if package_id:
        package = get_object_or_404(Package, pk=package_id)
        viafullname = False
    elif package_fullname:
        try:
            package = get_object_or_404(Package, fullname__icontains=package_fullname)
        except MultipleObjectsReturned:
            try :
                package = Package.objects.get(fullname=package_fullname)
            except ObjectDoesNotExist:
                return HttpResponseRedirect(reverse('package_search', args=[package_fullname]))
        package_id = package.id
        viafullname = True
    else :
        return HttpResponseRedirect(reverse('package_list'))
    if request.method == 'GET':
        installform = InstallForm(initial={'package_name' : package.name, 'package_id' : package_id})
        if Model is Package:
            queryset = Model.objects.filter(pk=package_id)
            object_id = package_id
        else:
            queryset = Model.objects.filter(package=package_id)
            object_id = Model.objects.get(package=package).id
        
        extra_context = {
            'viafullname' : viafullname,
            'package' : package,
            'installform' : installform,
            }
        menu_elt = 'menu_' + Model.__name__.lower()
        extra_context.update(menu_dict)
        extra_context[menu_elt] = 'sel'
        return object_detail(request,
                             queryset = queryset,
                             object_id = object_id,
                             extra_context = extra_context
                            )
    elif request.method == 'POST':
        return install_package(request, package)


def list_package_object (request, Model, package_id=None, package_fullname=None):
    if package_id:
        package = get_object_or_404(Package, pk=package_id)
        viafullname = False
    elif package_fullname:
        try:
            package = get_object_or_404(Package, fullname__icontains=package_fullname)
        except MultipleObjectsReturned:
            try :
                package = Package.objects.get(fullname=package_fullname)
            except ObjectDoesNotExist:
                return HttpResponseRedirect(reverse('package_search', args=[package_fullname]))
        package_id = package.id
        viafullname = True
    else :
        return HttpResponseRedirect(reverse('package_list'))
    queryset = Model.objects.filter(package=package_id)
    if request.method == 'GET':
        installform = InstallForm(initial={'package_name' : package.name, 'package_id' : package_id})
        extra_context = {
            'viafullname' : viafullname,
            'package' : package,
            'set_count' : queryset.count(),
            'installform' : installform,
            }
        menu_elt = 'menu_' + Model.__name__.lower()
        extra_context.update(menu_dict)
        extra_context[menu_elt] = 'sel'
        return object_list(request,
                           queryset = queryset,
                           extra_context = extra_context
                          )
    elif request.method == 'POST':
        return install_package(request, package)


def list_repositories(request):
    #repository_list = Repository.objects.filter(package__isnull=False).distinct()
    populated_repos = Package.objects.values('repos').distinct()
    repo_list = [repo['repos'] for repo in populated_repos]
    repository_list = Repository.objects.filter(pk__in=repo_list)
    
    repository_list = filter_by_repos_and_arch(request, repository_list, only_repos=True)
    repository_list = filter_by_categories(request, repository_list, only_packages=False)
    paginator, repositories = paginate(request, repository_list, 25)
    
    #Now fill the filter forms:
    filterform, filtersuggest = get_filters(request)
    
    extra_context = {
        'filterform' : filterform,
        'filtersuggest': filtersuggest,
        'repositories' : repositories,
        'total_repositories' : paginator.object_list.count(),
        'displayed_repositories' : repositories.object_list.count(),
        }
    
    return object_list(request,
                       queryset = repository_list,
                       extra_context = extra_context
                      )

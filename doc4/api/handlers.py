#-*- coding:utf-8 -*-

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse, Http404, HttpResponseRedirect
from piston.handler import AnonymousBaseHandler, BaseHandler
from piston.utils import rc

from doc4.models import File, Provide, Require, Obsolete, Conflict, Suggest, InUnScript, Changelog, Package, Repository, RepositoryHistory, Category
from doc4.views import get_package_list, filter_by_categories, filter_by_repos_and_arch, paginate

class HttpResponseSeeOther(HttpResponseRedirect):
    status_code = 303

class HttpResponseMultipleChoices(HttpResponseRedirect):
    status_code = 300

#Instead of defining "class ModelNameHandler(AnonymousBaseHandler)" for all models,
#We define a hanler for all models in one shot:
for Model in [File, Provide, Require, Obsolete, Conflict, Suggest, InUnScript, Changelog, Package, Repository, RepositoryHistory]:
    handler_name = '%sHandler' % Model.__name__
    locals()[handler_name] = type(handler_name, (AnonymousBaseHandler,), {'model' : Model, 'exclude' : ('package_id', 'id', 'password', 'login', 'port', 'package')})
#Add specific extra exludes:
RepositoryHandler.exclude = RepositoryHandler.exclude + ('url',)

#Now specific handlers:
class PackageListHandler(AnonymousBaseHandler):
    allowed_methods = ('GET')
    #exclude = ('id',)
    fields = ('provider', 'distribution', 'architecture', 'branch', 'section',)
    model = Repository
    def read(self, request, query=None, Model=None, field=None, provider=None, distribution=None, architecture=None, branch=None, section=None):
        filtered = False
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
        paginator, paginated_list = paginate(request, package_list, 25)
        package_list = paginated_list.object_list
        total_packages = paginator.object_list.count()
        listed_packages = paginated_list.object_list.count()
        if total_packages < total_packages_unfiltered:
            filtered = total_packages_unfiltered - total_packages
        
        results = {}
        results['filtered_out'] = filtered
        results['unfiltered_total'] = total_packages_unfiltered
        results['total'] = total_packages
        results['listed'] = listed_packages
        results['page'] = paginated_list.number 
        results['pages'] = paginator.num_pages
        if isinstance(category, Category):
            results['category'] = {'name' : category.name, 'number_packages' : category.nb_pkgs}
        else:
            results['category'] = category
        if sub_categories:
            results['sub_categories'] = []
            for cat in sub_categories:
                results['sub_categories'].append({'name' : cat.name, 'number_packages' : cat.nb_pkgs})
        else:
            results['sub_categories'] = sub_categories
        
        packages = {}
        packages['packages'] = []
        packages['results'] = results
        for pkg in package_list:
            #package = {'id' : pkg.id, 'name' : pkg.name, 'fullname' : pkg.fullname, 'category' : pkg.category, 'repositories' : pkg.repos.all() }
            package = {'id' : pkg.id, 'name' : pkg.name, 'fullname' : pkg.fullname }
            packages['packages'].append(package)
        return packages

class DetailPackageHandler(AnonymousBaseHandler):
    allowed_methods = ('GET')
    #model = Package
    exclude = ('id', 'port', 'login', 'password', 'package', 'package_id')
    def read(self, request, package_id=None, package_fullname=None):
        #keys = ('repositories', 'files', 'changelogs', 'scripts', 'provides', 'obsoletes', 'conflicts', 'suggests')
        result = {}
        result['package'] = {}
        pkg_rslt = result['package']
        if package_id:
            try:
                package = Package.objects.get(pk=package_id)
            except ObjectDoesNotExist:
                resp = rc.NOT_FOUND
                resp.write("\nNo Package with id %s" % package_id)
                return resp
        elif package_fullname:
            try:
                package = Package.objects.get(fullname__icontains=package_fullname)
                #package = Package.objects.get(fullname=package_fullname)
            except MultipleObjectsReturned:
                try:
                    package = Package.objects.get(fullname=package_fullname)
                except ObjectDoesNotExist:
                    #return HttpResponseRedirect(reverse('package_search_api', args=[package_fullname]))
                    return HttpResponseSeeOther(reverse('package_search_api', args=[package_fullname]))
            except ObjectDoesNotExist:
                resp = rc.NOT_FOUND
                resp.write("\nNo Package with fullname %s" % package_fullname)
                return resp
        pkg_rslt['details'] = package
        #pkg_rslt['repositories'] = package.get_repos()
        pkg_rslt['repositories'] = package.repos.all()
        pkg_rslt['files'] = File.objects.filter(package=package)
        pkg_rslt['changelogs'] = Changelog.objects.filter(package=package)
        pkg_rslt['inunscripts'] = InUnScript.objects.filter(package=package)
        pkg_rslt['provides'] = Provide.objects.filter(package=package)
        pkg_rslt['requires'] = Require.objects.filter(package=package)
        pkg_rslt['obsoletes'] = Obsolete.objects.filter(package=package)
        pkg_rslt['conflicts'] = Conflict.objects.filter(package=package)
        pkg_rslt['suggests'] = Suggest.objects.filter(package=package)
        return result
        


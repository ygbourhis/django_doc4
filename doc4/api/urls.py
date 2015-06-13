#-*- coding:utf-8 -*-

from django.conf.urls.defaults import patterns, include, url
from piston.resource import Resource
from piston.authentication import NoAuthentication

from handlers import PackageListHandler, DetailPackageHandler
from emitters import *

from doc4.models import File, Package, Repository, Changelog

class TunedRessource(Resource):
    def determine_emitter(self, request, *args, **kwargs):
        """
        sublassing Resource in order to have default emitter falling back to xml instead of json
        """
        em = kwargs.pop('emitter_format', None)
        if not em:
            em = request.GET.get('format', 'xml')
        return em


auth = NoAuthentication()
ad = {
    'authentication' : auth,
}

list_packages = TunedRessource(handler=PackageListHandler, **ad)
detail_package = TunedRessource(handler=DetailPackageHandler, **ad)

urlpatterns = patterns('',
    url(r'^(packages/)?$', list_packages, name='package_list_api'),
    url(r'^(?P<package_id>\d+)/$', detail_package, name='package_detail_api'),
    url(r'^package/(?P<package_fullname>[+\w./-]+)/$', detail_package, name='fullname_package_detail_api'),
    #url(r'^packages/repository/(?P<provider>[+\w.-]+)(/(?P<distribution>[+\w.-]+))?(/(?P<architecture>[+\w.-]+))?(/(?P<branch>[+\w.-]+))?(/(?P<section>[+\w.-]+))?/+$',
    url(r'^packages/repository/(?P<provider>[+\w.-]+)?/?((?P<distribution>[+\w.-]+))?/?((?P<architecture>[+\w.-]+))?/?((?P<branch>[+\w.-]+))?/?((?P<section>[+\w.-]+))?/+$',
        list_packages, {'Model' : Repository}, name='repository_packages_api'),
    url(r'^packages/file/(?P<query>[+\w.-]+)/$', list_packages, {'Model' : File, 'field' : 'name' } ,name='file_search_api'),
    url(r'^packages/path/(?P<query>[+\w./-]+)/$', list_packages, {'Model' : File, 'field' : 'path' } ,name='file_path_search_api'),
    url(r'(?u)^packages/changelog/(?P<query>[+ @*<>:\w./-]+)/$', list_packages, {'Model' : Changelog, 'field' : 'log' } ,name='changelog_search_api'),
    url(r'^packages/fullname/(?P<query>[+\w.-]+)/$', list_packages, {'Model' : Package, 'field' : 'fullname' }, name='package_search_api'),
    url(r'^packages/(name/)?(?P<query>[+\w.-]+)/$', list_packages, {'Model' : Package, 'field' : 'name' }, name='package_name_search_api'),
    url(r'^packages/category/(?P<query>[+ \w./-]+)/$', list_packages, {'Model' : Package, 'field' : 'category' } ,name='category_search_api'),
    url(r'(?u)^packages/summary/(?P<query>[+ \w./-]+)/$', list_packages, {'Model' : Package, 'field' : 'summary' } ,name='summary_search_api'),
    url(r'(?u)^packages/description/(?P<query>[+ \w./-]+)/$', list_packages, {'Model' : Package, 'field' : 'description' } ,name='description_search_api'),
    url(r'(?u)^packages/author/(?P<query>[+ \w./-]+)/$', list_packages, {'Model' : Package, 'field' : 'author' } ,name='author_search_api'),
    url(r'(?u)^packages/author_email/(?P<query>[+@\w./-]+)/$', list_packages, {'Model' : Package, 'field' : 'author_email' } ,name='author_email_search_api'),
)

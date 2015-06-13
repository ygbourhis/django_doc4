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

from django.conf.urls.defaults import patterns, include, url

from django.conf import settings
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.views.generic.list_detail import object_list, object_detail
from views import detail_package_object, list_package_object, list_packages, list_repositories
from models import File, Provide, Require, Obsolete, Conflict, Suggest, InUnScript, Changelog, Package, Repository, REPOSITORY_PACKAGE_SEARCH_URL

from api.urls import urlpatterns as apiurlpatterns

urlpatterns = patterns('',
    # Example:
    # url(r'^django_doc4/', include('django_doc4.foo.urls'), name='docs'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls'), name='admin_docs'),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls), name='admin_interface'),
    
)

#package pages:
urlpatterns += patterns('',
    url(r'^$', list_packages, name='home_page_package_list'),
    url(r'^packages/$', list_packages, name='package_list'),
    url(r'^repositories/$', list_repositories, name='repository_list'),
    #details per id:
    url(r'^(?P<package_id>\d+)/$', detail_package_object, {'Model' : Package}, name='package_detail'),
    url(r'^(?P<package_id>\d+)/inunscript/$', detail_package_object, {'Model' : InUnScript}, name='inunscript_detail'),
    url(r'^(?P<package_id>\d+)/changelog/$', detail_package_object, {'Model' : Changelog}, name='changelog_detail'),
    url(r'^(?P<package_id>\d+)/files/$', list_package_object, {'Model' : File}, name='file_list'),
    url(r'^(?P<package_id>\d+)/provides/$', list_package_object, {'Model' : Provide}, name='provide_list'),
    url(r'^(?P<package_id>\d+)/requires/$', list_package_object, {'Model' : Require}, name='require_list'),
    url(r'^(?P<package_id>\d+)/obsoletes/$', list_package_object, {'Model' : Obsolete}, name='obsolete_list'),
    url(r'^(?P<package_id>\d+)/conflicts/$', list_package_object, {'Model' : Conflict}, name='conflict_list'),
    url(r'^(?P<package_id>\d+)/suggests/$', list_package_object, {'Model' : Suggest}, name='suggest_list'),
    #details per fullname:
    url(r'^package/(?P<package_fullname>[+\w.-]+)/$', detail_package_object, {'Model' : Package}, name='fullname_package_detail'),
    url(r'^package/(?P<package_fullname>[+\w.-]+)/inunscript/$', detail_package_object, {'Model' : InUnScript}, name='fullname_inunscript_detail'),
    url(r'^package/(?P<package_fullname>[+\w.-]+)/changelog/$', detail_package_object, {'Model' : Changelog}, name='fullname_changelog_detail'),
    url(r'^package/(?P<package_fullname>[+\w.-]+)/files/$', list_package_object, {'Model' : File}, name='fullname_file_list'),
    url(r'^package/(?P<package_fullname>[+\w.-]+)/provides/$', list_package_object, {'Model' : Provide}, name='fullname_provide_list'),
    url(r'^package/(?P<package_fullname>[+\w.-]+)/requires/$', list_package_object, {'Model' : Require}, name='fullname_require_list'),
    url(r'^package/(?P<package_fullname>[+\w.-]+)/obsoletes/$', list_package_object, {'Model' : Obsolete}, name='fullname_obsolete_list'),
    url(r'^package/(?P<package_fullname>[+\w.-]+)/conflicts/$', list_package_object, {'Model' : Conflict}, name='fullname_conflict_list'),
    url(r'^package/(?P<package_fullname>[+\w.-]+)/suggests/$', list_package_object, {'Model' : Suggest}, name='fullname_suggest_list'),
    
    #search urls:
    url(r'^packages/file/(?P<query>[+\w.-]+)/$', list_packages, {'Model' : File, 'field' : 'name' } ,name='file_search'),
    url(r'^packages/path/(?P<query>[+\w./-]+)/$', list_packages, {'Model' : File, 'field' : 'path' } ,name='file_path_search'),
    url(r'(?u)^packages/changelog/(?P<query>[+ @*<>:\w./-]+)/$', list_packages, {'Model' : Changelog, 'field' : 'log' } ,name='changelog_search'),
    url(r'^packages/fullname/(?P<query>[+\w.-]+)/$', list_packages, {'Model' : Package, 'field' : 'fullname' } ,name='package_search'),
    url(r'^packages/(name/)?(?P<query>[+\w.-]+)/$', list_packages, {'Model' : Package, 'field' : 'name' } ,name='package_name_search'),
    url(r'^packages/category/(?P<query>[+ \w./-]+)/$', list_packages, {'Model' : Package, 'field' : 'category' } ,name='category_search'),
    url(r'(?u)^packages/summary/(?P<query>[+ \w./-]+)/$', list_packages, {'Model' : Package, 'field' : 'summary' } ,name='summary_search'),
    url(r'(?u)^packages/description/(?P<query>[+ \w./-]+)/$', list_packages, {'Model' : Package, 'field' : 'description' } ,name='description_search'),
    url(r'(?u)^packages/author/(?P<query>[+ \w./-]+)/$', list_packages, {'Model' : Package, 'field' : 'author' } ,name='author_search'),
    url(r'(?u)^packages/author_email/(?P<query>[+@\w./-]+)/$', list_packages, {'Model' : Package, 'field' : 'author_email' } ,name='author_email_search'),
    #If you change the url bellow, please edit models.Repository.get_absolute_url, which isn't DRY because of http://code.djangoproject.com/ticket/9176
    # REPOSITORY_PACKAGE_SEARCH_URL = 'search/category/' is prepended to the regex (%s)
    #url(r'^%s(?P<provider>[+\w.-]+)(/(?P<distribution>[+\w.-]+))?(/(?P<architecture>[+\w.-]+))?(/(?P<branch>[+\w.-]+))?(/(?P<section>[+\w.-]+))?/+$' % REPOSITORY_PACKAGE_SEARCH_URL,
    url(r'^%s(?P<provider>[+\w.-]+)?/?((?P<distribution>[+\w.-]+))?/?((?P<architecture>[+\w.-]+))?/?((?P<branch>[+\w.-]+))?/?((?P<section>[+\w.-]+))?/+$' % REPOSITORY_PACKAGE_SEARCH_URL,
        list_packages, {'Model' : Repository}, name='repository_packages'),
)

#api urls:
urlpatterns += patterns('',
    (r'^api/', include(apiurlpatterns)),
)

#serve static pages during development:
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }, name='serve_media'),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }, name='serve_static'),
        url(r'^upmi/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.EXTRACTION_DIR,
        }, name='serve_upmi'),
   )

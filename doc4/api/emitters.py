#-*- coding:utf-8 -*-

from piston.emitters import Emitter, XMLEmitter, YAMLEmitter, JSONEmitter, PickleEmitter
from django.utils.encoding import smart_unicode

from doc4.models import Package, Repository

#Creat custom emitter if required, and register it like this:
#Emitter.register('xml', XMLEmitter, 'text/xml; charset=utf-8')
Emitter.unregister('django')
Emitter.unregister('xml')

class DOC4XMLEmitter(XMLEmitter):
    def _to_xml(self, xml, data, startelement='resource'):
        startelements = {
            'packages' : 'package',
            'repositories' : 'repository',
            'files' : 'file',
            'changelogs' : 'changelog',
            'obsoletes' : 'obsolete',
            'conflicts' : 'conflict',
            'suggests' : 'suggestion',
            'scripts' : 'script',
            'requires' : 'required',
            'provides' : 'provided',
            'sub_categories' : 'sub_category',
            'categories' : 'category',
        }
        startelement = startelements.get(startelement, startelement)
        if isinstance(data, (list, tuple)):
            for item in data:
                xml.startElement(startelement, {})
                self._to_xml(xml, item)
                xml.endElement(startelement)
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                xml.startElement(key, {})
                self._to_xml(xml, value, key)
                xml.endElement(key)
        else:
            xml.characters(smart_unicode(data))

Emitter.register('xml', DOC4XMLEmitter, 'text/xml; charset=utf-8')

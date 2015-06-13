# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding index on 'Package', fields ['arch']
        db.create_index(u'doc4_packages', ['arch'])


    def backwards(self, orm):
        
        # Removing index on 'Package', fields ['arch']
        db.delete_index(u'doc4_packages', ['arch'])


    models = {
        'doc4.bugstat': {
            'Meta': {'object_name': 'Bugstat', 'db_table': "u'doc4_bugstats'"},
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'distribution': ('django.db.models.fields.CharField', [], {'max_length': '765', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'property': ('django.db.models.fields.CharField', [], {'max_length': '765'}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'doc4.changelog': {
            'Meta': {'object_name': 'Changelog', 'db_table': "u'doc4_changelogs'"},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'date': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']", 'null': 'True', 'blank': 'True'})
        },
        'doc4.conflict': {
            'Meta': {'object_name': 'Conflict', 'db_table': "u'doc4_conflicts'"},
            'epoch': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'flags': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']"}),
            'pre': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'releas': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.contributor': {
            'Meta': {'object_name': 'Contributor'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_mymandriva': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'pseudo': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.file': {
            'Meta': {'object_name': 'File', 'db_table': "u'doc4_files'"},
            'cat': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'extra': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '765', 'db_index': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']"}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '12000', 'db_index': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.installabilityviolationentry': {
            'Meta': {'object_name': 'InstallabilityViolationEntry', 'db_table': "u'doc4_installability'"},
            'architecture': ('django.db.models.fields.CharField', [], {'max_length': '765', 'db_index': 'True'}),
            'conflict': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'conflict_file': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'cstr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'dependency_avl': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'dependency_cstr': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'dependency_name': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'distribution': ('django.db.models.fields.CharField', [], {'max_length': '765', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '765', 'db_index': 'True'}),
            'object_cstr': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'object_name': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.inunscript': {
            'Meta': {'object_name': 'InUnScript', 'db_table': "u'doc4_scripts'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']"}),
            'postin': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'postun': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'prein': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'preun': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'doc4.license': {
            'Meta': {'object_name': 'License', 'db_table': "u'doc4_licenses'"},
            'abbreviation': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'doc4.licensedefinition': {
            'Meta': {'object_name': 'LicenseDefinition', 'db_table': "u'doc4_license_definition'"},
            'abbreviation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.License']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '765'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'doc4.obsolete': {
            'Meta': {'object_name': 'Obsolete', 'db_table': "u'doc4_obsoletes'"},
            'epoch': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'flags': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']"}),
            'pre': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'releas': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.package': {
            'Meta': {'object_name': 'Package', 'db_table': "u'doc4_packages'"},
            'arch': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '765', 'blank': 'True'}),
            'archive_size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'author_email': ('django.db.models.fields.EmailField', [], {'max_length': '765', 'blank': 'True'}),
            'build_host': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'build_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '765', 'blank': 'True'}),
            'checksum': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '765', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'epoch': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'file_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fullname': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '765', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_maintainer': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'installed_size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_source': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '765', 'blank': 'True'}),
            'releas': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'repos': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['doc4.Repository']", 'symmetrical': 'False'}),
            'sha1': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sloc_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'top_category': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '765', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.packagelicense': {
            'Meta': {'object_name': 'PackageLicense', 'db_table': "u'doc4_package_licenses'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '765'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']"})
        },
        'doc4.provide': {
            'Meta': {'object_name': 'Provide', 'db_table': "u'doc4_provides'"},
            'epoch': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'flags': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '765', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']"}),
            'pre': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'releas': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.queue': {
            'Meta': {'object_name': 'Queue'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'error_message': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'hash_type': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '765', 'db_index': 'True'}),
            'snapshot': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Snapshot']"}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.repository': {
            'Meta': {'object_name': 'Repository', 'db_table': "u'doc4_repositories'"},
            'architecture': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'distribution': ('django.db.models.fields.CharField', [], {'max_length': '765', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'section': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.repositoryhistory': {
            'Meta': {'object_name': 'RepositoryHistory', 'db_table': "u'doc4_history'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']"}),
            'snapshot': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Snapshot']"})
        },
        'doc4.require': {
            'Meta': {'object_name': 'Require', 'db_table': "u'doc4_requires'"},
            'epoch': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'flags': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '765', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']"}),
            'pre': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'releas': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.slocstat': {
            'Meta': {'object_name': 'SlocStat', 'db_table': "u'doc4_sloccount'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '765'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']"}),
            'percent': ('django.db.models.fields.FloatField', [], {}),
            'sloccount': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'doc4.snapshot': {
            'Meta': {'object_name': 'Snapshot', 'db_table': "u'doc4_snapshots'"},
            'file_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_last': ('django.db.models.fields.NullBooleanField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'package_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Repository']"}),
            'sloc_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'snapshot_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        'doc4.suggest': {
            'Meta': {'object_name': 'Suggest', 'db_table': "u'doc4_suggests'"},
            'epoch': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'flags': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Package']"}),
            'pre': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'releas': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'})
        },
        'doc4.targetrepos': {
            'Meta': {'object_name': 'TargetRepos', 'db_table': "u'doc4_target_repositories'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['doc4.Repository']"})
        }
    }

    complete_apps = ['doc4']

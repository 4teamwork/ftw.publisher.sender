from Products.PloneTestCase.ptc import PloneTestCase
from ftw.publisher.core.interfaces import IDataCollector
from ftw.publisher.core.utils import encode_after_json
from ftw.publisher.sender.extractor import Extractor
from ftw.publisher.sender.tests.layer import Layer
from zope.component import getAdapters
import unittest
import json


class TestExtractor(PloneTestCase):
    layer = Layer

    def afterSetUp(self):
        # add some default plone types
        testdoc1id = self.folder.invokeFactory('Document', 'test-doc-1')
        self.testdoc1 = getattr(self.folder, testdoc1id, None)
        topicid = self.folder.manage_addProduct['ATContentTypes'].addATTopic(
            id='topic1', title='topic 1')
        self.topic1 = getattr(self.folder, topicid, None)
        self.extractor = Extractor()
        self.extractor(self.testdoc1, 'delete')

    def test_extractor_object(self):
        adapters = getAdapters((self.testdoc1, ), IDataCollector)
        expected_adapters = [u'field_data_adapter',
                             u'properties_data_adapter',
                             u'backreferences_adapter',
                             u'interface_data_adapter',
                             u'portlet_data_adapter',
                             u'geo_data_adapter']
        list_adapters = []
        for name, adapter in adapters:
            list_adapters.append(name)
        self.assertEquals(set(expected_adapters), set(list_adapters))

    def test_extractor_topic(self):
        adapters = getAdapters((self.topic1, ), IDataCollector)
        expected_adapters = [u'field_data_adapter',
                             u'properties_data_adapter',
                             u'backreferences_adapter',
                             u'topic_critera_adapter',
                             u'interface_data_adapter',
                             u'portlet_data_adapter',
                             u'geo_data_adapter']
        list_adapters = []
        for name, adapter in adapters:
            list_adapters.append(name)
        self.assertEquals(set(expected_adapters), set(list_adapters))

    def test_getMetadata(self):
        metadata = self.extractor.getMetadata('delete')

        expected_metadata = {
            'UID': metadata['UID'],
            'portal_type': 'Document',
            'modified': 'MODIFIED',
            'physicalPath': '/Members/test_user_1_/test-doc-1',
            'schema_path':
                'Products.ATContentTypes.content.document.ATDocument.schema',
            'sibling_positions': {'topic1': 1,
                                  'test-doc-1': 0},
            'action': 'delete',
            'review_state': 'private',
            'id': 'test-doc-1'}

        self.assertTrue('modified' in metadata)
        metadata['modified'] = 'MODIFIED'

        self.assertEquals(expected_metadata, metadata)

    def test_ignoreFields(self):
        # first all fields are in data
        jsondata = self.extractor(self.testdoc1, 'push')
        # decode from json
        data = json.loads(jsondata)
        data = encode_after_json(data)
        self.assertTrue('description' in data['field_data_adapter'])
        self.assertTrue('excludeFromNav' in data['field_data_adapter'])

        # now ignore some fields
        from ftw.publisher.sender.interfaces import IConfig
        config = IConfig(self.portal)
        config.set_ignored_fields({'Document': ['description',
                                                'excludeFromNav']})

        jsondata = self.extractor(self.testdoc1, 'push')
        # decode from json
        data = json.loads(jsondata)
        data = encode_after_json(data)
        self.assertTrue('description' not in data['field_data_adapter'])
        self.assertTrue('excludeFromNav' not in data['field_data_adapter'])

    def test_getRelativePath(self):
        path = self.extractor.getRelativePath()
        self.assertEquals(path, '/Members/test_user_1_/test-doc-1')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

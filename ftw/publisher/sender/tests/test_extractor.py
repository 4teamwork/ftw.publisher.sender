from datetime import datetime
from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.core.interfaces import IDataCollector
from ftw.publisher.core.utils import encode_after_json
from ftw.publisher.sender.extractor import Extractor
from ftw.publisher.sender.interfaces import IConfig
from ftw.publisher.sender.tests import FunctionalTestCase
from ftw.publisher.sender.utils import IS_AT_LEAST_PLONE_5_1
from ftw.publisher.sender.utils import IS_PLONE_4
from ftw.testing import freeze
from ftw.testing import staticuid
from unittest import skipUnless
from zope.component import getAdapters
import json


class TestExtractor(FunctionalTestCase):

    def test_extractors_are_registered(self):
        self.grant('Manager')
        adapters = getAdapters((create(Builder('folder')),), IDataCollector)
        self.assertIn(u'properties_data_adapter', dict(adapters))

    @skipUnless(IS_PLONE_4, 'Plone 4 version')
    @staticuid()
    def test_delete_job_get_metadata_plone_4(self):
        self.grant('Manager')
        with freeze(datetime(2030, 1, 2, 4, 5)) as clock:
            folder = create(Builder('folder').titled(u'The Folder')
                            .within(create(Builder('folder').titled(u'Foo'))))
            clock.forward(hours=1)
            data = encode_after_json(json.loads(Extractor()(folder, 'delete', {})))

        self.maxDiff = None
        self.assertEquals(
            {'metadata': {'UID': 'testdeletejobgetmetadatapl000002',
                          'action': 'delete',
                          'id': 'the-folder',
                          'modified': '2030/01/02 04:05:00 GMT+1',
                          'physicalPath': '/foo/the-folder',
                          'portal_type': 'Folder',
                          'review_state': '',
                          'sibling_positions': {'the-folder': 0}}},
            data)

    @skipUnless(IS_AT_LEAST_PLONE_5_1, 'Plone 5 version')
    @staticuid()
    def test_delete_job_get_metadata_plone_5(self):
        self.grant('Manager')
        with freeze(datetime(2030, 1, 2, 4, 5)) as clock:
            folder = create(Builder('folder').titled(u'The Folder')
                            .within(create(Builder('folder').titled(u'Foo'))))
            clock.forward(hours=1)
            data = encode_after_json(json.loads(Extractor()(folder, 'delete', {})))

        self.maxDiff = None
        self.assertEquals(
            {'metadata': {'UID': 'testdeletejobgetmetadatapl000002',
                          'action': 'delete',
                          'id': 'the-folder',
                          'modified': '2030/01/02 04:05:00 GMT+1',
                          'physicalPath': '/foo/the-folder',
                          'portal_type': 'Folder',
                          'review_state': '',
                          'sibling_positions': {'the-folder': 0}}},
            data)

    @skipUnless(IS_PLONE_4, 'Plone 4 version')
    def test_ignoring_fields_of_field_data_adapter_plone_4(self):
        self.grant('Manager')
        folder = create(Builder('folder').titled(u'Foo'))
        data = encode_after_json(json.loads(Extractor()(folder, 'push', {})))
        self.assertIn('field_data_adapter', data)
        self.assertIn('description', data['field_data_adapter'])

        IConfig(self.portal).set_ignored_fields({'Folder': ['description']})
        data = encode_after_json(json.loads(Extractor()(folder, 'push', {})))
        self.assertNotIn('description', data['field_data_adapter'])

    @skipUnless(IS_AT_LEAST_PLONE_5_1, 'Plone 5 version')
    def test_ignoring_fields_of_field_data_adapter_plone_5(self):
        self.grant('Manager')
        folder = create(Builder('folder').titled(u'Foo'))
        data = encode_after_json(json.loads(Extractor()(folder, 'push', {})))
        self.assertIn('dx_field_data_adapter', data)
        self.assertIn('IDublinCore', data['dx_field_data_adapter'])
        self.assertIn('description', data['dx_field_data_adapter']['IDublinCore'])

        IConfig(self.portal).set_ignored_fields({'Folder': ['description']})
        data = encode_after_json(json.loads(Extractor()(folder, 'push', {})))
        self.assertNotIn('description', data['dx_field_data_adapter']['IDublinCore'])

    @skipUnless(IS_PLONE_4, 'Plone 4 version')
    @staticuid()
    def test_archetypes_folder_extractor(self):
        self.grant('Manager')
        self.maxDiff = None

        with freeze(datetime(2030, 1, 2, 4, 5)):
            folder = create(Builder('folder')
                            .titled(u'A folder')
                            .having(description=u'Description of the folder')
                            .within(create(Builder('folder').titled(u'Foo'))))

        self.assertDictEqual(
            encode_after_json(json.loads(self.asset('folder_at.json').text())),
            encode_after_json(json.loads(Extractor()(folder, 'push', {})))
        )

    @skipUnless(IS_AT_LEAST_PLONE_5_1, 'Plone 5 version')
    @staticuid()
    def test_dexterity_folder_extractor(self):
        self.grant('Manager')
        self.maxDiff = None

        with freeze(datetime(2030, 1, 2, 4, 5)):
            folder = create(Builder('folder')
                            .titled(u'A folder')
                            .having(description=u'Description of the folder')
                            .within(create(Builder('folder').titled(u'Foo'))))

        self.assertDictEqual(
            encode_after_json(json.loads(self.asset('folder_dx.json').text())),
            encode_after_json(json.loads(Extractor()(folder, 'push', {})))
        )

    @skipUnless(IS_PLONE_4, 'Plone 4 version')
    @staticuid()
    def test_archetypes_image_extractor(self):
        self.grant('Manager')
        self.maxDiff = None

        with freeze(datetime(2030, 1, 2, 4, 5)):
            image = create(Builder('image')
                           .titled(u'An image')
                           .with_dummy_content()
                           .having(description=u'Description of the image')
                           .within(create(Builder('folder').titled(u'Foo'))))

        self.assertDictEqual(
            encode_after_json(json.loads(self.asset('image_at.json').text())),
            encode_after_json(json.loads(Extractor()(image, 'push', {})))
        )

    @skipUnless(IS_AT_LEAST_PLONE_5_1, 'Plone 5 version')
    @staticuid()
    def test_dexterity_image_extractor(self):
        self.grant('Manager')
        self.maxDiff = None

        with freeze(datetime(2030, 1, 2, 4, 5)):
            image = create(Builder('image')
                           .titled(u'An image')
                           .with_dummy_content()
                           .having(description=u'Description of the image')
                           .within(create(Builder('folder').titled(u'Foo'))))

        self.assertDictEqual(
            encode_after_json(json.loads(self.asset('image_dx.json').text())),
            encode_after_json(json.loads(Extractor()(image, 'push', {})))
        )

from ftw.publisher.sender.interfaces import IConfig, IPathBlacklist
from ftw.publisher.sender.tests import FunctionalTestCase
from persistent.list import PersistentList


class TestBlacklist(FunctionalTestCase):

    def test_item_can_be_added_to_blacklist(self):
        config = IConfig(self.portal)
        config.setPathBlacklist(PersistentList())

        # The blacklist is empty by default.
        self.assertEqual(0, len(config.getPathBlacklist()))

        # Items can be added to the blacklist.
        config.appendPathToBlacklist('hans')
        self.assertIn(
            'hans',
            config.getPathBlacklist()
        )
        self.assertEqual(1, len(config.getPathBlacklist()))

    def test_blacklist_does_not_affect_parents(self):
        config = IConfig(self.portal)
        config.setPathBlacklist(PersistentList())
        config.appendPathToBlacklist('/foo/bar/one/two/three')
        blacklist = IPathBlacklist(self.portal)

        self.assertFalse(blacklist.is_blacklisted('/foo/bar'))
        self.assertFalse(blacklist.is_blacklisted('/foo/bar/one/two'))
        self.assertTrue(blacklist.is_blacklisted('/foo/bar/one/two/three'))

    def test_blacklisting_recursive_children_does_not_affect_parents(self):
        config = IConfig(self.portal)
        config.setPathBlacklist(PersistentList())
        config.appendPathToBlacklist('/foo/bar/one/*')
        blacklist = IPathBlacklist(self.portal)

        self.assertFalse(blacklist.is_blacklisted('/foo/bar'))
        self.assertTrue(blacklist.is_blacklisted('/foo/bar/one/two'))
        self.assertFalse(blacklist.is_blacklisted('/foo/bar/oneXXXXX'))
        self.assertTrue(blacklist.is_blacklisted('/foo/bar/one/two/three'))

    def test_blacklisting_trailing_wildcards_does_not_affect_parents(self):
        config = IConfig(self.portal)
        config.setPathBlacklist(PersistentList())
        config.appendPathToBlacklist('/foo/bar/one*')
        blacklist = IPathBlacklist(self.portal)

        self.assertFalse(blacklist.is_blacklisted('/foo/bar'))
        self.assertTrue(blacklist.is_blacklisted('/foo/bar/one'))
        self.assertFalse(blacklist.is_blacklisted('/foo/bar/one/two'))
        self.assertTrue(blacklist.is_blacklisted('/foo/bar/oneXXXX'))

    def test_portal_can_be_blacklisted(self):
        config = IConfig(self.portal)
        config.setPathBlacklist(PersistentList())
        blacklist = IPathBlacklist(self.portal)

        # The portal is not blacklisted by default.
        self.assertFalse(blacklist.is_blacklisted(self.portal))

        # Blacklist the portal.
        config.appendPathToBlacklist('/'.join(self.portal.getPhysicalPath()))
        self.assertTrue(blacklist.is_blacklisted(self.portal))

    def test_blacklisting_intermediate_wildcards_does_not_affect_parents(self):
        config = IConfig(self.portal)
        config.setPathBlacklist(PersistentList())
        config.appendPathToBlacklist('/demo/one*two')
        blacklist = IPathBlacklist(self.portal)

        self.assertFalse(blacklist.is_blacklisted('/demo/one'))
        self.assertFalse(blacklist.is_blacklisted('/demo/oneXtwo'))
        self.assertFalse(blacklist.is_blacklisted('/demo/one/two'))

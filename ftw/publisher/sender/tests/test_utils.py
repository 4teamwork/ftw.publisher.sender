from ftw.publisher.sender.utils import is_temporary
from ftw.testing import MockTestCase


class TestIsTemporary(MockTestCase):

    def test_no_parent_is_temporary(self):
        obj = self.mock()
        self.set_parent(obj, None)
        self.assertTrue(is_temporary(obj))

    def test_not_in_parent(self):
        obj = self.mock()
        parent = self.mock()
        self.set_parent(obj, parent)
        obj.getId.return_value = 'foo'
        parent.foo.side_effect = None
        self.assertTrue(is_temporary(obj))

    def test_isTemporary_True(self):
        obj = self.mock()
        self.set_parent(obj, self.stub())
        obj.getId.return_value = 'foo'
        obj.isTemporary.return_value = True
        self.assertTrue(is_temporary(obj))

    def test_isTemporary_raises(self):
        obj = self.mock()
        self.set_parent(obj, self.stub())
        obj.getId.return_value = 'foo'
        obj.isTemporary.side_effect = TypeError()
        self.assertTrue(is_temporary(obj))

    def test_not_temporary(self):
        obj = self.mock()
        parent = self.mock()
        self.set_parent(obj, parent)

        obj.getId.return_value = 'foo'
        parent.foo.side_effect = obj
        obj.isTemporary.return_value = False
        self.assertFalse(is_temporary(obj))

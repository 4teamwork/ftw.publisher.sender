from ftw.publisher.sender.utils import is_temporary
from ftw.testing import MockTestCase


class TestIsTemporary(MockTestCase):

    def test_no_parent_is_temporary(self):
        obj = self.mocker.mock()
        self.set_parent(obj, None)

        self.replay()
        self.assertTrue(is_temporary(obj))

    def test_not_in_parent(self):
        obj = self.mocker.mock()
        parent = self.mocker.mock()
        self.set_parent(obj, parent)

        self.expect(obj.getId()).result('foo')
        self.expect(parent.foo, None)

        self.replay()

        self.assertTrue(is_temporary(obj))

    def test_isTemporary_True(self):
        obj = self.mocker.mock()
        self.set_parent(obj, self.stub())
        self.expect(obj.getId).result(None)
        self.expect(obj.isTemporary()).result(True)

        self.replay()
        self.assertTrue(is_temporary(obj))

    def test_isTemporary_raises(self):
        obj = self.mocker.mock()
        self.set_parent(obj, self.stub())
        self.expect(obj.getId).result(None)
        self.expect(obj.isTemporary()).throw(TypeError())

        self.replay()
        self.assertTrue(is_temporary(obj))

    def test_not_temporary(self):
        obj = self.mocker.mock()
        parent = self.mocker.mock()
        self.set_parent(obj, parent)

        self.expect(obj.getId()).result('foo')
        self.expect(parent.foo).result(obj)
        self.expect(obj.isTemporary()).result(False)

        self.replay()
        self.assertFalse(is_temporary(obj))

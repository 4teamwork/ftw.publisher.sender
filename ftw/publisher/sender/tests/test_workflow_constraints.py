from Products.statusmessages.interfaces import IStatusMessage
from ftw.publisher.sender import _
from ftw.publisher.sender.workflows import constraints
from ftw.publisher.sender.workflows import interfaces
from ftw.testing import MockTestCase
from plone.mocktestcase.dummy import Dummy
from unittest2 import TestCase
from zope.interface import Interface
from zope.interface.verify import verifyClass


class ConstraintDefinition1(constraints.ConstraintDefinition):

    @constraints.message(_('Fohoo'))
    @constraints.error_on(interfaces.PUBLISH)
    @constraints.warning_on(interfaces.SUBMIT)
    def foo(self):
        return False

    @constraints.message(_('Bahar'))
    @constraints.error_on(interfaces.PUBLISH, interfaces.SUBMIT)
    def bar(self):
        return False


class ConstraintDefinition2(constraints.ConstraintDefinition):

    @constraints.message(_('X ${item} Y'))
    @constraints.error_on(interfaces.PUBLISH)
    def baz(self):
        foo = Dummy(absolute_url=lambda: 'http://host/foo',
                    Title=lambda: 'Foo')
        bar = Dummy(absolute_url=lambda: 'http://host/bar',
                    Title=lambda: 'Bar')
        return [foo, bar]


class TestDecorators(TestCase):

    def test_message_decorator(self):
        @constraints.message(u'Foo bar')
        def foo():
            return 2

        self.assertEqual(foo._publisher_message, 'Foo bar')
        self.assertEqual(foo(), 2)

    def test_publisher_error_on_decorator(self):
        @constraints.error_on(interfaces.SUBMIT, interfaces.PUBLISH)
        def foo():
            return 2

        self.assertEqual(foo._publisher_error_on, (
                interfaces.SUBMIT, interfaces.PUBLISH))
        self.assertEqual(foo(), 2)

    def test_publisher_warning_on_decorator(self):
        @constraints.warning_on(interfaces.SUBMIT, interfaces.PUBLISH)
        def foo():
            return 2

        self.assertEqual(foo._publisher_warning_on, (
                interfaces.SUBMIT, interfaces.PUBLISH))
        self.assertEqual(foo(), 2)


class TestConstraintDefinition(TestCase):

    def test_implements_interface(self):
        self.assertTrue(interfaces.IConstraintDefinition.implementedBy(
                constraints.ConstraintDefinition))
        verifyClass(interfaces.IConstraintDefinition,
                    constraints.ConstraintDefinition)

    def test_definition1_submit(self):
        constriants = ConstraintDefinition1(None, None)

        self.assertEqual(constriants.check_action(interfaces.SUBMIT),
                         {'errors': ['Bahar'],
                          'warnings': ['Fohoo']})

    def test_definition1_publish(self):
        constriants = ConstraintDefinition1(None, None)

        self.assertEqual(constriants.check_action(interfaces.PUBLISH),
                         {'errors': ['Bahar', 'Fohoo'],
                          'warnings': []})

    def test_definition2_multi_objects(self):
        constriants = ConstraintDefinition2(None, None)

        self.assertEqual(
            constriants.check_action(interfaces.PUBLISH),
            {'errors': ['X <a href="http://host/foo">Foo</a> Y',
                        'X <a href="http://host/bar">Bar</a> Y'],
             'warnings': []})


class TestConstraintStatusMessages(MockTestCase):

    def setUp(self):
        super(TestConstraintStatusMessages, self).setUp()

        self.context = self.create_dummy()
        self.request = self.create_dummy()

        status_message = self.stub()
        self.mock_adapter(status_message, IStatusMessage, [Interface])
        self.msg = self.mocker.mock()
        self.expect(status_message(self.request)).result(self.msg)

    def test_definition1_submit(self):
        self.expect(self.msg.addStatusMessage('Bahar', type='error'))
        self.expect(self.msg.addStatusMessage('Fohoo', type='warning'))

        self.replay()
        constriants = ConstraintDefinition1(self.context, self.request)
        self.assertFalse(constriants.is_action_allowed(interfaces.SUBMIT))

    def test_definition1_publish(self):
        self.expect(self.msg.addStatusMessage('Bahar', type='error'))
        self.expect(self.msg.addStatusMessage('Fohoo', type='error'))

        self.replay()
        constriants = ConstraintDefinition1(self.context, self.request)
        self.assertFalse(constriants.is_action_allowed(interfaces.PUBLISH))

    def test_definition2_success(self):

        self.replay()
        constriants = ConstraintDefinition2(self.context, self.request)
        self.assertTrue(constriants.is_action_allowed(interfaces.SUBMIT))

    def test_definition2_multi_objects(self):
        self.expect(self.msg.addStatusMessage(
                'X <a href="http://host/foo">Foo</a> Y', type='error'))
        self.expect(self.msg.addStatusMessage(
                'X <a href="http://host/bar">Bar</a> Y', type='error'))

        self.replay()
        constriants = ConstraintDefinition2(self.context, self.request)
        self.assertFalse(constriants.is_action_allowed(interfaces.PUBLISH))

    def test_no_messages_when_silent(self):
        self.replay()
        constriants = ConstraintDefinition2(self.context, self.request)
        self.assertFalse(constriants.is_action_allowed(interfaces.PUBLISH,
                                                       silent=True))

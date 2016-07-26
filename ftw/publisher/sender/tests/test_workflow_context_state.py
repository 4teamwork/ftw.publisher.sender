from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.testing import PUBLISHER_SENDER_INTEGRATION_TESTING
from ftw.publisher.sender.workflows.contextstate import PublisherContextState
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from plone.app.relationfield.behavior import IRelatedItems
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from unittest2 import TestCase
from z3c.relationfield.event import _setRelation
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
from zope.interface.verify import verifyClass
from z3c.relationfield.relation import create_relation


def get_state(context):
    return getMultiAdapter((context, context.REQUEST),
                           IPublisherContextState)


EXAMPLE_WF_INTERNAL = 'publisher-example-workflow--STATUS--internal'
EXAMPLE_WF_PUBLISHED = 'publisher-example-workflow--STATUS--published'
EXAMPLE_WF_REVISION = 'publisher-example-workflow--STATUS--revision'


class TestPublisherContextState(TestCase):

    layer = PUBLISHER_SENDER_INTEGRATION_TESTING

    def setUp(self):
        super(TestPublisherContextState, self).setUp()

        self.portal = self.layer['portal']
        self.request = self.portal.REQUEST
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        self.wftool = getToolByName(self.portal, 'portal_workflow')
        self.wftool.setChainForPortalTypes(
            ['Document', 'Folder'],
            'publisher-example-workflow')

    def test_component_registered(self):
        page = create(Builder('page'))
        state = queryMultiAdapter((page, self.request),
                                  IPublisherContextState)
        self.assertTrue(state)
        self.assertEqual(type(state), PublisherContextState)

    def test_implements_interface(self):
        self.assertTrue(IPublisherContextState.implementedBy(
                PublisherContextState))
        verifyClass(IPublisherContextState, PublisherContextState)

    def test_page_has_workflow(self):
        # workflow for type "Document" (alias "page") is installed in "setUp"
        page = create(Builder('page'))
        self.assertTrue(get_state(page).has_workflow())

    def test_page_has_publisher_config(self):
        page = create(Builder('page'))
        self.assertTrue(get_state(page).has_publisher_config())

    def test_portal_has_no_publisher_config(self):
        self.assertFalse(get_state(self.portal).has_publisher_config())

    def test_portal_has_no_workflow(self):
        self.assertFalse(get_state(self.portal).has_workflow())

    def test_get_workflow(self):
        page = create(Builder('page'))
        page_workflow = get_state(page).get_workflow()
        self.assertEquals('publisher-example-workflow', page_workflow.id)

    def test_get_workflow__portal(self):
        portal_workflow = get_state(self.portal).get_workflow()
        self.assertEquals(None, portal_workflow)

    def test_get_review_state__page(self):
        page = create(Builder('page'))
        self.assertEquals(EXAMPLE_WF_INTERNAL,
                          get_state(page).get_review_state())

    def test_get_review_state__portal(self):
        self.assertEquals(None, get_state(self.portal).get_review_state())

    def test_is_published__positive(self):
        published_page = create(Builder('page')
                                .in_state(EXAMPLE_WF_PUBLISHED))
        self.assertTrue(get_state(published_page).is_published(),
                        'Expected the page to be published')

    def test_is_published__negative(self):
        internal_page = create(Builder('page')
                                .in_state(EXAMPLE_WF_INTERNAL))
        self.assertFalse(get_state(internal_page).is_published(),
                         'Expected the page to be not published')

    def test_is_parent_published__positive(self):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_PUBLISHED))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_INTERNAL))
        self.assertTrue(get_state(page).is_parent_published(),
                        'Expected parent folder to be published')

    def test_is_parent_published__negative(self):
        folder = create(Builder('folder')
                        .in_state(EXAMPLE_WF_INTERNAL))
        page = create(Builder('page')
                      .within(folder)
                      .in_state(EXAMPLE_WF_PUBLISHED))
        self.assertFalse(get_state(page).is_parent_published(),
                        'Expected parent folder not to be published')

    def test_is_parent_published__positive__when_parent_has_no_workflow(self):
        folder = create(Builder('folder').in_state(EXAMPLE_WF_PUBLISHED))
        page = create(Builder('content page').within(folder))  # no wf
        subpage = create(Builder('content page').within(page))  # no wf

        self.assertTrue(get_state(subpage).is_parent_published(),
                        'Expected parent folder not to be published')

    def test_is_parent_published__negeative__when_parent_has_no_workflow(self):
        folder = create(Builder('folder').in_state(EXAMPLE_WF_INTERNAL))
        page = create(Builder('content page').within(folder))  # no wf
        subpage = create(Builder('content page').within(page))  # no wf

        self.assertFalse(get_state(subpage).is_parent_published(),
                         'Expected parent folder not to be published')

    def test_getting_unpublished_references(self):
        foo = create(Builder('page').titled('Foo'))
        bar = create(Builder('page').titled('Bar'))
        bar.setRelatedItems(foo)

        self.assertEquals(
            [foo], list(get_state(bar).get_unpublished_references()))

        self._set_state_of(foo, EXAMPLE_WF_PUBLISHED)
        self.assertEquals(
            [], list(get_state(bar).get_unpublished_references()))

    def test_getting_published_references(self):
        foo = create(Builder('page').titled('Foo')
                     .in_state(EXAMPLE_WF_PUBLISHED))
        bar = create(Builder('page').titled('Bar'))
        bar.setRelatedItems(foo)

        self.assertEquals(
            [foo], list(get_state(bar).get_published_references()))

        self._set_state_of(foo, EXAMPLE_WF_INTERNAL)
        self.assertEquals(
            [], list(get_state(bar).get_published_references()))

    def test_do_not_fail_getting_published_references_if_ref_is_none(self):
        foo = create(Builder('page').titled('Foo')
                     .in_state(EXAMPLE_WF_PUBLISHED))
        bar = create(Builder('page').titled('Bar'))
        bar.setRelatedItems(foo)
        self.portal._delObject(foo.getId(), suppress_events=True)

        self.assertEquals(
            [], list(get_state(bar).get_published_references()))

    def test_references_dx_to_dx(self):
        foo = create(Builder('example dx type').titled(u'Foo'))
        bar = create(Builder('example dx type').titled(u'Bar'))

        foo_relation = create_relation('/'.join(foo.getPhysicalPath()))
        IRelatedItems(bar).relatedItems = [foo_relation]
        _setRelation(bar, 'relatedItems', foo_relation)
        self.assertEquals(
            [foo],
            list(get_state(bar).get_references())
        )

    def test_references_at_to_dx(self):
        dx = create(Builder('example dx type').titled(u'DX'))
        at = create(Builder('page').titled('AT'))
        at.setRelatedItems(dx)
        self.assertEquals(
            [dx],
            list(get_state(at).get_references())
        )

    def test_references_dx_to_at(self):
        at = create(Builder('page').titled('AT'))
        dx = create(Builder('example dx type').titled(u'DX'))
        at_relation = create_relation('/'.join(at.getPhysicalPath()))
        IRelatedItems(dx).relatedItems = [at_relation]
        _setRelation(dx, 'relatedItems', at_relation)
        self.assertEquals(
            [at],
            list(get_state(dx).get_references())
        )

    def _set_state_of(self, obj, state):
        self.wftool.setStatusOf('publisher-example-workflow', obj,
                                {'review_state': state})

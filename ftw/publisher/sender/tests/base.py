from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.sender.workflows import interfaces
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from Products.CMFCore.utils import getToolByName
from unittest2 import TestCase
from zope.component import getAdapter
from zope.component import getMultiAdapter


class WorkflowConfigTest(TestCase):

    workflow_id = None
    publisher_transition_view = 'publisher-modify-status'

    def setUp(self):
        if self._is_base_test():
            return

        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)

        wftool = getToolByName(portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Document'], self.workflow_id)

    def _is_base_test(self):
        """Detect that the class was not subclassed so we can skip the tests.
        """
        return type(self) == WorkflowConfigTest

    def test_all_states_are_in_workflow(self):
        if self._is_base_test():
            return

        config = self.get_config()
        self.assertEquals(
            set(self.get_workflow().states),
            set(config.states().keys()),
            '%s the publisher configuration does not declare all states.' % (
                self.workflow_id))

    def test_all_states_have_valid_kinds(self):
        if self._is_base_test():
            return

        invalid_states = []
        config = self.get_config()
        for state, kind in config.states().items():
            if kind not in interfaces.VALID_STATES:
                invalid_states.append((state, kind))

        self.assertEquals(
            [], invalid_states,
            '%s: some states have invalid kinds. Allowed: %s' % (
                self.workflow_id, str(interfaces.VALID_STATES)))

    def test_all_transitions_are_in_workflow(self):
        if self._is_base_test():
            return

        config = self.get_config()
        self.assertEquals(
            set(self.get_workflow().transitions),
            set(config.transitions().keys()),
            '%s the publisher configuration does not declare all states.' % (
                self.workflow_id))

    def test_all_transitions_have_valid_kinds(self):
        if self._is_base_test():
            return

        invalid_transitions = []
        config = self.get_config()
        for transition, kind in config.transitions().items():
            if kind not in interfaces.VALID_ACTIONS:
                invalid_transitions.append((transition, kind))

        self.assertEquals(
            [], invalid_transitions,
            '%s: some transitions have invalid kinds. Allowed: %s' % (
                self.workflow_id, str(interfaces.VALID_ACTIONS)))

    def test_all_transitions_pointing_to_published_states_do_publish(self):
        if self._is_base_test():
            return

        invalid_transitions = []
        config = self.get_config()
        workflow = self.get_workflow()

        published_states = []
        for state, kind in config.states().items():
            if kind == interfaces.PUBLISHED:
                published_states.append(state)

        for transition_id, kind in config.transitions().items():
            transition = workflow.transitions.get(transition_id)
            if transition.new_state_id not in published_states:
                continue

            origin_kinds = self.get_transition_origin_kinds(transition_id)
            has_not_published_origins = (
                origin_kinds - set(interfaces.PUBLISHED_STATES))
            if not has_not_published_origins:
                # The transition goes from a public state to a public state,
                # therefore it is allowed to not publish this transition.
                continue

            if kind != interfaces.PUBLISH:
                invalid_transitions.append((transition, kind,
                                            transition.new_state_id))

        self.assertEquals(
            [], invalid_transitions,
            'Some transitions do point to a published state but are'
            ' not configured to publish.')

    def test_transition_actions_have_publisher_action(self):
        if self._is_base_test():
            return

        workflow = self.get_workflow()
        invalid_transitions = []
        for transition_id, transition in workflow.transitions.items():
            url = transition.actbox_url
            expected_url = '%(content_url)s/' +\
                '%s?transition=%s' % (
                    self.publisher_transition_view,
                    transition_id)

            if url != expected_url:
                invalid_transitions.append({'transition_id': transition_id,
                                            'got': url,
                                            'expected': expected_url})

        self.assertEquals(
            [], invalid_transitions,
            'Some transitions have invalid actions. Publisher workflows'
            ' should be configured to always call "publisher-modify-status"'
            ' for every transition, regardless wether they publish or not.')

    def test_workflow_has_constraint_definition(self):
        if self._is_base_test():
            return

        folder = create(Builder('folder'))
        page = create(Builder('page').within(folder))

        constraints = getMultiAdapter((page, page.REQUEST),
                                      interfaces.IConstraintDefinition,
                                      name=self.workflow_id)
        self.assertTrue(constraints)

    def get_config(self):
        return getAdapter(self.layer['request'],
                          interfaces.IWorkflowConfiguration,
                          name=self.workflow_id)

    def get_workflow(self):
        if self._is_base_test():
            return

        if getattr(self, '_workflow', None) is None:
            portal = self.layer['portal']
            wftool = getToolByName(portal, 'portal_workflow')
            workflow = wftool.get(self.workflow_id)
            self.assertTrue(workflow, 'Could not find workflow "%s"' % (
                    self.workflow_id))
            self._workflow = workflow
        return self._workflow

    def get_transition_origin_kinds(self, transition_id):
        workflow = self.get_workflow()
        config = self.get_config()

        state_kinds = set([])
        for state in workflow.states.values():
            if transition_id in state.transitions:
                state_kinds.add(config.states()[state.id])

        return state_kinds

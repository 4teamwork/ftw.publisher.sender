from Products.CMFCore.utils import getToolByName
from ftw.publisher.sender.testing import PUBLISHER_SENDER_INTEGRATION_TESTING
from ftw.publisher.sender.workflows import interfaces
from unittest2 import TestCase
from zope.component import getAdapter


class TestExampleWorkflowConfig(TestCase):

    layer = PUBLISHER_SENDER_INTEGRATION_TESTING
    workflow_id = 'publisher-example-workflow'

    def test_all_states_are_in_workflow(self):
        config = self.get_config()
        self.assertEquals(
            set(self.get_workflow().states),
            set(config.states().keys()),
            '%s the publisher configuration does not declare all states.' % (
                self.workflow_id))

    def test_all_states_have_valid_kinds(self):
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
        config = self.get_config()
        self.assertEquals(
            set(self.get_workflow().transitions),
            set(config.transitions().keys()),
            '%s the publisher configuration does not declare all states.' % (
                self.workflow_id))

    def test_all_transitions_have_valid_kinds(self):
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

            if kind != interfaces.PUBLISH:
                invalid_transitions.append((transition, kind,
                                            transition.new_state_id))

        self.assertEquals(
            [], invalid_transitions,
            'Some transitions do point to a published state but are'
            ' not configured to publish.')

    def test_transition_actions_have_publisher_action(self):
        workflow = self.get_workflow()
        invalid_transitions = []
        for transition_id, transition in workflow.transitions.items():
            url = transition.actbox_url
            expected_url = '%%(content_url)s/publisher-modify-status/%s' % (
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

    def get_config(self):
        return getAdapter(self.layer['request'],
                          interfaces.IWorkflowConfiguration,
                          name=self.workflow_id)

    def get_workflow(self):
        portal = self.layer['portal']
        wftool = getToolByName(portal, 'portal_workflow')
        workflow = wftool.get(self.workflow_id)
        self.assertTrue(workflow, 'Could not find workflow "%s"' % (
                self.workflow_id))
        return workflow

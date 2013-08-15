from Products.CMFCore.utils import getToolByName
from ftw.publisher.sender.workflows import interfaces
from plone.i18n.normalizer.interfaces import INormalizer
from zope.component import adapts
from zope.component import getUtility
from zope.component import queryAdapter
from zope.interface import Interface
from zope.interface import implements
import re


class LawgiverWorkflowConfiguration(object):
    implements(interfaces.IWorkflowConfiguration)
    adapts(Interface)

    def __init__(self, request):
        self.request = request

    def states(self):
        states = {}
        for title, kind in self.lawgiver_states().items():
            states[self._status_id(title)] = kind
        return states

    def transitions(self):
        transitions = {}
        for title, kind in self.lawgiver_transitions().items():
            transitions[self._transition_id(title)] = kind
        return transitions

    def _transition_id(self, transition):
        xpr = re.compile(r'([^\(]*?) ?\(([^=]*?) ?=> ?([^\(]*)\)')
        match = xpr.match(transition.lower())
        if not match:
            raise ValueError(
                'Transition line has an invalid format: "%s"' % transition)

        return '%s--TRANSITION--%s--%s_%s' % tuple(
            [self.workflow_id,] + map(self._normalize, match.groups()))

    def _status_id(self, status_title):
        return '%s--STATUS--%s' % (
            self.workflow_id, self._normalize(status_title))

    def _normalize(self, text):
        if isinstance(text, str):
            text = text.decode('utf-8')

        normalizer = getUtility(INormalizer)
        result = normalizer.normalize(text)
        return result.decode('utf-8')


class PublisherConfigs(object):
    implements(interfaces.IWorkflowConfigs)

    def is_published(self, context):
        state = self.get_state_of(context)
        return state in self.get_state_ids_with_kind(interfaces.PUBLISHED,
                                                     context)

    def is_in_revision(self, context):
        state = self.get_state_of(context)
        return state in self.get_state_ids_with_kind(interfaces.REVISION,
                                                     context)

    def get_config_for(self, context):
        wftool = getToolByName(context, 'portal_workflow')
        workflows = wftool.getWorkflowsFor(context)

        if len(workflows) == 0:
            return None

        workflow_id = workflows[0].id
        return queryAdapter(context.REQUEST,
                            interfaces.IWorkflowConfiguration,
                            name=workflow_id)

    def get_state_ids_with_kind(self, kind, context):
        state_ids = []
        config = self.get_config_for(context)
        if not config:
            return []
        for state_id, state_kind in config.states().items():
            if state_kind == kind:
                state_ids.append(state_id)
        return state_ids

    def get_state_of(self, context):
        wftool = getToolByName(context, 'portal_workflow')
        return wftool.getInfoFor(context, 'review_state', None)

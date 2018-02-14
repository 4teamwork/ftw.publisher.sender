from Products.Five import BrowserView
from ftw.publisher.sender.workflows import interfaces
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import implements

try:
    from plone.protect.utils import addTokenToUrl
except ImportError:
    # Plone 4 ships plone.protect 2.x, missing `addTokenToUrl`.
    HAS_MODERN_PLONE_PROTECT = False
else:
    # Plone >= 5 ships plone.protect 3.x featuring `addTokenToUrl`.
    HAS_MODERN_PLONE_PROTECT = True


class ModifyStatusView(BrowserView):
    implements(interfaces.IModifyStatus)

    def __init__(self, context, request):
        super(ModifyStatusView, self).__init__(context, request)
        self._context_state = None
        self._constraint_definition = None

    def __call__(self):
        transition = self.request.get('transition')
        if not transition:
            raise ValueError('No transition passed.')

        if self.is_transition_allowed(transition):
            target_url = self.get_transition_action(transition)

            if HAS_MODERN_PLONE_PROTECT:
                target_url = addTokenToUrl(target_url)

            self.request.RESPONSE.redirect(target_url)

        else:
            self.request.RESPONSE.redirect(
                self.context.absolute_url())

    def get_transition_action(self, transition):
        return '%s/content_status_modify?workflow_action=%s' % (
            self.context.absolute_url(),
            transition)

    def is_transition_allowed(self, transition, silent=False):
        action = self._get_transition_action(transition)
        if action is None:
            return True

        return self.get_constraints().is_action_allowed(
            action, silent=silent)

    def _get_transition_action(self, transition):
        config = getUtility(interfaces.IWorkflowConfigs).get_config_for(
            self.context)

        if config is None:
            return None

        return config.transitions().get(transition, None)

    def get_constraints(self):
        if self._constraint_definition is None:
            workflow_name = self.get_context_state().get_workflow().id
            self._constraint_definition = getMultiAdapter(
                (self.context, self.request),
                interfaces.IConstraintDefinition,
                name=workflow_name)
        return self._constraint_definition

    def get_context_state(self):
        if self._context_state is None:
            self._context_state = getMultiAdapter(
                (self.context, self.request),
                interfaces.IPublisherContextState)
        return self._context_state

from Acquisition import aq_parent, aq_inner
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from ftw.publisher.sender.workflows.interfaces import IWorkflowConfigs
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import implements


class PublisherContextState(object):
    implements(IPublisherContextState)
    adapts(Interface, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def has_workflow(self):
        return self.get_workflow() is not None

    def get_workflow(self):
        wftool = getToolByName(self.context, 'portal_workflow')
        workflows = wftool.getWorkflowsFor(self.context)

        if len(workflows) == 0:
            return None

        assert len(workflows) == 1, 'Multiple workflows are unsupported'
        return workflows[0]

    def get_review_state(self):
        wftool = getToolByName(self.context, 'portal_workflow')
        return wftool.getInfoFor(self.context, 'review_state', None)

    def is_published(self):
        if IPloneSiteRoot.providedBy(self.context):
            return True

        configs = getUtility(IWorkflowConfigs)
        return configs.is_published(self.context)

    def is_in_revision(self):
        configs = getUtility(IWorkflowConfigs)
        return configs.is_in_revision(self.context)

    def get_parent_state(self):
        parent = aq_parent(aq_inner(self.context))
        parent_state = getMultiAdapter((parent, self.request),
                                       IPublisherContextState)
        return parent_state

    def is_parent_published(self):
        parent_state = self.get_parent_state()
        return parent_state.is_published()

    def get_unpublished_references(self):
        try:
            referenceable = IReferenceable(self.context)
        except TypeError:
            # could not adapt
            # this means we have a dexterity object without
            # plone.app.referenceablebehavior activated.
            return

        for obj in referenceable.getReferences():
            obj_state = getMultiAdapter((obj, self.request),
                                        IPublisherContextState)

            if not obj_state.is_published():
                yield obj

    def get_published_references(self):
        for obj in self.context.getReferences():
            obj_state = getMultiAdapter((obj, self.request),
                                        IPublisherContextState)

            if obj_state.is_published():
                yield obj

    def get_published_children(self):
        for obj in self.context.getFolderContents(full_objects=True):
            obj_state = getMultiAdapter((obj, self.request),
                                        IPublisherContextState)

            if obj_state.has_workflow() and obj_state.is_published():
                yield obj

    def get_workflow_config(self):
        configs = getUtility(IWorkflowConfigs)
        return configs.get_config_for(self.context)
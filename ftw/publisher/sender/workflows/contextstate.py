from Acquisition import aq_parent, aq_inner
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from ftw.publisher.sender.workflows.interfaces import IWorkflowConfigs
from operator import attrgetter
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import implements
from zope.interface import Interface
import pkg_resources

try:
    pkg_resources.get_distribution('zc.relation')
except pkg_resources.DistributionNotFound:
    HAS_ZC_CATALOG = False
else:
    HAS_ZC_CATALOG = True
    from zope.intid.interfaces import IIntIds
    from zc.relation.interfaces import ICatalog


class PublisherContextState(object):
    implements(IPublisherContextState)
    adapts(Interface, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def has_workflow(self):
        return self.get_workflow() is not None

    def has_publisher_config(self):
        config = getUtility(IWorkflowConfigs).get_config_for(self.context)
        return config is not None

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
        return configs.is_published(self.context) or self.is_in_revision()

    def is_in_revision(self):
        configs = getUtility(IWorkflowConfigs)
        return configs.is_in_revision(self.context)

    def get_closest_parent_having_workflow(self):
        """Visits the parents of an object by walking up. If the parent
        has a workflow then that object (the parent) is returned.
        When the plone site is reached then that object (the plone site)
        is returned.
        """
        workflow_tool = getToolByName(self.context, 'portal_workflow')
        parent = aq_parent(aq_inner(self.context))

        while True:
            chain = workflow_tool.getChainFor(parent)
            if chain or IPloneSiteRoot.providedBy(parent):
                return parent
            parent = aq_parent(aq_inner(parent))

    def get_parent_state(self):
        parent = self.get_closest_parent_having_workflow()
        parent_state = getMultiAdapter((parent, self.request),
                                       IPublisherContextState)
        return parent_state

    def is_parent_published(self):
        parent_state = self.get_parent_state()
        return parent_state.is_published()

    def get_unpublished_references(self):
        for obj in self.get_references():
            if obj is None:
                continue

            obj_state = getMultiAdapter((obj, self.request),
                                        IPublisherContextState)

            if not obj_state.is_published():
                yield obj

    def get_published_references(self):
        for obj in self.get_references():
            if obj is None:
                continue

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

    def get_references(self):
        """Returns the references of the current context.
        """
        return self._get_references_for(self.context)

    def _get_references_for(self, context):
        try:
            referenceable = IReferenceable(context)
        except TypeError:
            # could not adapt
            # this means we have a dexterity object without
            # plone.app.referenceablebehavior activated.
            objs = []
        else:
            objs = referenceable.getReferences()

        if HAS_ZC_CATALOG:
            relation_catalog = getUtility(ICatalog)
            obj_intid = getUtility(IIntIds).getId(context)
            relation_catalog.findRelations({'from_id': obj_intid})
            relations = tuple(relation_catalog.findRelations({'from_id': obj_intid}))
            objs += map(attrgetter('to_object'), relations)

        return list(set(objs))

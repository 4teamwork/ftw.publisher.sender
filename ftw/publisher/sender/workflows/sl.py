from ftw.publisher.sender.workflows.contextstate import PublisherContextState
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from simplelayout.base.interfaces import ISimpleLayoutBlock
from simplelayout.base.interfaces import ISimpleLayoutCapable
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.interface import Interface


class SimplelayoutContainerContextState(PublisherContextState):
    adapts(ISimpleLayoutCapable, Interface)

    def get_references(self):
        """Returns the references of the current context.
        """

        references = list(self._get_references_for(self.context))
        for block in self.get_blocks_without_worfklows():
            references.extend(self._get_references_for(block))

        return references

    def get_blocks_without_worfklows(self):
        for obj in self.context.objectValues():
            if not ISimpleLayoutBlock.providedBy(obj):
                continue

            state = getMultiAdapter((obj, self.request),
                                    IPublisherContextState)
            if state.has_workflow():
                continue

            yield obj

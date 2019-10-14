from ftw.publisher.sender.workflows.contextstate import PublisherContextState
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from ftw.simplelayout.interfaces import ISimplelayout
from ftw.simplelayout.interfaces import ISimplelayoutBlock
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.interface import Interface


class FtwSimplelayoutContainerContextState(PublisherContextState):
    adapts(ISimplelayout, Interface)

    def get_references(self):
        """Returns the references of the current context.
        """

        references = list(self._get_references_for(self.context))
        for block in self.get_blocks_without_worfklows():
            references.extend(self._get_references_for(block))

        return references

    def get_blocks_without_worfklows(self):
        # Use contentValues for implicit ftw.trash compatibility.
        for obj in self.context.contentValues():
            if not ISimplelayoutBlock.providedBy(obj):
                continue

            state = getMultiAdapter((obj, self.request),
                                    IPublisherContextState)
            if state.has_workflow():
                continue

            yield obj

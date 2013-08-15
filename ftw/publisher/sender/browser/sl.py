from ftw.publisher.sender.browser.views import PublishObject
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from simplelayout.base.interfaces import ISimpleLayoutBlock
from zope.component import getMultiAdapter


class PublishSimplelayoutContainer(PublishObject):

    def __call__(self, *args, **kwargs):
        result = super(PublishSimplelayoutContainer, self).__call__(
            *args, **kwargs)

        for obj in self.context.objectValues():
            if not ISimpleLayoutBlock.providedBy(obj):
                continue

            state = getMultiAdapter((obj, self.request),
                                    IPublisherContextState)
            if state.has_workflow():
                continue

            obj.restrictedTraverse('@@publisher.publish')(*args, **kwargs)

        return result


class PublishFolderishSimplelayoutBlocks(PublishObject):

    def __call__(self, *args, **kwargs):
        result = super(PublishFolderishSimplelayoutBlocks, self).__call__(
            *args, **kwargs)

        for obj in self.context.objectValues():
            state = getMultiAdapter((obj, self.request),
                                    IPublisherContextState)
            if state.has_workflow():
                continue

            obj.restrictedTraverse('@@publisher.publish')(*args, **kwargs)

        return result

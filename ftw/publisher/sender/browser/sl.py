from ftw.publisher.sender.browser.views import PublishObject
from ftw.publisher.sender.workflows.interfaces import IPublisherContextState
from zope.component import getMultiAdapter
import pkg_resources

SL_BLOCK_INTERFACES = []

try:
    pkg_resources.get_distribution('simplelayout.base')
except pkg_resources.DistributionNotFound:
    pass
else:
    from simplelayout.base.interfaces import ISimpleLayoutBlock
    SL_BLOCK_INTERFACES.append(ISimpleLayoutBlock)


try:
    pkg_resources.get_distribution('ftw.simplelayout')
except pkg_resources.DistributionNotFound:
    pass
else:
    from ftw.simplelayout.interfaces import ISimplelayoutBlock
    SL_BLOCK_INTERFACES.append(ISimplelayoutBlock)
    from ftw.simplelayout.configuration import synchronize_page_config_with_blocks


def is_simplelayout_block(context):
    for iface in SL_BLOCK_INTERFACES:
        if iface.providedBy(context):
            return True
    return False


class PublishSimplelayoutContainer(PublishObject):

    def __call__(self, *args, **kwargs):
        result = super(PublishSimplelayoutContainer, self).__call__(
            *args, **kwargs)

        for obj in self.context.objectValues():
            if not is_simplelayout_block(obj):
                continue

            state = getMultiAdapter((obj, self.request),
                                    IPublisherContextState)
            if state.has_workflow():
                continue

            obj.restrictedTraverse('@@publisher.publish')(*args, **kwargs)

        return result


class PublishFtwSimplelayoutContainer(PublishSimplelayoutContainer):

    def __call__(self, *args, **kwargs):
        synchronize_page_config_with_blocks(self.context)
        super(PublishFtwSimplelayoutContainer, self).__call__(*args, **kwargs)



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

from ftw.publisher.core.adapters.ftw_simplelayout import is_sl_contentish
from ftw.publisher.sender.browser.views import PublishObject
from ftw.simplelayout.configuration import synchronize_page_config_with_blocks


class PublishSLObject(PublishObject):

    def __call__(self, *args, **kwargs):
        result = super(PublishSLObject, self).__call__(*args, **kwargs)

        for obj in filter(is_sl_contentish, self.context.objectValues()):
            obj.restrictedTraverse('@@publisher.publish')(*args, **kwargs)

        return result


class PublishSLContainer(PublishSLObject):

    def __call__(self, *args, **kwargs):
        synchronize_page_config_with_blocks(self.context)
        return super(PublishSLContainer, self).__call__(*args, **kwargs)

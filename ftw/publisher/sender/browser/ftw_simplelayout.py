from ftw.publisher.sender.browser.views import PublishObject
from ftw.simplelayout.configuration import synchronize_page_config_with_blocks


class PublishSLContainer(PublishObject):

    def __call__(self, *args, **kwargs):
        synchronize_page_config_with_blocks(self.context)
        return super(PublishSLContainer, self).__call__(*args, **kwargs)

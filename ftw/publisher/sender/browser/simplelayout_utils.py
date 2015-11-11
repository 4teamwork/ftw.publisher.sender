from ftw.publisher.core.adapters.simplelayout_utils import is_sl_contentish
from ftw.publisher.sender.browser.views import PublishObject


class PublishSLObject(PublishObject):

    def __call__(self, *args, **kwargs):
        result = super(PublishSLObject, self).__call__(*args, **kwargs)

        for obj in filter(is_sl_contentish, self.context.objectValues()):
            obj.restrictedTraverse('@@publisher.publish')(*args, **kwargs)

        return result

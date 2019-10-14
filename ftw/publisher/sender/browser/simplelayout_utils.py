from ftw.publisher.core import belongs_to_parent
from ftw.publisher.sender.browser.views import PublishObject


class PublishSLObject(PublishObject):

    def __call__(self, *args, **kwargs):
        result = super(PublishSLObject, self).__call__(*args, **kwargs)

        for obj in filter(belongs_to_parent, self.context.objectValues()):
            obj.restrictedTraverse('@@publisher.publish')(*args, **kwargs)

        return result

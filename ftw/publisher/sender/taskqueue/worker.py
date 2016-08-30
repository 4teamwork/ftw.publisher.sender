from ftw.publisher.sender import getLogger
from ftw.publisher.sender.extractor import Extractor
from plone import api
from Products.Five.browser import BrowserView
import os


class PublisherExtractObject(BrowserView):

    def __call__(self):
        logger = getLogger()

        action = self.request.form['action']
        filepath = self.request.form['filepath']
        path = self.request.form['path']

        obj = api.portal.get().unrestrictedTraverse(path, None)

        if obj is None:
            os.remove(filepath)
            logger.warning(
                'Removed "{0}", since the destination {1} no longer '
                'exists'.format(filepath, path))
            return 'JSON File "{0}" removed'.format(filepath)

        extractor = Extractor()
        data = extractor(obj, action)

        with open(filepath, 'w') as target:
            target.write(data)

        return 'OK'

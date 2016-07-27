from ftw.publisher.sender.extractor import Extractor
from Products.Five.browser import BrowserView


class PublisherExtractObject(BrowserView):

    def __call__(self):
        action = self.request.form['action']
        filepath = self.request.form['filepath']

        extractor = Extractor()
        data = extractor(self.context, action)

        with open(filepath, 'w') as target:
            target.write(data)

        return 'OK'

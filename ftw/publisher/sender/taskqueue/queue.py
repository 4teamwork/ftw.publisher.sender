from collective.taskqueue import taskqueue
from ftw.publisher.sender import getLogger
from ftw.publisher.sender.extractor import Extractor
from plone import api
from Products.Five.browser import BrowserView
from zope.annotation import IAnnotations
import json
import os
import uuid


TOKEN_ANNOTATION_KEY = 'ftw.publisher.sender:deferred-extraction-token'


def enqueue_deferred_extraction(obj, action, filepath, additional_data,
                                attempt=1, token=None):
    callback_path = '/'.join(api.portal.get().getPhysicalPath() +
                             ('taskqueue_publisher_extract_object',))

    # Set a token on the object so that we can make sure that we extract
    # this version of the object later in the worker.
    if token is None:
        token = str(uuid.uuid4())
        IAnnotations(obj)[TOKEN_ANNOTATION_KEY] = token

    path = '/'.join(obj.getPhysicalPath())
    taskqueue.add(callback_path, params={
        'action': action,
        'filepath': filepath,
        'path': path,
        'attempt:int': attempt,
        'token': token,
        'additional_data': json.dumps(dict(additional_data))})


class PublisherExtractObjectWorker(BrowserView):

    def __call__(self):
        logger = getLogger()

        action = self.request.form['action']
        filepath = self.request.form['filepath']
        path = self.request.form['path']
        additional_data = json.loads(self.request.form['additional_data'])

        obj = api.portal.get().unrestrictedTraverse(path, None)

        require_token = self.request.form['token']
        current_token = IAnnotations(obj).get(TOKEN_ANNOTATION_KEY, None)
        if current_token != require_token:
            # The current version of the object is not the version we have
            # planned to extract.
            attempt = self.request.form['attempt']
            if attempt == 1:
                # Lets retry for solving the problem that the worker is too
                # early and the transaction which triggered the action was not
                # yet commited to the database.
                return enqueue_deferred_extraction(
                    obj, action, filepath, additional_data,
                    attempt=attempt + 1,
                    token=require_token)

            else:
                raise Exception(
                    'Unexpected object version' +
                    ' after {!r} attempts.'.format(attempt) +
                    ' Required token: {!r},'.format(require_token) +
                    ' got token: {!r}'.format(current_token))

        if obj is None:
            os.remove(filepath)
            logger.warning(
                'Removed "{0}", since the destination {1} no longer '
                'exists'.format(filepath, path))
            return 'JSON File "{0}" removed'.format(filepath)

        extractor = Extractor()
        data = extractor(obj, action, additional_data)

        with open(filepath, 'w') as target:
            target.write(data)

        return 'OK'

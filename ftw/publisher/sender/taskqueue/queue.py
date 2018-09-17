from collective.taskqueue import taskqueue
from ftw.publisher.core.utils import decode_for_json
from ftw.publisher.core.utils import encode_after_json
from ftw.publisher.sender import getLogger
from ftw.publisher.sender.extractor import Extractor
from plone import api
from Products.Five.browser import BrowserView
from time import sleep
from zope.annotation import IAnnotations
import json
import os
import uuid


TOKEN_ANNOTATION_KEY = 'ftw.publisher.sender:deferred-extraction-token'
MAX_ATTEMPTS = 10
TIMEOUT_BETWEEN_ATTEMPTS = 0.5


def enqueue_deferred_extraction(obj, action, filepath, additional_data,
                                attempt=1, token=None, path=None):
    callback_path = '/'.join(api.portal.get().getPhysicalPath() +
                             ('taskqueue_publisher_extract_object',))

    if obj is None and (path is None or token is None):
        raise ValueError('When obj is None, path and token must be provided.')
    elif obj is not None:
        path = '/'.join(obj.getPhysicalPath())

    # Set a token on the object so that we can make sure that we extract
    # this version of the object later in the worker.
    if token is None:
        token = str(uuid.uuid4())
        IAnnotations(obj)[TOKEN_ANNOTATION_KEY] = token

    taskqueue.add(callback_path, params={
        'action': action,
        'filepath': filepath,
        'path': path,
        'attempt:int': attempt,
        'token': token,
        'additional_data': json.dumps(decode_for_json(dict(dict(additional_data))))})


class PublisherExtractObjectWorker(BrowserView):

    def __call__(self):
        logger = getLogger()

        action = self.request.form['action']
        filepath = self.request.form['filepath']
        path = self.request.form['path']
        additional_data = encode_after_json(json.loads(self.request.form['additional_data']))
        obj = api.portal.get().unrestrictedTraverse(path, None)
        require_token = self.request.form['token']
        attempt = self.request.form['attempt']

        if obj is None:
            if attempt < MAX_ATTEMPTS:
                sleep(TIMEOUT_BETWEEN_ATTEMPTS)
                return enqueue_deferred_extraction(
                    None, action, filepath, additional_data,
                    attempt=attempt + 1,
                    token=require_token,
                    path=path)
            else:
                os.remove(filepath)
                logger.warning(
                    'Removed "{0}", since the destination {1} no longer '
                    'exists.'.format(filepath, path))
                return 'JSON File "{0}" removed'.format(filepath)

        current_token = IAnnotations(obj).get(TOKEN_ANNOTATION_KEY, None)

        if current_token != require_token:
            # The current version of the object is not the version we have
            # planned to extract.
            if attempt < MAX_ATTEMPTS:
                # Lets retry for solving the problem that the worker is too
                # early and the transaction which triggered the action was not
                # yet commited to the database.
                sleep(TIMEOUT_BETWEEN_ATTEMPTS)
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

        extractor = Extractor()
        data = extractor(obj, action, additional_data)

        with open(filepath, 'w') as target:
            target.write(data)

        return 'OK'

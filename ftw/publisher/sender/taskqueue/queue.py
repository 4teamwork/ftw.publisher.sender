from collective.taskqueue import taskqueue
from plone import api


def enqueue_deferred_extraction(obj, action, filepath):
    callback_path = '/'.join(api.portal.get().getPhysicalPath() +
                             ('taskqueue_publisher_extract_object',))

    path = '/'.join(obj.getPhysicalPath())
    taskqueue.add(callback_path, params={'action': action,
                                         'filepath': filepath,
                                         'path': path})

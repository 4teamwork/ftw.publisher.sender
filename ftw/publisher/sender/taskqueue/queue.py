from collective.taskqueue import taskqueue


def enqueue_deferred_extraction(obj, action, filepath):
    callback_path = '/'.join(obj.getPhysicalPath() +
                             ('taskqueue_publisher_extract_object',))
    taskqueue.add(callback_path, params={'action': action,
                                         'filepath': filepath})

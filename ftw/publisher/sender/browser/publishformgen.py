from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from ftw.publisher.sender import getLogger
from ftw.publisher.sender import message_factory as _
from ftw.publisher.sender.persistence import Queue


class PublishObject(BrowserView):
    """
    This BrowserView adds the current object (self.context) to the publishing queue.
    """
    def __call__(self, no_response=False, msg=None, *args, **kwargs):
        """
        This is a copy from the orginal publisher.publish view for
        PloneFormGen.
        it also publishs all its contents
        """
        self.logger = getLogger()

        # get username
        user = self.context.portal_membership.getAuthenticatedMember()
        username = user.getUserName()
        # create Job
        queue = Queue(self.context)
        queue.createJob('push', self.context, username)
        self.logger.info('Created "%s" Job for "%s" at %s' % (
                'push',
                self.context.Title(),
                '/'.join(self.context.getPhysicalPath()),
                ))

        # Get all items recursively and add theme to the queue
        def add_item_to_queue(items):
            for item in items:
                queue.createJob('push', item, username)
                subitems = item.objectValues()
                if subitems:
                    add_item_to_queue(subitems)
        add_item_to_queue(self.context.objectValues())

        # status message
        if msg is None:
            msg = _(u'This object has been added to the queue.')
        IStatusMessage(self.request).addStatusMessage(
            msg,
            type='info'
            )
        if not no_response:
            return self.request.RESPONSE.redirect('./view')

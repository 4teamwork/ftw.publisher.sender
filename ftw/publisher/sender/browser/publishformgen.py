#
# File:     communication.py
# Author:   Jonas Baumann <j.baumann@4teamwork.ch>
# Modified: 06.03.2009
#
# Copyright (c) 2007 by 4teamwork.ch
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
__author__ = """Mathias Leimgruber <m.leimgruber@4teamwork.ch>"""


# zope imports
from Products.Five import BrowserView

# plone imports
from Products.statusmessages.interfaces import IStatusMessage

# publisher imports
from ftw.publisher.sender.persistence import Queue
from ftw.publisher.sender import getLogger


"""
@var BATCH_SIZE:        Maximum amount of Jobs to be performed at one ExecuteQueue call
"""
BATCH_SIZE = 0

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
        
        # get all blocks and add them to the queue too
        items = self.context.objectValues()
        for item in items:
            queue.createJob('push', item, username)
        
        
        # status message
        if msg is None:
            msg = 'This object has been added to the queue.'
        IStatusMessage(self.request).addStatusMessage(
                msg,
                type='info'
        )
        if not no_response:
            return self.request.RESPONSE.redirect('./view')


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
__author__ = """Jonas Baumann <j.baumann@4teamwork.ch>"""

# python imports
from StringIO import StringIO
import logging

# zope imports
from Products.Five import BrowserView

# plone imports
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.statusmessages.interfaces import IStatusMessage

# publisher imports
from ftw.publisher.sender.persistence import Queue, Config
from ftw.publisher.sender.utils import sendJsonToRealm
from ftw.publisher.sender import extractor
from ftw.publisher.sender import getLogger
from ftw.publisher.core import states

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile 

# event
from ftw.publisher.sender.events import AfterPushEvent
from zope import event

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
        The __call__ method is used to execute the BrowserView. It creates and
        adds a "PUSH"-Job on the current context to the queue.
        @param args:    list of unnamed arguments
        @type args:     list
        @param kwargs:  dict of named keyword-arguments
        @type kwargs:   dict
        @return:        Redirect to object`s default view
        """
        self.logger = getLogger()
        # This View should not be executed at the PloneSiteRoot
        if IPloneSiteRoot.providedBy(self.context):
            raise Exception('Not allowed on PloneSiteRoot')
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
        # status message
        if msg is None:
            msg = 'This object has been added to the queue.'
        IStatusMessage(self.request).addStatusMessage(
                msg,
                type='info'
        )
        if not no_response:
            return self.request.RESPONSE.redirect('./view')


class MoveObject(BrowserView):
    """
    This BrowserView adds the current object (self.context) to the publishing queue for renaming.
    """
    def __call__(self, no_response=False, msg=None, *args, **kwargs):
        """
        Creates a "rename" job for the current item(s)
        @param args:    list of unnamed arguments
        @type args:     list
        @param kwargs:  dict of named keyword-arguments
        @type kwargs:   dict
        @return:        Redirect to object`s default view
        """
        self.logger = getLogger()
        # This View should not be executed at the PloneSiteRoot
        if IPloneSiteRoot.providedBy(self.context):
            raise Exception('Not allowed on PloneSiteRoot')
        # get username
        user = self.context.portal_membership.getAuthenticatedMember()
        username = user.getUserName()
        # create Job
        queue = Queue(self.context)
        queue.createJob('move', self.context, username, )
        self.logger.info('Created "%s" Job for "%s" at %s' % (
                'move',
                self.context.Title(),
                '/'.join(self.context.getPhysicalPath()),
        ))
        # status message
        if msg is None:
            msg = 'Object move/rename action has been added to the queue.'
        IStatusMessage(self.request).addStatusMessage(
                msg,
                type='info'
        )
        if not no_response:
            return self.request.RESPONSE.redirect('./view')



class DeleteObject(BrowserView):
    """
    Add a object to the queue with the action "delete".
    """

    def __call__(self, no_response=False, msg=None, *args, **kwargs):
        """
        Add the current context as delete-job to the queue, creates a status
        message to inform the user and returns to the default view.
        @param args:    list of unnamed arguments
        @type args:     list
        @param kwargs:  dict of named keyword-arguments
        @type kwargs:   dict
        @return:        Redirect to object`s default view
        """
        self.logger = getLogger()
        # This view should not be executed at the PloneSiteRoot
        if IPloneSiteRoot.providedBy(self.context):
            raise Exception('Not allowed on PloneSiteRoot')
        # get username
        user = self.context.portal_membership.getAuthenticatedMember()
        username = user.getUserName()
        # create Job
        queue = Queue(self.context)
        queue.createJob('delete', self.context, username)
        self.logger.info('Created "%s" Job for "%s" at %s' % (
                'delete',
                self.context.Title(),
                '/'.join(self.context.getPhysicalPath()),
        ))
        # status message
        if msg is None:
            msg = 'This object will be deleted at the remote sites.'
        IStatusMessage(self.request).addStatusMessage(
                msg,
                type='info'
        )
        if not no_response:
            return self.request.RESPONSE.redirect('./view')



class ExecuteQueue(BrowserView):
    """
    Executes the Queue and sends BATCH_SIZE amount of Jobs to the target realms.
    """

    def __call__(self, *args, **kwargs):
        """
        Handles logging purposes and calls execute() method.
        @param args:    list of unnamed arguments
        @type args:     list
        @param kwargs:  dict of named keyword-arguments
        @type kwargs:   dict
        @return:        Redirect to object`s default view
        """
        self.logger = getLogger()
        # register our own logging handler for returning logs afterwards
        logStream = StringIO()
        logHandler = logging.StreamHandler(logStream)
        self.logger.addHandler(logHandler)
        # be sure to remove the handler!
        try:
            # get config and queue
            self.config = Config(self.context)
            self.queue = Queue(self.context)
            # execute queue
            self.execute()
        except:
            self.logger.removeHandler(logHandler)
            # re-raise exception
            raise
        # get logs
        self.logger.removeHandler(logHandler)
        logStream.seek(0)
        log = logStream.read()
        del logStream
        del logHandler
        
        return log

    def getActiveRealms(self):
        """
        @return: a list of active Realms
        @rtype: list
        """
        if '_activeRealms' not in dir(self):
            self._activeRealms = [r for r in self.config.getRealms() if r.active]
        return self._activeRealms

    def execute(self):
        """
        Executes the jobs from the queue. Maximum amount of performed jobs can
        be set with the BATCH_SIZE global.
        @return: None
        """
        # jobCounter counts the amount of executed jobs
        jobCounter = 0
        jobs = self.queue.countJobs()
        self.logger.info('Executing Queue: %i of %i objects to %i realms' % (
                jobs>BATCH_SIZE and BATCH_SIZE or jobs,
                self.queue.countJobs(),
                len(self.getActiveRealms()),
        ))
        while self.queue.countJobs()>0 and (BATCH_SIZE<1 or jobCounter<BATCH_SIZE):
            # get job from queue
            job = self.queue.popJob()
            # execute job
            self.executeJob(job)
            # remove cache file from file system / delete job
            job.removeJob()
            jobCounter += 1
            
    def executeJob(self, job):
        """
        Executes a Job: sends the job to all available realms.
        @param job:     Job object to execute
        @type job:      Job
        """
        # get data from chache file
        state = None
        json = job.getData()
        self.logger.info('-' * 100)
        self.logger.info('executing "%s" on "%s" (at %s | UID %s)' % (
                job.action,
                job.objectTitle,
                job.objectPath,
                job.objectUID,
        ))
        self.logger.info('... request data length: %i' % len(json))
        for realm in self.getActiveRealms():
            self.logger.info('... to realm %s' % (
                    realm.url,
            ))
            # send data to each realm
            state = sendJsonToRealm(json, realm, 'publisher.receive')
            if isinstance(state, states.ErrorState):
                self.logger.error('... got result: %s' % state.toString())
            else:
                self.logger.info('... got result: %s' % state.toString())

        # fire AfterPushEvent
        obj = self.context.archetype_tool.getObject(job.objectUID)
        if state is not None:
            event.notify(AfterPushEvent(obj, state, job))


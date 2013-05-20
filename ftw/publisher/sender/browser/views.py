from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from StringIO import StringIO
from ZODB.POSException import ConflictError
from datetime import datetime
from ftw.publisher.core import states
from ftw.publisher.sender import getLogger, getErrorLogger
from ftw.publisher.sender import message_factory as _
from ftw.publisher.sender.events import AfterPushEvent, QueueExecutedEvent
from ftw.publisher.sender.events import BeforeQueueExecutionEvent
from ftw.publisher.sender.interfaces import IPathBlacklist, IConfig, IQueue
from ftw.publisher.sender.utils import add_transaction_aware_status_message
from ftw.publisher.sender.utils import sendJsonToRealm
from threading import RLock
from urllib2 import URLError
from zope import event
from zope.publisher.interfaces import Retry
import logging
import sys
import traceback
import transaction


"""
@var BATCH_SIZE:        Maximum amount of Jobs to be performed at one
ExecuteQueue call
"""
BATCH_SIZE = 0


class PublishObject(BrowserView):
    """This BrowserView adds the current object (self.context) to the
    publishing queue.

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
        # is the object blacklisted?
        if IPathBlacklist(self.context).is_blacklisted():
            self.logger.warning('Could not create push job for blacklisted '+\
                                    'object (%s at %s)' % (
                    self.context.Title(),
                    '/'.join(self.context.getPhysicalPath())))
            if not no_response:
                return self.request.RESPONSE.redirect('./view')
            return False

        # mle: now its possible to execite this view on plonesiteroot
        # This View should not be executed at the PloneSiteRoot
        #if IPloneSiteRoot.providedBy(self.context):
        #    raise Exception('Not allowed on PloneSiteRoot')
        # get username
        user = self.context.portal_membership.getAuthenticatedMember()
        username = user.getUserName()
        # create Job
        portal = self.context.portal_url.getPortalObject()
        queue = IQueue(portal)
        queue.createJob('push', self.context, username)
        self.logger.info('Created "%s" Job for "%s" at %s' % (
                'push',
                self.context.Title(),
                '/'.join(self.context.getPhysicalPath()),
                ))

        # status message
        if msg is None:
            msg = _(u'This object has been added to the queue.')
        IStatusMessage(self.request).addStatusMessage(
            msg,
            type='info'
            )
        if not no_response:
            return self.request.RESPONSE.redirect('./view')


class MoveObject(BrowserView):
    """This BrowserView adds the current object (self.context) to the
    publishing queue for renaming.

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
        # is the object blacklisted?
        if IPathBlacklist(self.context).is_blacklisted():
            self.logger.warning('Could not create move job for blacklisted '+\
                                    'object (%s at %s)' % (
                    self.context.Title(),
                    '/'.join(self.context.getPhysicalPath())))
            if not no_response:
                return self.request.RESPONSE.redirect('./view')
            return False

        # This View should not be executed at the PloneSiteRoot
        if IPloneSiteRoot.providedBy(self.context):
            raise Exception('Not allowed on PloneSiteRoot')
        # get username
        user = self.context.portal_membership.getAuthenticatedMember()
        username = user.getUserName()
        # create Job
        portal = self.context.portal_url.getPortalObject()
        queue = IQueue(portal)
        queue.createJob('move', self.context, username, )
        self.logger.info('Created "%s" Job for "%s" at %s' % (
                'move',
                self.context.Title(),
                '/'.join(self.context.getPhysicalPath()),
                ))
        # status message
        if msg is None:
            msg = _(u'Object move/rename action has been added to the queue.')
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
        # is the object blacklisted?
        if IPathBlacklist(self.context).is_blacklisted():
            self.logger.warning('Could not create delete job for blacklisted '
                                'object (%s at %s)' % (
                    self.context.Title(),
                    '/'.join(self.context.getPhysicalPath())))
            if not no_response:
                return self.request.RESPONSE.redirect('./view')
            return False

        # This view should not be executed at the PloneSiteRoot
        if IPloneSiteRoot.providedBy(self.context):
            raise Exception('Not allowed on PloneSiteRoot')
        # get username
        user = self.context.portal_membership.getAuthenticatedMember()
        username = user.getUserName()
        # create Job
        portal = self.context.portal_url.getPortalObject()
        queue = IQueue(portal)
        queue.createJob('delete', self.context, username)
        self.logger.info('Created "%s" Job for "%s" at %s' % (
                'delete',
                self.context.Title(),
                '/'.join(self.context.getPhysicalPath()),
                ))

        # status message
        if msg is None:
            msg = _(u'This object will be deleted at the remote sites.')
        add_transaction_aware_status_message(self.request, msg, type='info')

        if not no_response:
            return self.request.RESPONSE.redirect('./view')



class ExecuteQueue(BrowserView):
    """Executes the Queue and sends BATCH_SIZE amount of Jobs to the target
    realms.

    """

    def execute_single_job(self, job):
        """ Executes a single job without calling the view
        """
        self.logger = getLogger()
        self.error_logger = getErrorLogger()
        portal = self.context.portal_url.getPortalObject()
        self.config = IConfig(portal)
        self.queue = IQueue(portal)
        # remove job from queue
        if job in self.queue.getJobs():
            self.queue.removeJob(job)
        elif job in self.queue.get_executed_jobs():
            self.queue.remove_executed_job(job)
        # execute it
        self.executeJob(job)
        # move json file
        job.move_jsonfile_to(self.config.get_executed_folder())
        # add to executed list
        return self.queue.append_executed_job(job)

    def __call__(self, batchsize=None):
        """
        Handles logging purposes and calls execute() method.
        """
        if batchsize is None:
            batchsize = BATCH_SIZE
        self.batchsize = batchsize

        # get config and queue
        self.config = IConfig(self.context)
        portal = self.context.portal_url.getPortalObject()
        self.queue = IQueue(portal)
        event.notify(BeforeQueueExecutionEvent(portal, self.queue))
        # prepare logger
        self.logger = getLogger()
        self.error_logger = getErrorLogger()
        # is it allowed to publish?
        if not self.config.publishing_enabled():
            self.logger.warning('PUBLISHING IS DISABLED')
            return 'PUBLISHING IS DISABLED'

        if self.config.locking_enabled():
            self.logger.info('LOCKING IS ENABLED')
        else:
            self.logger.info('LOCKING IS DISABLED')

        # lock - check for locking flag
        if self.config.locking_enabled() and not self.get_lock_object().acquire(0):
            self.logger.info('Already publishing')
            return 'Already publishing'

        # register our own logging handler for returning logs afterwards
        logStream = StringIO()
        logHandler = logging.StreamHandler(logStream)
        self.logger.addHandler(logHandler)
        # be sure to remove the handler!
        try:
            # execute queue
            self.execute()
        except:
            self.logger.removeHandler(logHandler)
            if self.config.locking_enabled(): self.get_lock_object().release()
            # re-raise exception
            raise
        # get logs
        self.logger.removeHandler(logHandler)
        logStream.seek(0)
        log = logStream.read()
        del logStream
        del logHandler

        # unlock
        if self.config.locking_enabled(): self.get_lock_object().release()

        event.notify(QueueExecutedEvent(portal, log))
        return log

    def get_lock_object(self):
        if getattr(self.__class__, '_lock', None) == None:
            self.__class__._lock = RLock()
        return self.__class__._lock

    def getActiveRealms(self):
        """
        @return: a list of active Realms
        @rtype: list
        """
        if '_activeRealms' not in dir(self):
            self._activeRealms = [r for r in self.config.getRealms()
                                  if r.active]
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
                jobs>self.batchsize and self.batchsize or jobs,
                self.queue.countJobs(),
                len(self.getActiveRealms()),
                ))
        while self.queue.countJobs()>0 and (self.batchsize<1 or
                                            jobCounter<self.batchsize):
            jobCounter += 1
            # get job from queue
            job = self.queue.popJob()
            if not job.json_file_exists():
                continue
            try:
                # execute job
                self.executeJob(job)
            except (ConflictError, Retry):
                raise
            except URLError:
                raise
            except:
                # print the exception to the publisher error log
                exc = ''.join(traceback.format_exception(*sys.exc_info()))
                self.error_logger.error(exc)
                job.executed_exception = exc
            job.move_jsonfile_to(self.config.get_executed_folder())
            self.queue.append_executed_job(job)
            transaction.commit()

    def executeJob(self, job):
        """
        Executes a Job: sends the job to all available realms.
        @param job:     Job object to execute
        @type job:      Job
        """
        objTitle = job.objectTitle
        if isinstance(objTitle, unicode):
            objTitle = objTitle.encode('utf8')
        # is the object blacklisted?
        if IPathBlacklist(self.context).is_blacklisted(job.objectPath):
            self.logger.error('blacklisted: "%s" on "%s" (at %s | UID %s)' % (
                    job.action,
                    objTitle,
                    job.objectPath,
                    job.objectUID,
                    ))
            self.error_logger.error(
                'blacklisted: "%s" on "%s" (at %s | UID %s)' % (
                    job.action,
                    objTitle,
                    job.objectPath,
                    job.objectUID,
                    ))
            return False

        # get data from chache file
        state = None
        json = job.getData()
        self.logger.info('-' * 100)
        self.logger.info('executing "%s" on "%s" (at %s | UID %s)' % (
                job.action,
                objTitle,
                job.objectPath,
                job.objectUID,
                ))
        self.logger.info('... request data length: %i' % len(json))
        state_entries = {'date': datetime.now()}
        for realm in self.getActiveRealms():
            self.logger.info('... to realm %s' % (
                    realm.url,
                    ))
            # send data to each realm
            state = sendJsonToRealm(json, realm, 'publisher.receive')
            if isinstance(state, states.ErrorState):
                self.logger.error('... got result: %s' % state.toString())
                self.error_logger.error(
                    'executing "%s" on "%s" (at %s | UID %s)' % (
                        job.action,
                        objTitle,
                        job.objectPath,
                        job.objectUID,
                        ))
                self.error_logger.error('... got result: %s' %
                                        state.toString())
            else:
                self.logger.info('... got result: %s' % state.toString())
            state_entries[realm] = state
        job.executed_with_states(state_entries)

        # fire AfterPushEvent
        reference_catalog = getToolByName(self.context, 'reference_catalog')
        obj = reference_catalog.lookupObject(job.objectUID)
        if state is not None:
            event.notify(AfterPushEvent(obj, state, job))

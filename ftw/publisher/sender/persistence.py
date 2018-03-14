from AccessControl.SecurityInfo import ClassSecurityInformation
from Acquisition import aq_inner
from BTrees.IOBTree import IOBTree
from ftw.publisher.core import states
from ftw.publisher.sender import extractor
from ftw.publisher.sender import getLogger
from ftw.publisher.sender.interfaces import IConfig
from ftw.publisher.sender.interfaces import IOverriddenRealmRegistry
from ftw.publisher.sender.interfaces import IQueue
from ftw.publisher.sender.interfaces import IRealm
from ftw.publisher.sender.nojobs import publisher_jobs_are_disabled
from persistent import Persistent
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from plone.app.uuid.utils import uuidToObject
from plone.memoize import instance
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Transience.Transience import Increaser
from zope import interface, component
from zope.annotation.interfaces import IAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable
import os
import time
import transaction
import zc.queue

_marker = object()


ANNOTATIONS_PATH_BLACKLIST_KEY = 'publisher-path-blacklist'


class Config(object):
    """
    The Config object is registered via zcml as adapter. It stores the
    configured realms
    """

    interface.implements(IConfig)
    component.adapts(IPloneSiteRoot)
    security = ClassSecurityInformation()

    def __init__(self, context):
        """
        Constructor: load the annotations, which are stored on the
        plone site.

        @param context:     any context
        @type context:      Plone object
        """
        # get plone site
        self.context = aq_inner(context.portal_url.getPortalObject())
        # get annotations for plone site
        self.annotations = IAnnotations(self.context)

    security.declarePublic('is_update_realms_possible')
    def is_update_realms_possible(self):
        return self._get_realm_registry() is None

    security.declarePrivate('getRealms')
    def getRealms(self):
        """
        Returns a PersistentList of Realm objects
        @return:    Realm objects
        @rtype:     PersistentList
        """

        registry = self._get_realm_registry()
        if registry:
            return tuple(registry.realms)

        else:
            return self.annotations.get('publisher-realms', PersistentList())

    security.declarePrivate('_setRealms')
    def _setRealms(self, list):
        """
        Stores a PersistentList of Realm objects
        @param list:    Realm objects
        @type list:     PersistentList
        @return:        None
        """
        if not self.is_update_realms_possible():
            raise AttributeError(
                'The realm registry is overridden and not mutatable.')

        if not isinstance(list, PersistentList):
            raise TypeError('Excpected PersistentList')
        self.annotations['publisher-realms'] = list

    security.declarePrivate('appendRealm')
    def appendRealm(self, realm):
        """
        Appends a Realm to the realm list
        @param realm:   Realm object
        @type realm:    Realm
        @return:        None
        """

        if not IRealm.providedBy(realm):
            raise TypeError('Excpected Realm object')

        list = self.getRealms()
        list.append(realm)
        self._setRealms(list)

    security.declarePrivate('removeRealm')
    def removeRealm(self, realm):
        """
        Removes a Realm from the realm list
        @param realm:   Realm object
        @type realm:    Realm
        @return:        None
        """
        if not isinstance(realm, Realm):
            raise TypeError('Excpected Realm object')
        list = self.getRealms()
        list.remove(realm)
        self._setRealms(list)

    security.declarePrivate('_get_realm_registry')
    def _get_realm_registry(self):
        return component.queryUtility(IOverriddenRealmRegistry)

    security.declarePrivate('getDataFolder')
    @instance.memoize
    def getDataFolder(self):
        """
        Returns the path to the data folder. If it does not exist, it will
        be created.
        @return:        absolute file system path
        @rtype:         string
        """
        path = os.path.join('/'.join(
                os.environ['CLIENT_HOME'].split('/')[:-2] + ['var',
                                                             'publisher']))
        # create if not existing
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    security.declarePrivate('get_executed_folder')
    def get_executed_folder(self):
        executed_folder = os.path.join(self.getDataFolder(), 'executed')
        if not os.path.exists(executed_folder):
            os.makedirs(executed_folder)
        return executed_folder

    security.declarePrivate('getPathBlacklist')
    def getPathBlacklist(self):
        """
        Returns a list of paths which are blacklistet and are not
        touched by the publisher.
        """
        blacklist = self.annotations.get(ANNOTATIONS_PATH_BLACKLIST_KEY,
                                         _marker)
        if blacklist is _marker:
            blacklist = PersistentList()
            self.setPathBlacklist(blacklist)
        return blacklist

    security.declarePrivate('setPathBlacklist')
    def setPathBlacklist(self, blacklist):
        """
        Sets the path blacklist
        """
        if not isinstance(blacklist, PersistentList):
            raise ValueError('Expected PersistentList, got %s' %
                             repr(blacklist))
        self.annotations[ANNOTATIONS_PATH_BLACKLIST_KEY] = blacklist

    security.declarePrivate('appendPathToBlacklist')
    def appendPathToBlacklist(self, path):
        """
        Appends a path to the blacklist, if it isnt already blacklisted...
        """
        if type(path) not in (str, unicode):
            raise ValueError('Expected string, got %s' % repr(path))
        path = path.strip()
        blacklist = self.getPathBlacklist()
        if path not in blacklist:
            blacklist.append(path)
            self.setPathBlacklist(blacklist)

    security.declarePrivate('removePathFromBlacklist')
    def removePathFromBlacklist(self, path):
        """
        Removes a path from the path blacklist
        """
        if type(path) not in (str, unicode):
            raise ValueError('Expected string, got %s' % repr(path))
        path = path.strip()
        blacklist = self.getPathBlacklist()
        if path in blacklist:
            blacklist.remove(path)
            return True
        else:
            return False

    security.declarePrivate('publishing_enabled')
    def publishing_enabled(self):
        """ Returns True if the publishing is enable at the moment
        """
        return self.annotations.get('publisher-publishing-enabled', True)

    security.declarePrivate('set_publishing_enabled')
    def set_publishing_enabled(self, enabled):
        self.annotations['publisher-publishing-enabled'] = bool(enabled)

    security.declarePrivate('locking_enabled')
    def locking_enabled(self):
        """ Returns True if locking is enabled, default is True
        """
        return self.annotations.get('publisher-locking-enabled', True)

    security.declarePrivate('set_locking_enabled')
    def set_locking_enabled(self, enabled):
        if not isinstance(enabled, bool):
            enabled = bool(enabled == '1')
        self.annotations['publisher-locking-enabled'] = bool(enabled)

    security.declarePrivate('get_ignored_fields')
    def get_ignored_fields(self):
        """ Returns a PersistentDict if there are no ignored-fields yet.
        """
        return self.annotations.get('publisher-ignored-fields',
                                    PersistentDict())

    security.declarePrivate('set_ignored_fields')
    def set_ignored_fields(self, dictionary):
        """ Sets the publisher-ignored-fields.
            Example:
            {'FormSaveDataAdapter': ['SavedFormInput',]}
        """
        self.annotations['publisher-ignored-fields'] = dictionary


class Queue(object):
    """
    The Queue adapter stores a list of Jobs to process.
    """

    interface.implements(IQueue)
    component.adapter(IPloneSiteRoot)
    security = ClassSecurityInformation()

    def __init__(self, context):
        """
        Constructor: load the annotations, which are stored on the
        plone site.

        @param context:     any context
        @type context:      Plone object
        """
        self.context = aq_inner(context.portal_url.getPortalObject())
        self.annotations = IAnnotations(self.context)
        self.logger = getLogger()

    security.declarePrivate('_get_jobs_queue')
    def _get_jobs_queue(self):
        if 'publisher-queue' not in self.annotations:
            self.annotations['publisher-queue'] = zc.queue.Queue()
        return self.annotations['publisher-queue']

    security.declarePrivate('_get_worker_queue')
    def _get_worker_queue(self):
        if 'worker-queue' not in self.annotations:
            self.annotations['worker-queue'] = zc.queue.Queue()
        return self.annotations['worker-queue']

    security.declarePrivate('get_worker_queue')
    def get_worker_queue(self):
        return self._get_worker_queue()

    security.declarePrivate('move_to_worker_queue')
    def move_to_worker_queue(self):
        job_queue = self._get_jobs_queue()
        worker_queue = self._get_worker_queue()

        # The worker queue threshold should be small
        # because we want the move-loop to terminate fast
        # but it should be enough big to use one cronjob
        # iteration, which is usually 1-2 minutes.
        worker_queue_threshold = 1000

        if len(worker_queue) > worker_queue_threshold:
            return

        if not len(job_queue):
            return

        while len(job_queue) > 0 and len(worker_queue) < worker_queue_threshold:
            try:
                if os.path.getsize(self.nextJob().dataFile) == 0:
                    # ABORT
                    self.logger.warning(
                        'Aborting move job to worker queue because data file'
                        ' is empty and async extractor may not be finished.')
                    self.logger.info(
                        'Worker queue: {} / {}'.format(len(worker_queue), len(job_queue)))
                    transaction.commit()
                    return
            except OSError:
                pass

            worker_queue.put(job_queue.pull())

        self.logger.info(
            'Worker queue: {} / {}'.format(len(worker_queue), len(job_queue)))
        transaction.commit()

    security.declarePrivate('getJobs')
    def getJobs(self):
        """
        Returns a list of Job objects
        @return:        job-objects
        @rtype:         list
        """

        # zc.queue.Queue does not support + operator
        return tuple(self._get_worker_queue()) + tuple(self._get_jobs_queue())

    security.declarePrivate('clearJobs')
    def clearJobs(self):
        """
        Remove all jobs from the queue.
        """
        jobs_queue = self._get_jobs_queue()
        worker_queue  = self._get_worker_queue()
        map(worker_queue.pull, len(worker_queue) * [0])
        map(jobs_queue.pull, len(jobs_queue) * [0])

    security.declarePrivate('appendJob')
    def appendJob(self, job):
        """
        Appends a Job to the queue
        @param job:     Job object
        @type:          Job
        @return:        None
        """
        if publisher_jobs_are_disabled():
            return None

        if not isinstance(job, Job):
            raise TypeError('Excpected Job object')

        self._get_jobs_queue().put(job)

    security.declarePrivate('createJob')
    def createJob(self, *args, **kwargs):
        """
        Creates a new Job object, adds it to the queue
        and returns it.
        Arguments are redirected to the Job-Constructor.
        @return:    Job object
        @rtype:     Job
        """
        if publisher_jobs_are_disabled():
            return None

        job = Job(*args, **kwargs)
        self.appendJob(job)
        return job

    security.declarePrivate('removeJob')
    def removeJob(self, job):
        """
        Removes a Job from the queue
        @param job:     Job object
        @type job:      Job
        @return:        None
        """
        if not isinstance(job, Job):
            raise TypeError('Excpected Job object')

        job_queue = self._get_jobs_queue()
        worker_queue = self._get_worker_queue()

        if job in job_queue:
            job_queue.pull(tuple(job_queue).index(job))
        else:
            worker_queue.pull(tuple(worker_queue).index(job))

    security.declarePrivate('countJobs')
    def countJobs(self):
        """
        Returns the amount of jobs in the queue.
        Used in combination with popJob()
        @return:        Amount of jobs in the queue
        @rtype:         int
        """
        return len(self.getJobs())

    security.declarePrivate('nextJob')
    def nextJob(self):
        """
        Returns the next job to be executed but does not pop it.
        This should only be used when the job is NOT executed but
        when we need to make checks first in order to decide whether
        to execute it or not.
        @return:        Oldest Job object
        @rtype:         Job
        """
        return self._get_jobs_queue()[0]

    security.declarePrivate('popJob')
    def popJob(self):
        """
        Returns the oldest Job from the queue. The Job will be
        removed from the queue immediately!
        @return:        Oldest Job object
        @rtype:         Job
        """
        return self.get_worker_queue().pull()

    security.declarePrivate('_get_executed_jobs_storage')
    def _get_executed_jobs_storage(self):
        """Returns the IOBTree storage object for executed jobs.
        """
        if self.annotations.get('publisher-executed', _marker) == _marker:
            self.annotations['publisher-executed'] = IOBTree()
        return self.annotations['publisher-executed']

    security.declarePrivate('_generate_next_executed_jobs_storage_key')
    def _generate_next_executed_jobs_storage_key(self):
        """Returns a transaction-safe auto-increment value
        http://pyyou.wordpress.com/2009/12/09/how-to-add-a-counter-without-conflict-error-in-zope

        """
        ann_key = 'publisher-executed-key-auto-increment'
        # get the increaser stored in the annotations
        if ann_key not in self.annotations.keys():
            self.annotations[ann_key] = Increaser(0)
        inc = self.annotations[ann_key]
        # increase by one
        inc.set(inc() + 1)
        # check the current max key
        try:
            current_max_key = self._get_executed_jobs_storage().maxKey()
        except ValueError:
            # the storage is empty, start with 0
            current_max_key = 0
        while current_max_key >= inc():
            inc.set(inc() + 1)
        # set and return the new value
        self.annotations[ann_key] = inc
        return inc()

    security.declarePrivate('get_executed_jobs')
    def get_executed_jobs(self, start=0, end=None):
        """Returns a iterator of executed jobs. You can make a batch by
        providing a range with `start` and `end` parameters. The start and
        end parameters represent the index number in the storage, so we can
        expect that the length of the iterate is `end - start`, if there
        are enough objects in the storage.
        A key / value pair is returned.

        """
        data = self._get_executed_jobs_storage()
        if start == 0 and end == None:
            # return all
            return data.iteritems()

        elif start > end or start == end:
            return ()

        else:
            # make a batch without touching unused values
            # the iteritems() method wants the min-key and the
            # max-key which is used as filter then. So we need to map
            # our `start` and `end` (which is the index) to the max-
            # and min-*keys*
            keys = data.keys()[start:end]
            return data.iteritems(min(keys), max(keys))

    security.declarePrivate('get_executed_jobs_length')
    def get_executed_jobs_length(self):
        """Returns the amount of currently stored executed jobs.
        """
        return len(self._get_executed_jobs_storage().keys())

    security.declarePrivate('append_executed_job')
    def append_executed_job(self, job):
        """Add another
        """
        data = self._get_executed_jobs_storage()
        key = self._generate_next_executed_jobs_storage_key()
        data.insert(key, job)
        return key

    security.declarePrivate('remove_executed_job')
    def remove_executed_job(self, key, default=None):
        """Removes the job with the `key` from the executed jobs storage.
        """
        return self._get_executed_jobs_storage().pop(key, default)

    security.declarePrivate('get_executed_job_by_key')
    def get_executed_job_by_key(self, key):
        """Returns a executed job according to its internal storage key
        """
        return self._get_executed_jobs_storage()[key]

    security.declarePrivate('clear_executed_jobs')
    def clear_executed_jobs(self):
        """Removes all jobs from the executed jobs storage.
        """
        for key, job in self.get_executed_jobs():
            job.removeJob()
        self._get_executed_jobs_storage().clear()

    security.declarePrivate('remove_executed_jobs_older_than')
    def remove_executed_jobs_older_than(self, time):
        """Removes all executed jobs which are older
        than `time` (datetime instance).

        """

        def _get_date_of_job(job):
            """Returns the date of the newest execution of this job or None.
            """
            if getattr(job, 'executed_list', None) == None:
                return None
            elif len(job.executed_list) == 0:
                return None
            else:
                return job.executed_list[-1]['date']

        # start end
        data = self._get_executed_jobs_storage()
        for key in tuple(data.keys()):
            job = data.get(key)
            date = _get_date_of_job(job)
            if not date:
                continue
            elif date < time:
                self.remove_executed_job(key)
                job.removeJob()
            else:
                break

    security.declarePrivate('remove_jobs_by_filter')
    def remove_jobs_by_filter(self, filter_method):
        """Removs jobs by a filter method.
        The `filter_method` gets the `key` and the `job` as parameters.
        If it returns `True` the job os deleted.

        """
        for key, job in tuple(self.get_executed_jobs()):
            if filter_method(key, job):
                self.remove_executed_job(key)
                job.removeJob()


class Job(Persistent):
    """
    A Job object contains action, object and the user who triggered the job.
    It is stored in the Queue and is executed asynchronous.
    """

    security = ClassSecurityInformation()

    def __init__(self, action, object, username, additional_data=None):
        """
        Constructor: sets the given arguments.
        @param action:      action type [push|delete]
        @type action:       string
        @param object:      plone object to run job on
        @type object:       Plone object
        @param username:    Name of the user which performed the action
        @type username:     string
        """
        super(Persistent, self).__init__()
        self.is_root = IPloneSiteRoot.providedBy(object)
        self.action = action
        self.username = username
        self.objectPath = '/'.join(object.getPhysicalPath())
        # store the path as uid if we are on a plone root
        self.objectUID = self.is_root and self.objectPath or object.UID()
        putils = getToolByName(object, 'plone_utils')
        self.objectTitle = putils.pretty_title_or_id(object)
        self.additional_data = PersistentDict(additional_data or {})
        self._extractData(object)

    security.declarePrivate('_extractData')
    def _extractData(self, object):
        """
        Extracts the data from the object and stores the JSON string
        in a cache-file.
        @param object:      plone object to run job on
        @type object:       Plone object
        """
        # create new data file
        dir = Config(object).getDataFolder()
        i = 1
        file = None
        while not file:
            filename = '%s.%s.%s.json' % (
                # on plone root we use the path as uid, now we have to replace
                # the '/' by '_' to provide a good name
                self.objectUID.replace('/', '_'),
                time.strftime('%Y%m%d-%H%M%S'),
                str(i).rjust(3, '0'),
                )
            file = os.path.join(dir, filename)
            if os.path.exists(file):
                file = None

        def direct_extract(filepath, obj, action):
            f = open(filepath, 'w')
            # extract data
            data = extractor.Extractor()(obj, action, self.additional_data)
            # write data
            f.write(data)
            f.close()

        if os.environ.get('PUBLISHER_TASKQUEUE'):
            open(file, 'w').close()  # touch
            from ftw.publisher.sender.taskqueue import queue

            if self.action not in ['delete', 'move']:
                queue.enqueue_deferred_extraction(object, self.action, file,
                                                  self.additional_data)
            else:
                direct_extract(file, object, self.action)

        else:
            direct_extract(file, object, self.action)

        self.dataFile = file

    security.declarePrivate('getSize')
    def getSize(self):
        try:
            return len(self.getData())
        except IOError:
            return -1

    security.declarePrivate('getData')
    def getData(self):
        """
        Loads the JSON-data from the cache file and returns
        the JSON-string
        @return:    JSON data
        @rtype:     string
        """
        f = open(self.dataFile)
        data = f.read()
        f.close()
        return data

    security.declarePrivate('removeJob')
    def removeJob(self):
        """
        Removes the cache file for this job from the file system
        """
        if os.path.exists(self.dataFile):
            os.remove(self.dataFile)

    security.declarePrivate('json_file_exists')
    def json_file_exists(self):
        return os.path.exists(self.dataFile)

    security.declarePrivate('move_jsonfile_to')
    def move_jsonfile_to(self, dir):
        oridir, oname = os.path.split(self.dataFile)
        obase = '.'.join(oname.split('.')[:-1])
        oext = oname.split('.')[-1]
        i = 1
        path = os.path.join(dir, oname)
        # find new unused name
        while os.path.exists(path):
            i += 1
            path = os.path.join(dir, '%s.%i.%s' % (
                    obase,
                    i,
                    oext))
        # move it
        os.rename(self.dataFile, path)
        self.dataFile = path

    security.declarePrivate('getObject')
    def getObject(self, context):
        """
        Returns the object with UID stored in this Job. This method
        requires any context for getting the reference_catalog.
        @param context:     Any Plone object
        @type context:      Plone Object
        @return:            Context object of this Job
        @rtype:             Plone object
        """
        return self.is_root and context.portal_url.getPortalObject() or \
            uuidToObject(self.objectUID)

    security.declarePrivate('executed_with_states')
    def executed_with_states(self, entries):
        """ entries: {'date': <datetime ...>, <Realm1 ..>: <State1 ..>,
        <Realm2 ..>: <State2 ..>}
        """
        if not getattr(self, 'executed_list', None):
            self.executed_list = PersistentList()
        self.executed_list.append(entries)

    security.declarePrivate('get_latest_executed_entry')
    def get_latest_executed_entry(self):
        entries_list = getattr(self, 'executed_list', ())
        # get the last entries
        if len(entries_list) == 0:
            return None
        last_entries = entries_list[-1]
        # then return the first "bad" entry or the last
        for state in last_entries.values():
            if isinstance(state, states.ErrorState):
                return state
        return state

    security.declarePrivate('get_filename')
    def get_filename(self):
        return os.path.split(self.dataFile)[1]


class Realm(Persistent):
    """
    A Realm object provides information about a target plone instance
    (receiver) which should have installed ftw.publisher.receiver.
    It stores and provides information such as URL or credentials.
    URL+username should be unique!
    """

    interface.implements(IAttributeAnnotatable, IRealm)
    security = ClassSecurityInformation()

    active = 0
    url = ''
    username = ''
    password = ''

    def __init__(self, active, url, username, password):
        """
        Constructor: stores the given arguments in the object
        @param active:      Is this realm active?
        @type active:       boolean or int
        @param url:         URL to the plone site of the target realm
        @type url:          string
        @param username:    Username to login on target realm
        @type username:     string
        @param password:    Password of the User with **username**
        @type password:     string
        """
        self.active = active and 1 or 0
        self.url = url
        self.username = username
        self.password = password

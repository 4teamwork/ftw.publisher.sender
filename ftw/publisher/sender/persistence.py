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

# Python imports
import os
import time

# Zope imports
from Acquisition import aq_inner
from persistent import Persistent
from persistent.list import PersistentList
from zope import interface, component
from zope.annotation.interfaces import IAnnotations
from zope.app.annotation.interfaces import IAttributeAnnotatable

# Plone imports
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot

# publisher imports
from interfaces import IConfig, IQueue
from ftw.publisher.sender import extractor

class Config(object):
    """
    The Config object is registered via zcml as adapter. It stores the
    configured realms
    """
    interface.implements(IConfig)
    component.adapts(IPloneSiteRoot)

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

    def getRealms(self):
        """
        Returns a PersistentList of Realm objects
        @return:    Realm objects
        @rtype:     PersistentList
        """
        return self.annotations.get('publisher-realms', PersistentList())

    def _setRealms(self, list):
        """
        Stores a PersistentList of Realm objects
        @param list:    Realm objects
        @type list:     PersistentList
        @return:        None
        """
        if not isinstance(list, PersistentList):
            raise TypeError('Excpected PersistentList')
        self.annotations['publisher-realms'] = list

    def appendRealm(self, realm):
        """
        Appends a Realm to the realm list
        @param realm:   Realm object
        @type realm:    Realm
        @return:        None
        """
        if not isinstance(realm, Realm):
            raise TypeError('Excpected Realm object')
        list = self.getRealms()
        list.append(realm)
        self._setRealms(list)

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

    def getDataFolder(self):
        """
        Returns the path to the data folder. If it does not exist, it will
        be created.
        @return:        absolute file system path
        @rtype:         string
        """
        path = self.annotations.get('publisher-dataFolder', None)
        if not path:
            path = os.path.join(os.environ['CLIENT_HOME'], '..',
                                'var','publisher')
            self.setDataFolder(path)
        # create if not existing
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    def setDataFolder(self, path):
        """
        Sets the data folder path
        @param path:    absoliute path to the data folder
        @type path:     string
        @return:        None
        """
        self.annotations['publisher-dataFolder'] = path

class Queue(object):
    """
    The Queue adapter stores a list of Jobs to process.
    """
    interface.implements(IQueue)
    component.adapter(IPloneSiteRoot)

    def __init__(self, context):
        """
        Constructor: load the annotations, which are stored on the
        plone site.

        @param context:     any context
        @type context:      Plone object
        """
        self.context = aq_inner(context.portal_url.getPortalObject())
        self.annotations = IAnnotations(self.context)

    def getJobs(self):
        """
        Returns a PersistentList of Job objects
        @return:        job-objects
        @rtype:         PersistentList
        """
        return self.annotations.get('publisher-queue', PersistentList())

    def _setJobs(self, list):
        """
        Stores a PersistentList of Job objects
        @param list:    list of jobs
        @type list:     PersistentList
        @return:        None
        """
        if not isinstance(list, PersistentList):
            raise TypeError('Excpected PersistentList')
        self.annotations['publisher-queue'] = list

    def appendJob(self, job):
        """
        Appends a Job to the queue
        @param job:     Job object
        @type:          Job
        @return:        None
        """
        if not isinstance(job, Job):
            raise TypeError('Excpected Job object')
        list = self.getJobs()
        list.append(job)
        self._setJobs(list)

    def createJob(self, *args, **kwargs):
        """
        Creates a new Job object, adds it to the queue
        and returns it.
        Arguments are redirected to the Job-Constructor.
        @return:    Job object
        @rtype:     Job
        """
        job = Job(*args, **kwargs)
        self.appendJob(job)
        return job

    def removeJob(self, job):
        """
        Removes a Job from the queue
        @param job:     Job object
        @type job:      Job
        @return:        None
        """
        if not isinstance(job, Job):
            raise TypeError('Excpected Job object')
        list = self.getJobs()
        list.remove(job)
        self._setJobs(list)

    def countJobs(self):
        """
        Returns the amount of jobs in the queue.
        Used in combination with popJob()
        @return:        Amount of jobs in the queue
        @rtype:         int
        """
        return len(self.getJobs())

    def popJob(self):
        """
        Returns the oldest Job from the queue. The Job will be
        removed from the queue immediately!
        @return:        Oldest Job object
        @rtype:         Job
        """
        return self.getJobs().pop(0)


class Job(Persistent):
    """
    A Job object contains action, object and the user who triggered the job.
    It is stored in the Queue and is executed asynchronous.
    """

    def __init__(self, action, object, username):
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
        self.objectTitle = object.Title()
        self._extractData(object)

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
                self.objectUID.replace('/','_'), # on plone root we have we use the path as uid, now we habe to replace the '/' by '_' to provide a good name
                time.strftime('%Y%m%d-%H%M%S'),
                str(i).rjust(3, '0')
            )
            file = os.path.join(dir, filename)
            if os.path.exists(file):
                file = None
        f = open(file, 'w')
        # extract data
        data = extractor.Extractor()(object, self.action)
        # write data
        f.write(data)
        f.close()
        self.dataFile = file

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

    def removeJob(self):
        """
        Removes the cache file for this job from the file system
        """
        os.remove(self.dataFile)

    def getObject(self, context):
        """
        Returns the object with UID stored in this Job. This method
        requires any context for getting the reference_catalog.
        @param context:     Any Plone object
        @type context:      Plone Object
        @return:            Context object of this Job
        @rtype:             Plone object
        """
        reference_tool = getToolByName(context, 'reference_catalog')
        return self.is_root and context.portal_url.getPortalObject() or reference_tool.lookupObject(self.objectUID)


class Realm(Persistent):
    """
    A Realm object provides information about a target plone instance (receiver)
    which should have installed ftw.publisher.receiver.
    It stores and provides information such as URL or credentials.
    URL+username should be unique!
    """
    interface.implements(IAttributeAnnotatable)

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
        @param username:    Username of the user to publish data with on this realm
        @type username:     string
        @param password:    Password of the User with **username**
        @type password:     string
        """
        self.active = active and 1 or 0
        self.url = url
        self.username = username
        self.password = password


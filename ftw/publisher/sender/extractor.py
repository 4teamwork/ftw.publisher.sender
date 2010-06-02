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

# global imports
import simplejson

# zope imports
from zope.component import getAdapters

#ftw.publisher.core imports
from ftw.publisher.core.interfaces import IDataCollector
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zExceptions import NotFound

class Extractor(object):
    """
    The Extractor module is used for extracting the data from a Object and
    pack it with json.
    """

    def __call__(self, object, action):
        """
        Extracts the required data (action dependent) from a object for
        creating a Job.
        @param object:      Plone Object to export data from
        @param action:      Action to perform [push|delete]
        @type action:       string
        @return:            data (json "encoded")
        @rtype:             string
        """
        self.object = object
        self.is_root = IPloneSiteRoot.providedBy(self.object)
        data = {}
        if action not in ['delete', 'move']:
            adapters = getAdapters((self.object,),IDataCollector)
            for name,adapter in adapters:
                data[name] = adapter.getData()
        # gets the metadata, we dont use an adapter in this case,
        # cause metdata is the most important data-set we need
        data['metadata'] = self.getMetadata(action)

        if action == 'move':
            #read out data from event_information attr
            move_data = getattr(self.object,'event_information', None)
            #make data convertable and shrink amount of data (replace objects by path)
            del move_data['object']
            move_data['newParent'] = '/'.join(move_data['newParent'].getPhysicalPath())
            move_data['oldParent'] = '/'.join(move_data['oldParent'].getPhysicalPath())
            move_data['newTitle'] = self.object.Title().decode('utf-8')
            data['move'] = move_data
            # finally remove event_information from object
            delattr(self.object, 'event_information')

        # convert to json
        jsondata = self.convertToJson(data)
        return jsondata


    def getMetadata(self, action):
        """
        Returns a dictionary with metadata about this object. It contains also the action.
        @param action:  publishing action [push|delete]
        @type action:   string
        @return:        metadata dictionary
        @rtype:         dict
        """
        # get object positions
        positions = {}
        if not self.is_root:
            parent = self.object.aq_inner.aq_parent
            for obj_id in parent.objectIds():
                try:
                    positions[obj_id] = parent.getObjectPosition(obj_id)
                except NotFound:
                    # catch notfound, some zope objects (ex. syndication_information of a topic)
                    # has no getObjectPosition
                    pass
                    
        # create metadata dict
        uid = self.is_root and self.getRelativePath() or self.object.UID()
        try:
            wf_info = self.object.portal_workflow.getInfoFor(self.object, 'review_state')
        except Exception:
            wf_info = ''
        # get schema path
        if self.is_root:
            schema_path = None
        else:
            schema_path = '.'.join((self.object.__module__,
                                    self.object.__class__.__name__,
                                    'schema'))
        data = {
            'UID' : uid,
            'id'  : self.object.id,
            'portal_type' : self.object.portal_type,
            'action' : action,
            'physicalPath' : self.getRelativePath(),
            'sibling_positions' : positions,
            'review_state' : wf_info,
            'schema_path': schema_path,
            }
        return data



    def getRelativePath(self):
        """
        Returns the relative path (relative to plone site) to the current context object.
        @return:    relative path
        @rtype:     string
        """
        path = '/'.join(self.object.getPhysicalPath())
        portalPath = '/'.join(self.object.portal_url.getPortalObject().getPhysicalPath())
        if not path.startswith(portalPath):
            raise TypeError('Expected object to be in a portal object -.-')
        relative_path = path[len(portalPath):]
        if relative_path == '':
            return '/'
        return relative_path

    def convertToJson(self, data):
        """
        Converts a dictionary to a JSON-string
        @param data:    data dictionary
        @type data:     dict
        @return:        JSON
        @rtype:         string
        """
        return simplejson.dumps(data, sort_keys=True)


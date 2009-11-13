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
import base64

# zope imports
from zope.component import getAdapters

#ftw.publisher.core imports
from ftw.publisher.core.interfaces import IDataCollector

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
        data = {}
        if action!='delete':
            adapters = getAdapters((self.object,),IDataCollector)
            for name,adapter in adapters:
                data[name] = adapter.getData()
        # gets the metadata, we dont use an adapter in this case, 
        # cause metdata is the most important data-set we need 
        data['metadata'] = self.getMetadata(action)
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
        parent = self.object.aq_inner.aq_parent
        # get object positions
        positions = {}
        for obj_id in parent.objectIds():
            positions[obj_id] = parent.getObjectPosition(obj_id)
        # create metadata dict
        data = {
            'UID' : self.object.UID(),
            'id'  : self.object.id,
            'portal_type' : self.object.portal_type,
            'action' : action,
            'physicalPath' : self.getRelativePath(),
            'sibling_positions' : positions,
            'review_state' : self.object.portal_workflow.getInfoFor(self.object, 'review_state')
            
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
        return path[len(portalPath):]

    def convertToJson(self, data):
        """
        Converts a dictionary to a JSON-string
        @param data:    data dictionary
        @type data:     dict
        @return:        JSON
        @rtype:         string
        """
        return simplejson.dumps(data, sort_keys=True)


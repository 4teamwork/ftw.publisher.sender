from AccessControl.SecurityInfo import ClassSecurityInformation
from Products.CMFPlone.interfaces import IPloneSiteRoot
from ZODB.POSException import ConflictError
from ftw.publisher.core.interfaces import IDataCollector
from ftw.publisher.core.utils import decode_for_json
from ftw.publisher.sender.interfaces import IConfig
from zExceptions import NotFound
from zope.component import getAdapters
from zope.publisher.interfaces import Retry
import json


class Extractor(object):
    """
    The Extractor module is used for extracting the data from a Object and
    pack it with json.
    """

    security = ClassSecurityInformation()

    security.declarePrivate('__call__')
    def __call__(self, object, action, additional_data):
        """
        Extracts the required data (action dependent) from a object for
        creating a Job.
        @param object:      Plone Object to export data from
        @param action:      Action to perform [push|delete]
        @type action:       string
        @param additional_data: Additional infos.
        @type additional_data: dict
        @return:            data (json "encoded")
        @rtype:             string
        """
        self.object = object
        self.is_root = IPloneSiteRoot.providedBy(self.object)
        data = {}

        if action not in ['delete', 'move']:
            adapters = sorted(getAdapters((self.object, ), IDataCollector))
            for name, adapter in adapters:
                data[name] = adapter.getData()
        # gets the metadata, we dont use an adapter in this case,
        # cause metdata is the most important data-set we need
        data['metadata'] = self.getMetadata(action)

        # remove ignored fields
        portal = self.object.portal_url.getPortalObject()
        config = IConfig(portal)
        ignore = config.get_ignored_fields()
        for field_to_ignore in ignore.get(data['metadata']['portal_type'], ()):
            # AT:
            data.get('field_data_adapter', {}).pop(field_to_ignore, None)
            # DX:
            for schemata in data.get('dx_field_data_adapter', {}).values():
                schemata.pop(field_to_ignore, None)

        if action == 'move':
            data['move'] = additional_data['move_data']

        # convert to json
        jsondata = self.convertToJson(data)
        return jsondata

    security.declarePrivate('getMetadata')
    def getMetadata(self, action):
        """
        Returns a dictionary with metadata about this object. It contains also
        the action.
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
                    # catch notfound, some zope objects
                    # (ex. syndication_information of a topic)
                    # has no getObjectPosition
                    pass

        # create metadata dict
        uid = self.is_root and self.getRelativePath() or self.object.UID()
        try:
            wf_info = self.object.portal_workflow.getInfoFor(
                self.object, 'review_state')
        except (ConflictError, Retry):
            raise
        except Exception:
            wf_info = ''
        try:
            modifiedDate = str(self.object.modified())
        except AttributeError:
            modifiedDate = None
        data = {
            'UID': uid,
            'id': self.object.id,
            'portal_type': self.object.portal_type,
            'action': action,
            'physicalPath': self.getRelativePath(),
            'sibling_positions': positions,
            'review_state': wf_info,
            'modified': modifiedDate,
            }
        return data

    security.declarePrivate('getRelativePath')
    def getRelativePath(self):
        """
        Returns the relative path (relative to plone site) to the current
        context object.
        @return:    relative path
        @rtype:     string
        """
        path = '/'.join(self.object.getPhysicalPath())
        portalPath = '/'.join(
            self.object.portal_url.getPortalObject().getPhysicalPath())
        if not path.startswith(portalPath):
            raise TypeError('Expected object to be in a portal object -.-')
        relative_path = path[len(portalPath):]
        if relative_path == '':
            return '/'
        return relative_path

    security.declarePrivate('convertToJson')
    def convertToJson(self, data):
        """
        Converts a dictionary to a JSON-string
        @param data:    data dictionary
        @type data:     dict
        @return:        JSON
        @rtype:         string
        """
        data = decode_for_json(data)

        return json.dumps(data, sort_keys=True)

from AccessControl.SecurityInfo import ClassSecurityInformation
from Products.ZCatalog import CatalogBrains
from ftw.publisher.sender.interfaces import IPathBlacklist, IConfig
from zope.interface import implements


class PathBlacklist(object):
    """ The `PathBlacklist` adapter knows if the adapted context or any other context / path
    is blacklisted.
    """

    implements(IPathBlacklist)
    security = ClassSecurityInformation()

    def __init__(self, context):
        self.context = context
        self.portal = context.portal_url.getPortalObject()

    security.declarePrivate('is_blacklisted')
    def is_blacklisted(self, context=None, path=None):
        """ Checks if the adapter the context, the given
        `context` or the given `path` is blacklisted.
        """
        if context and path:
            raise ValueError('Only one of `context` and `path` can be checked at once.')
        elif not context and not path:
            context = self.context
        elif not path and type(context) in (str, unicode):
            path = context
            context = None
        if not path and isinstance(context, CatalogBrains.AbstractCatalogBrain):
            # context is a brain
            path = context.getPath()
        if not path:
            path = '/'.join(context.getPhysicalPath())

        path = path.strip()
        if path.endswith('/'):
            path = path[:-1]

        # check the path
        config = IConfig(self.portal)

        for blocked_path in config.getPathBlacklist():
            blocked_path = blocked_path.strip()
            if path == blocked_path:
                return True
            if blocked_path.endswith('*') and \
                    path.startswith(blocked_path[:-1]):
                if path == blocked_path[:-1]:
                    return True
                elif blocked_path[-2] != '/' and \
                        path[len(blocked_path) - 1] == '/':
                    return False
                else:
                    return True
        return False

from Acquisition import aq_base
from ftw.publisher.sender.utils import IS_AT_LEAST_PLONE_5_1
from plone import api
from zope.component import getUtility
from zope.event import notify
from zope.intid import IIntIds
from zope.lifecycleevent import ObjectModifiedEvent
import transaction


def set_related_items(obj, *args, **kwargs):
    related_items = list(args)

    if IS_AT_LEAST_PLONE_5_1 or kwargs.get('force_relation_values', False):
        from z3c.relationfield import RelationValue
        intids = getUtility(IIntIds)

        relations = [
            RelationValue(intids.getId(aq_base(item)))
            for item in related_items
        ]

        obj.relatedItems = relations

        notify(ObjectModifiedEvent(obj))
    else:
        obj.setRelatedItems(related_items)

    transaction.commit()


def add_behaviors(type_to_configure, *additional_behaviors):
    fti = api.portal.get().portal_types.get(type_to_configure)
    behaviors = list(fti.behaviors)
    behaviors += list(additional_behaviors)
    fti.behaviors = tuple(set(behaviors))
    transaction.commit()

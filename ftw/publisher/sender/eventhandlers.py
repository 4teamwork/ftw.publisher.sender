from ftw.publisher.core import belongs_to_parent
from zope.component import queryMultiAdapter
import os


def add_move_job(obj, event):
    """
    This event handles move and rename jobs
    """

    if os.environ.get('disable-publisher-for-testing', None):
        return

    if belongs_to_parent(obj):
        # We are moving a content which is considered part of the parent.
        # A move of this content should not be published instantly, but when
        # the parent is published.
        return

    if obj == event.object:
        # do nohting, if we are in portal_factory or the item is just created
        if not event.oldName:
            return
        url_endswith = event.object.REQUEST.get('ACTUAL_URL') \
            .split('/')[-1:][0]
        # also include manage_pasteObjects for ZMI support
        if url_endswith not in ['folder_rename_form',
                                'folder_paste',
                                'manage_pasteObjects',
                                'object_rename',
                                '@@fc-rename',
                                'object_paste']:
            return
        # set event info on
        move_view = queryMultiAdapter(
            (obj, obj.REQUEST),
            name="publisher.move")
        move_view(event, no_response=True)

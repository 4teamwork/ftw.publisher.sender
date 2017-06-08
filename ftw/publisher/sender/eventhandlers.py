from ftw.publisher.core.adapters.simplelayout_utils import is_sl_contentish
from zope.component import queryMultiAdapter
import os


def add_move_job(obj, event):
    """
    This event handles move and rename jobs
    """

    if os.environ.get('disable-publisher-for-testing', None):
        return

    if is_sl_contentish(obj):
        # We are moving a simplelayout block, which is considered part
        # of the content.
        # A move of content should not be published instantly, but when
        # the page is published.
        # Since the simplelayout publisher adapter makes sure that blocks
        # are removed when the content no longer exists on the backend,
        # we can savely skip publishing block movements instantly.
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
                                'object_paste']:
            return
        #set event info on
        move_view = queryMultiAdapter(
            (obj, obj.REQUEST),
            name="publisher.move")
        move_view(event, no_response=True)

from zope.component import queryMultiAdapter
import os


def add_move_job(obj, event):
    """
    This event handles move and rename jobs
    """

    if os.environ.get('disable-publisher-for-testing', None):
        return

    if obj == event.object:
        data = event.__dict__.copy()
        # do nohting, if we are in portal_factory or the item is just created
        if not data['oldName']:
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
        setattr(obj, 'event_information', data)
        move_view = queryMultiAdapter(
            (obj, obj.REQUEST),
            name="publisher.move")
        move_view(no_response=True)

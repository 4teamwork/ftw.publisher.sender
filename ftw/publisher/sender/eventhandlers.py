from zope.component import queryMultiAdapter


def add_move_job(obj, event):
    """
    This event handles move and rename jobs
    """
    if obj == event.object:
        # do nohting, if we are in portal_factory or the item is just created
        if not data['oldParent'] or not getattr(event.object, '_at_creation_flag', False):
            return        
        #set event info on on obj
        data = event.__dict__.copy()
        setattr(obj, 'event_information', data)
        move_view = queryMultiAdapter((obj, obj.REQUEST), name="publisher.move")
        move_view(no_response=True)

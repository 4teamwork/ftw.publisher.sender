from zope.component import queryMultiAdapter


def add_move_job(obj, event):
    """
    This event handles move and rename jobs
    """
    if obj == event.object:
        
        #set event info on on obj
        data = event.__dict__.copy()
        setattr(obj, 'event_information', data)
        move_view = queryMultiAdapter((obj, obj.REQUEST), name="publisher.move")
        move_view(no_response=True)

from ftw.publisher.sender.interfaces import IConfig


def add_saved_input_to_ignored_fields(site):
    config = IConfig(site)
    ignored_fields = config.get_ignored_fields()
    if 'FormSaveDataAdapter' in ignored_fields.keys():
        if 'SavedFormInput' not in ignored_fields['FormSaveDataAdapter']:
            ignored_fields['FormSaveDataAdapter'].append('SavedFormInput')
    else:
        ignored_fields['FormSaveDataAdapter'] = ['SavedFormInput', ]

    config.set_ignored_fields(ignored_fields)

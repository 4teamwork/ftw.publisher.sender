from ftw.simplelayout.configuration import synchronize_page_config_with_blocks


def synchronize_sl_page(obj, event):
    """
    Always synchronize the simplelayout page config with the blocks before publishing.
    """
    synchronize_page_config_with_blocks(obj)

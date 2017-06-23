from ftw.testbrowser import browser as default_browser
from ftw.testbrowser.pages import statusmessages


class Workflow(object):

    def __init__(self, browser=default_browser):
        self.browser = browser

    def get_status(self):
        locals()['__traceback_info__'] = self.browser.url
        elm = self.browser.xpath(
            '//span[starts-with(@class, "state-")]')
        assert elm, 'Could not find element containg current status'
        return elm.first.text

    def assert_status(self, status):
        locals()['__traceback_info__'] = self.browser.url
        current_status = self.get_status()
        assert status == current_status, \
            'Expected workflow state "%s" but it is "%s"' % (
            status, current_status)

    def do_transition(self, label, assert_success=True):
        locals()['__traceback_info__'] = self.browser.url
        elements = self.browser.xpath(
            '//a[starts-with(@id, "workflow-transition-")]')
        assert elements, 'No workflow transitions available.'

        links = {}
        for node in elements:
            links[node.text] = node

        assert label in links, 'Could not find transition "%s", got %s' % (
            label, links.keys())

        links[label].click()
        if assert_success:
            statusmessages.assert_message('Item state changed.')

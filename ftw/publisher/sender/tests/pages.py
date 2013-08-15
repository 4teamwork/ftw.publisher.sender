from ftw.testing import browser
from ftw.testing.pages import Plone


class Workflow(Plone):

    def get_status(self):
        locals()['__traceback_info__'] = browser().url
        elm = browser().find_by_xpath(
            '//span[starts-with(@class, "state-")]')
        assert elm, 'Could not find element containg current status'
        return elm.first.text

    def assert_status(self, status):
        locals()['__traceback_info__'] = browser().url
        current_status = self.get_status()
        assert status == current_status, \
            'Expected workflow state "%s" but it is "%s"' % (
            status, current_status)

    def do_transition(self, label, assert_success=True):
        locals()['__traceback_info__'] = browser().url
        elements = browser().find_by_xpath(
            '//a[starts-with(@id, "workflow-transition-")]')

        assert elements, 'No workflow transitions available.'

        links = {}
        for node in elements:
            links[self.normalize_whitespace(node.text)] = node

        assert label in links, 'Could not find transition "%s", got %s' % (
            label, links.keys())

        links[label].click()
        if assert_success:
            self.assert_portal_message('info', 'Item state changed.')

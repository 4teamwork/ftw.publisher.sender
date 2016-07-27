from DateTime import DateTime
from ftw.upgrade import UpgradeStep
from ftw.upgrade.progresslogger import ProgressLogger
from random import random
from zc.queue import Queue
from zope.annotation.interfaces import IAnnotations


class MigrateQueueToZCQueue(UpgradeStep):
    """Migrate queue to zc.queue.
    """

    def __call__(self):
        self.install_upgrade_profile()
        annotations = IAnnotations(self.portal)

        jobs = annotations.get('publisher-queue', ())
        if hasattr(jobs, 'values'):
            jobs = jobs.values()

        queue = annotations['publisher-queue'] = Queue()
        map(queue.put, ProgressLogger('Migrate jobs to new queue storage', jobs))

from datetime import datetime
from ftw.builder import Builder, create
from ftw.publisher.sender.interfaces import IQueue
from ftw.publisher.sender.persistence import Job
from ftw.publisher.sender.tests import FunctionalTestCase


class TestStorage(FunctionalTestCase):

    def setUp(self):
        super(TestStorage, self).setUp()
        self.grant('Manager')

        self.folder = create(Builder('folder').titled(u'Foo'))
        self.queue = IQueue(self.portal)

    def test_queue_has_no_jobs_by_default(self):
        self.assertEqual(0, self.queue.countJobs())

    def test_queue_has_no_executed_jobs_by_default(self):
        self.assertEqual((), tuple(self.queue.get_executed_jobs()))
        self.assertEqual(0, self.queue.get_executed_jobs_length())

    def test_adding_a_job_to_the_queue(self):
        self.queue.createJob('push', self.folder, 'user')

        # The queue contains one job now.
        self.assertEqual(1, self.queue.countJobs())

        # Make sure the job is there.
        self.assertEqual(
            ['push'],
            [job.action for job in self.queue.getJobs()]
        )

    def test_queue_after_publishing(self):
        """
        Simulate an entire publishing cycle.
        """
        self.queue.createJob('push', self.folder, 'user')

        self.queue.move_to_worker_queue()
        job = self.queue.popJob()
        self.assertEqual('push', job.action)

        key = self.queue.append_executed_job(job)
        self.assertEqual(1, key)

        self.assertEqual(0, self.queue.countJobs())
        self.assertEqual(1, self.queue.get_executed_jobs_length())

        executed_job = list(self.queue.get_executed_jobs())[0]
        self.assertEqual(key, executed_job[0])
        self.assertEqual('push', executed_job[1].action)

        self.queue.remove_executed_job(key)
        self.assertEqual([], list(self.queue.get_executed_jobs()))
        self.assertEqual(0, self.queue.get_executed_jobs_length())

    def test_clear_executed_jobs(self):
        for i in range(10):
            self.queue.append_executed_job(Job('push', self.folder, 'user'))

        self.assertEqual(10, self.queue.get_executed_jobs_length())

        self.queue.clear_executed_jobs()

        self.assertEqual((), tuple(self.queue.get_executed_jobs()))
        self.assertEqual(0, self.queue.get_executed_jobs_length())

    def test_get_executed_job_by_key(self):
        self.queue.clear_executed_jobs()

        for i in range(10):
            self.queue.append_executed_job('obj %i' % i)

        self.assertEqual(
            'obj 5',
            self.queue.get_executed_job_by_key(6)
        )
        with self.assertRaises(KeyError):
            self.queue.get_executed_job_by_key(1000)

    def test_get_batch_of_executed_jobs(self):
        self.queue.clear_executed_jobs()

        for i in range(10):
             self.queue.append_executed_job('obj %i' % i)

        self.assertEqual(10, self.queue.get_executed_jobs_length())

        self.assertEqual(
            [(1, 'obj 0'), (2, 'obj 1')],
            list(self.queue.get_executed_jobs(start=0, end=2))
        )
        self.assertEqual(
            [(5, 'obj 4')],
            list(self.queue.get_executed_jobs(start=4, end=5))
        )
        with self.assertRaises(ValueError):
            list(self.queue.get_executed_jobs(start=1000, end=1001))

    def test_get_batch_of_executed_jobs_on_empty_storage(self):
        self.queue.clear_executed_jobs()

        self.assertEqual(0, self.queue.get_executed_jobs_length())
        self.assertEqual((), tuple(self.queue.get_executed_jobs(0, 0)))
        self.assertEqual((), tuple(self.queue.get_executed_jobs(10, 2)))

    def test_remove_old_executed_jobs(self):
        self.queue.clear_executed_jobs()

        # Execute 19 jobs.
        for day in range(1, 20):
            job = Job('push', self.folder, 'user')
            date = datetime(year=2000, month=1, day=day, hour=12)
            job.executed_with_states({'date': date})
            self.queue.append_executed_job(job)

        self.assertEqual(19, self.queue.get_executed_jobs_length())

        # Remove old jobs (older than 2000-01-10, including the one from 2000-01-10).
        tenth = datetime(year=2000, month=1, day=10, hour=23)
        self.queue.remove_executed_jobs_older_than(tenth)
        self.assertEqual(9, self.queue.get_executed_jobs_length())

    def test_remove_jobs_with_filter(self):
        self.queue.clear_executed_jobs()

        for i in range(10):
            self.queue.append_executed_job(Job('push', self.folder, 'user'))

        self.assertEqual(10, self.queue.get_executed_jobs_length())

        entry_to_delete = tuple(self.queue.get_executed_jobs())[2]
        self.queue.remove_jobs_by_filter(lambda *params: params == entry_to_delete)

        self.assertEqual(9, self.queue.get_executed_jobs_length())

        self.assertTrue(entry_to_delete not in tuple(self.queue.get_executed_jobs()))



import unittest
from os import path

from agora.jobs import VideoStreamCondense

HERE = path.abspath(path.dirname(__file__))


class VideoStreamCondenseTestcase(unittest.TestCase):

    """
    Test agora.jobs.VideoStreamCondense job.
    """
    @classmethod
    def setup_class(cls):
        cls.sample_data_file = path.join(
            HERE, './fixtures/goonhilly-log-sample')

    def test_mr(self):
        """
        Let's make sure we can run a test runner
        """
        mr_job = VideoStreamCondense(['--no-conf', '-'])
        with open(self.sample_data_file, 'r') as data:
            mr_job.sandbox(stdin=data)
            results = []
            with mr_job.make_runner() as runner:
                runner.run()
                for line in runner.stream_output():
                    results.append(line)
        self.assertTrue(len(results) > 0)

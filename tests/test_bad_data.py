import unittest
from os import path

from agora.stats import PBSVideoStats
from mrjob.protocol import JSONProtocol

HERE = path.abspath(path.dirname(__file__))


class BadDataTestcase(unittest.TestCase):

    """
    Test playing_duration calculation in agora.stats.PBSVideoStats
    """
    @staticmethod
    def events_generator():
        """
        Parse the output from our VideoCondense mapper.
        """
        protocol = JSONProtocol()
        with open(path.join(HERE, './fixtures/bad_data_stream'), 'r') as f:
            line = f.readline()
            while line:
                key, events = protocol.read(line)
                yield key, events
                line = f.readline()

    @classmethod
    def setup_class(cls):
        """
        Parse our sample data into a format similar to what is expected for
        a MRJob reduce(key, events) method.
        """
        cls.events = {}
        for key, event in cls.events_generator():
            if key:
                key_events = cls.events.setdefault(key, [])
                key_events.append(event)
                cls.events[key] = key_events

    def perform_test(self, test_num, test):
        """
        General test helper method. Only adds events that correspond
        to the correct test number (test_num) and performs the passed
        in assert test.
        """
        for key, events in self.events.items():
            if key == test_num:
                stats = PBSVideoStats()
                for event in events:
                    stats.add_event(event)

                results = stats.summary()
                test(results)

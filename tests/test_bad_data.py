import unittest
from os import path

from mrjob.protocol import JSONProtocol

from agora.stats import PBSVideoStats

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

    def test_skip_negative_buffering(self):
        """
        Test that any negative buffering events are skipped
        """
        test = lambda results: self.assertTrue(
            results.get('buffering_length') >= 0)
        self.perform_test('1', test)

    def test_skip_negative_add_positive(self):
        """
        Tests that we can skip negative buffering length
        but still calculate correct data
        """
        test = lambda results: self.assertEqual(
            results.get('buffering_length'), 300)
        self.perform_test('2', test)

    def test_initial_buffering_length_correct(self):
        """
        Tests that initial_buffering_length is calculated
        correctly
        """
        test = lambda results: self.assertEqual(
            results.get('initial_buffering_length'), 100)
        self.perform_test('3', test)

    def test_initial_buffering_length_skip_negative(self):
        """
        Tests that all negative buffering is skipped
        """
        test = lambda results: self.assertEqual(
            results.get('initial_buffering_length'), 0)
        self.perform_test('4', test)

    def test_initial_buffering_length_mixed(self):
        """
        Tests that initial_buffering_length is
        calculated correctly with a mix of 
        negative and positive values
        """
        test = lambda results: self.assertEqual(
            results.get('initial_buffering_length'), 200)
        self.perform_test('5', test)

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

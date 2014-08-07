import unittest
import copy
from os import path

from mrjob.protocol import JSONProtocol

from agora.stats import PBSVideoStats

HERE = path.abspath(path.dirname(__file__))


class PlayingDurationTestcase(unittest.TestCase):

    """
    Test playing_duration calculation in agora.stats.PBSVideoStats
    """
    @staticmethod
    def events_generator():
        """
        Parse the output from our VideoCondense mapper.
        """
        protocol = JSONProtocol()
        input_filename = './fixtures/video-stream-mapper-custom'
        with open(path.join(HERE, input_filename), 'r') as f:
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

    def test_playing_duration_none(self):
        """
        Tests that we're calculating playing_duration correctly
        when passed events without timestamps
        """
        for key, events in copy.deepcopy(self.events.items()):
            stats = PBSVideoStats()
            for event in events:
                if event.get('event_date'):
                    event['event_date'] = None
                stats.add_event(event)
            results = stats.summary()
            self.assertEqual(results['playing_duration'], None)

    def test_playing_duration_mediastarted_only(self):
        """
        Test that we're calculating playing_duration correctly
        when only passed MediaStarted events
        """
        for key, events in copy.deepcopy(self.events.items()):
            stats = PBSVideoStats()
            for event in events:
                if event.get('event_type'):
                    event['event_type'] = 'MediaStarted'
                stats.add_event(event)
            results = stats.summary()
            self.assertEqual(results.get('playing_duration'), None)

    def test_playing_duration_mediaended_only(self):
        """
        Test that we're calculating playing_duration correctly
        when only passed MediaEnded events
        """
        for key, events in copy.deepcopy(self.events.items()):
            stats = PBSVideoStats()
            for event in events:
                if event.get('event_type'):
                    event['event_type'] = 'MediaEnded'
                stats.add_event(event)
            results = stats.summary()
            self.assertEqual(results.get('playing_duration'), None)

    def test_small_playing_duration(self):
        """
        Test that we are calculating the playing duration correctly
        for a small duration (1 minute) and only a MediaStarted
        and MediaEnded event
        """
        test = lambda results: self.assertEqual(
            results.get('playing_duration'), 60.0)
        self._perform_test('1', test)

    def test_medium_playing_duration(self):
        """
        Test that we are calculating the playing duration correctly
        for a medium duration (30 minutes) and only a MediaStarted
        and MediaEnded event
        """
        test = lambda results: self.assertEqual(
            results.get('playing_duration'), 1800.0)
        self._perform_test('2', test)

    def test_large_playing_duration(self):
        """
        Test that we are calculating the playing duration correctly
        for a large duration (2 hours) and only a MediaStarted
        and MediaEnded event
        """
        test = lambda results: self.assertEqual(
            results.get('playing_duration'), 7200.0)
        self._perform_test('3', test)

    def test_playing_duration_start_stop(self):
        """
        Test that we are calculating the playing duration correctly
        for a 30 minute duration with three sets of MediaStarted
        and MediaEnded pairs
        """
        test = lambda results: self.assertEqual(
            results.get('playing_duration'), 1800.0)
        self._perform_test('4', test)

    def test_playing_duration_incomplete(self):
        """
        Test that we are calculating the playing duration correctly
        in which user starts video, stops video, starts video again
        with no final MediaEnded event
        """
        test = lambda results: self.assertEqual(
            results.get('playing_duration'), 600.0)
        self._perform_test('5', test)

    def _perform_test(self, test_num, test):
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

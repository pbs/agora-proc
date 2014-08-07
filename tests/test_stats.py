import unittest
import copy
from os import path

from mrjob.protocol import JSONProtocol

from agora.stats import PBSVideoStats

HERE = path.abspath(path.dirname(__file__))


class PBSVideoStatsTestcase(unittest.TestCase):

    """
    Test agora.stats.PBSVideoStats
    """
    @staticmethod
    def events_generator():
        """
        Parse the output from our VideoCondense mapper.
        """
        protocol = JSONProtocol()
        input_filename = './fixtures/video-stream-mapper-sample'
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

    def test_finished_playback(self):
        """
        Test that we're accurately marking playback as finished.
        """
        for key, events in self.events.items():
            stats = PBSVideoStats()
            finished_playback = False
            for event in events:
                stats.add_event(event)
                if event.get('event_type') == 'MediaCompleted':
                    finished_playback = True
            results = stats.summary()
            self.assertEqual(
                results.get('finished_playback'), finished_playback)

    def test_latest_time(self):
        """
        Test that we're correctly calculating
        the time of the last event of a stream
        """
        for key, events in self.events.items():
            stats = PBSVideoStats()
            latest_time = None
            for event in events:
                stats.add_event(event)
                if event.get('event_date') > latest_time:
                    latest_time = event.get('event_date')
            results = stats.summary()
            self.assertEqual(results.get('latest_time'), latest_time)

    def test_latest_time_none(self):
        """
        Test that we're correctly calculating
        the time of the last event of a stream
        given events with no timestamps
        """
        for key, events in copy.deepcopy(self.events.items()):
            stats = PBSVideoStats()
            for event in events:
                if event.get('event_date'):
                    event['event_date'] = None
                stats.add_event(event)
            results = stats.summary()
            self.assertEqual(results.get('latest_time'), None)

    def test_earliest_time(self):
        """
        Test that we're correctly calculating
        the time of the first event of a stream
        """
        for key, events in self.events.items():
            stats = PBSVideoStats()
            earliest_time = None
            for event in events:
                stats.add_event(event)
                if event.get('event_date') < earliest_time:
                    earliest_time = event.get('event_date')
            results = stats.summary()
            self.assertEqual(results.get('earliest'), earliest_time)

    def test_earliest_time_none(self):
        """
        Test that we're correctly calculating
        the time of the first event of a stream
        given events with no timestamps
        """
        for key, events in copy.deepcopy(self.events.items()):
            stats = PBSVideoStats()
            earliest_time = None
            for event in events:
                if event.get('event_date'):
                    event['event_date'] = None
                stats.add_event(event)
            results = stats.summary()
            self.assertEqual(results.get('earliest_time'), earliest_time)

    def test_add_duration_event(self):
        """
        Test that only the correct MEDIA_EVENTS
        that have timestamps are added to the
        duration_events list
        """
        for key, events in self.events.items():
            stats = PBSVideoStats()
            for event in events:
                stats.add_event(event)

            results = stats.duration_events
            for edata in results:
                self.assertTrue(edata.get('etype') in stats.MEDIA_EVENTS)
                self.assertTrue(edata.get('edate') is not None)

    def test_sort_duration_events_in_order(self):
        """
        Test that we're sorting the duration_event timestamps
        (added in chronological order) correctly
        """
        for key, events in self.events.items():
            stats = PBSVideoStats()
            for event in events:
                stats.add_event(event)

            stats._calculate_duration()
            results = stats.duration_events
            for count, edata in enumerate(results):
                if count + 1 < len(results):
                    self.assertTrue(
                        edata.get('edate') <= results[count + 1].get('edate'))

    def test_sort_duration_events_reverse_order(self):
        """
        Test that we're sorting the duration_event timestamps
        (added in reversed order) correctly
        """
        for key, events in self.events.items():
            stats = PBSVideoStats()
            for event in reversed(events):
                stats.add_event(event)

            stats._calculate_duration()
            results = stats.duration_events
            for count, edata in enumerate(results):
                if count + 1 < len(results):
                    self.assertTrue(
                        edata.get('edate') <= results[count + 1].get('edate'))

import copy
import unittest
from os import path

from agora.stats import PBSVideoStats
from dateutil.parser import parse
from mrjob.protocol import JSONProtocol

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

    def test_media_quality_change_auto(self):
        """
        Test that we're tallying MediaQualityChangeAuto events
        """
        for key, events in self.events.items():
            stats = PBSVideoStats()
            auto_bitrate_events = 0
            for event in events:
                stats.add_event(event)
                if event.get('event_type') == 'MediaQualityChangeAuto':
                    auto_bitrate_events += 1
            results = stats.summary()
            self.assertEqual(
                results.get('auto_bitrate_events'), auto_bitrate_events)

    def test_media_quality_change_user(self):
        """
        Test that we're tallying MediaQualityChange events
        """
        for key, events in self.events.items():
            stats = PBSVideoStats()
            user_bitrate_events = 0
            for event in events:
                stats.add_event(event)
                if event.get('event_type') == 'MediaQualityChange':
                    user_bitrate_events += 1
            results = stats.summary()
            self.assertEqual(
                results.get('user_bitrate_events'), user_bitrate_events)

    def test_buffering_length(self):
        """
        Verify that we're summing the time a stream spends buffering.
        """
        streams_with_buffer_length = 0
        enum = -1
        for key, events in self.events.items():
            enum += 1
            stats = PBSVideoStats()
            stream_buffer_length = None
            open_start_buffer = False
            is_valid_buffering = True
            media_buffering_start_time = None
            media_buffering_start_location = None
            for event in events:
                stats.add_event(event)
                event_type = event.get('event_type')
                if not event_type:
                    is_valid_buffering = False
                    break
                if event_type == 'MediaBufferingStart':
                    if open_start_buffer:
                        # two MediaBufferingStart events in a row
                        # toss stream
                        is_valid_buffering = False
                        break
                    open_start_buffer = True
                    media_buffering_start_time = parse(event.get('event_date'))
                    media_buffering_start_location = event.get('x_video_location')
                if event_type == 'MediaBufferingEnd':
                    if not open_start_buffer:
                        # two MediaBufferingEnd events in a row
                        # toss stream
                        is_valid_buffering = False
                        break
                    open_start_buffer = False
                    # verify that we didn't scrub video
                    if event.get('x_video_location') != media_buffering_start_location:
                        is_valid_buffering = False
                        break
                    # subtract MediaBufferingEnd timestamp from
                    # MediaBufferingStart timestamp
                    if not stream_buffer_length:
                        stream_buffer_length = 0
                    media_buffering_end_time = parse(event.get('event_date'))
                    buffer_delta = media_buffering_end_time - media_buffering_start_time
                    stream_buffer_length += self._total_seconds(buffer_delta)
            if is_valid_buffering:
                results = stats.summary()
                results_buffering_length = results.get('buffering_length')
                self.assertEqual(results_buffering_length, stream_buffer_length)
                if stream_buffer_length is not None:
                    self.assertTrue(
                        results_buffering_length >= 0,
                        '%s is not a positive number' % results_buffering_length)
                    streams_with_buffer_length += 1
        self.assertTrue(streams_with_buffer_length > 0)

    def _total_seconds(self, timedelta):
        """
        Replacement for timedelta.total_seconds() which
        is not supported in python 2.6
        """
        delta_seconds = timedelta.days * 24 * 3600
        delta_microseconds = (timedelta.seconds + delta_seconds) * 10 ** 6
        return (timedelta.microseconds + delta_microseconds) / 10 ** 6

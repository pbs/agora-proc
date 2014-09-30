import logging

import pygeoip
from agora.logs import GoonHillyLog
from agora.stats import PBSVideoStats
from mrjob.job import MRJob


class VideoStreamCondense(MRJob):

    def __init__(self, args=None):
        self.isp_lookup = None
        super(VideoStreamCondense, self).__init__(args=args)
        self.logger = logging.getLogger('mrjob')

    def configure_options(self):
        """
        Add custom command line options.
        """
        super(VideoStreamCondense, self).configure_options()
        self.add_file_option(
            '--isp_db', help='Optional: path to ISP-lookup database')

    def load_options(self, args):
        """
        Load command-line options into self.options.
        https://pythonhosted.org/mrjob/job.html?highlight=configure_options#mrjob.job.MRJob.load_options
        """
        super(VideoStreamCondense, self).load_options(args)
        if self.options.isp_db:
            self.isp_lookup = pygeoip.GeoIP(
                self.options.isp_db, pygeoip.MEMORY_CACHE)

    def mapper(self, _, line):
        '''
        Takes a goonhilly line and parses all the fields to a dictionary
        '''
        self.increment_counter('job-metrics', 'total-events', 1)
        parsed_line = GoonHillyLog.parse_log_line(line)
        if not parsed_line:
            self.logger.debug(
                'agora.logs.GoonHillyLog: Unable to parse line: ' + line)
            self.increment_counter('job-metrics', 'unparsable-events', 1)

        elif parsed_line.get('x_tracking_id') and parsed_line.get('x_tpmid'):
            # if this line has a tracking id that uses guid, then
            # use key, else concatenate with x_tpmid to generate
            # more unique key
            key = parsed_line['x_tracking_id']
            if len(key) < 30:
                key += '-' + parsed_line['x_tpmid']

            self.increment_counter('job-metrics', 'valid-events', 1)
            yield key, parsed_line

        else:
            # No tracking id, no value to the statistics so skip it
            self.logger.debug(
                'Event: Unable to generate tracking key: ' + line)
            self.increment_counter('job-metrics', 'keyless-events', 1)

    def reducer(self, key, events):
        '''
        Aggregates all the play events
        '''
        # increment total number of streams
        self.increment_counter('event-metrics', 'total-streams', 1)

        # aggregate all events in a stream
        stats = PBSVideoStats(self.isp_lookup)
        for event in events:
            stats.add_event(event)

        summary = stats.summary()
        if summary.get('playing_duration'):
            # increment total number of playing_durations > 0
            self.increment_counter('event-metrics', 'valid-duration', 1)
        if summary.get('first_event_type'):
            # increment total for first_event_type
            self.increment_counter('first-event-type-metrics',
                                   summary.get('first_event_type'), 1)
        if summary.get('last_event_type'):
            # increment total for last event type
            self.increment_counter('last-event-type-metrics',
                                   summary.get('last_event_type'), 1)

        yield key, summary


def main():
    """
    Start a map reduce job with mrjob.conf settings
    """
    VideoStreamCondense.run()


if __name__ == '__main__':
    main()

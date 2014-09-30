import socket

from dateutil.parser import parse


class PBSVideoStats(object):

    # These are the only events that are parsed for playing duration
    MEDIA_START_EVENTS = ['MediaStarted', 'MediaInitialBufferStart']
    MEDIA_ENDED_EVENTS = ['MediaEnded', 'MediaCompleted']
    MEDIA_EVENTS = MEDIA_START_EVENTS + MEDIA_ENDED_EVENTS

    def __init__(self, isp_lookup=None):

        # Ids used to differentiate videos
        self.tracking_id = None
        self.media_id = None

        # Timestamps for earliest and latest events
        # in the stream
        self.earliest_time = None
        self.latest_time = None

        # Whether a stream was completed or not
        self.incomplete_stream = None
        self.finished_playback = False

        # Event types of first and last event in stream
        self.first_event_type = None
        self.last_event_type = None

        # Tracks amount of buffering and amount of video played
        self.buffer_start_events = 0
        self.playing_duration = 0

        self.source = None
        self.component = None
        self.auto_bitrate = None
        self.client_id = None
        self.title = None
        self.session_id = None
        self.user_agent = None
        self.position_earliest_play = None
        self.position_latest_play = None
        self.duration_events = []
        # track bitrate changes automatically made by the video player
        self.auto_bitrate_events = 0
        # track bitrate changes manually made by the user
        self.user_bitrate_events = 0

        # Keeps track of number of buffering events/video location
        # of the events
        self.buffering_positions = []
        self.buffering_events = 0

        # Keeps track of buffering length of stream
        self.buffering_length = 0
        self.initial_buffering_length = 0

        self.isp_lookup = isp_lookup

    def add_event(self, event):
        '''
        Take the events and calculate the following:
        https://projects.pbs.org/confluence/display/analytics/Video+Event+Tracking
        '''
        self.tracking_id = event['x_tracking_id']
        etype = None
        edate = None

        # TODO: check if current event's values are the same
        # set the following values only once per event
        if not self.source and event.get('source_tag'):
            self.source = event['source_tag']
        if not self.component and event.get('component'):
            self.component = event['component']
        if not self.client_id and event.get('client_id'):
            self.client_id = event['client_id']
        if not self.title and event.get('x_episode_title'):
            self.title = event['x_episode_title']
        if not self.session_id and event.get('x_session_id'):
            self.session_id = event['x_session_id']
        if not self.user_agent and event.get('x_user_agent'):
            self.user_agent = event['x_user_agent']

        # Skip event if it contains bad data
        if self._contains_bad_data(event):
            return

        # calc earliest and latest date of event
        if event.get('event_date'):
            edate = parse(event['event_date'])
            if self.earliest_time and (edate < self.earliest_time):
                self.earliest_time = edate
                self.first_event_type = event.get('event_type', None)
            elif not self.earliest_time:
                self.earliest_time = edate
                self.first_event_type = event.get('event_type', None)

            # since events are not necessarily given to the reducer in order
            # we have to grab the last event type while we grab the
            # last event date
            if self.latest_time and (edate > self.latest_time):
                self.latest_time = edate
                self.last_event_type = event.get('event_type', None)
            elif not self.latest_time:
                self.latest_time = edate
                self.last_event_type = event.get('event_type', None)

        # Now call the appropriate handler for the type of event
        if event.get('event_type'):
            etype = event['event_type']
            if etype == "MediaStarted":
                self._addEventMediaStarted(event)
            elif etype == "MediaEnded":
                self._addEventMediaEnded(event)
            elif etype == "MediaCompleted":
                self._addEventMediaCompleted(event)
            elif etype == "MediaBufferingStart":
                self._addEventMediaBufferingStart(event)
            elif etype == "MediaBufferingEnd":
                self._addEventMediaBufferingEnd(event)
            elif etype == "MediaInitialBufferEnd":
                self._addEventMediaInitalBufferEnd(event)
            elif etype == "MediaQualityChangeAuto":
                self._addEventMediaQualityChangeAuto(event)
            elif etype == "MediaScrub":
                self._addEventMediaScrub(event)
            elif etype == "MediaQualityChangedProgrammatically":
                self._addEventMediaQualityChangedProgrammatically(event)
            elif etype == "MediaQualityChange":
                self._addEventMediaQualityChange(event)

        # if event is a media start/end event and has a date timestamp,
        # save event to calculate playing_duration later
        if edate is not None and etype in self.MEDIA_EVENTS:
            self._add_duration_event(etype, edate)

    def summary(self):
        r = dict()
        r['tracking_id'] = self.tracking_id
        r['media_id'] = self.media_id
        r['earliest_time'] = str(self.earliest_time) if self.earliest_time else None
        r['latest_time'] = str(self.latest_time) if self.latest_time else None
        r['incomplete_stream'] = self.incomplete_stream
        r['finished_playback'] = self.finished_playback
        r['first_event_type'] = self.first_event_type
        r['last_event_type'] = self.last_event_type
        r['buffer_start_events'] = self.buffer_start_events
        r['playing_duration'] = self._calculate_duration()
        r['source'] = self.source
        r['component'] = self.component
        r['auto_bitrate'] = self.auto_bitrate
        r['client_id'] = self.client_id
        r['title'] = self.title
        r['session_id'] = self.session_id
        r['position_earliest_play'] = self.position_earliest_play
        r['buffering_events'] = self.buffering_events
        r['buffering_length'] = self.buffering_length
        r['initial_buffering_length'] = self.initial_buffering_length
        r['auto_bitrate_events'] = self.auto_bitrate_events
        r['user_bitrate_events'] = self.user_bitrate_events
        r['isp_name'] = None
        if self.client_id and self.isp_lookup:
            try:
                r['isp_name'] = self.isp_lookup.org_by_addr(self.client_id)
            except socket.error:
                # TODO: logging
                print 'BAD IP: %s' % self.client_id
        return r

    def _contains_bad_data(self, event):
        """
        Check if the current event has any
        incorrect or badly formatted data.
        """

        # All events must have a me
        if not self._check_media_id(event):
            print 'XXXX Fail!'
            return True

        try:
            # TODO: truncate floating to int
            # Events should not have negative buffering_length
            if int(event.get('x_buffering_length', 0)) < 0:
                print 'Negative Buffering'
                return True
        except ValueError:
            # buffering_length is a float (illegal)
            print 'Buffering Length not an integer'
            return True

        return False

    def _check_media_id(self, event):
        if not event.get('x_tpmid'):
            print 'no tp media id'
            return None

        if not self.media_id:
            self.media_id = event['x_tpmid']
        else:
            if self.media_id != event['x_tpmid']:
                print 'Media ID mismatch!'

        return True

    def _addEventMediaStarted(self, event):
        # We are seeing the play event in the stream so we consider it complete
        # from a logging perspective
        if self.incomplete_stream is None:
            self.incomplete_stream = True
        if event.get('x_video_location'):
            loc = event['x_video_location']
            if not self.position_earliest_play:
                self.position_earliest_play = loc
            elif self.position_earliest_play > loc:
                self.position_earliest_play = loc

    def _addEventMediaEnded(self, event):
        # figure last play endpoint
        self.incomplete_stream = False
        if event.get('x_video_location'):
            loc = event['x_video_location']
            if not self.position_latest_play:
                self.position_latest_play = loc
            else:
                self.position_latest_play = {
                    True: loc, False: self.position_latest_play}
                [self.position_latest_play < loc]

    def _addEventMediaCompleted(self, event):
        # figure last play endpoint
        self.incomplete_stream = False
        self.finished_playback = True
        if event.get('x_video_location'):
            loc = event['x_video_location']
            if not self.position_latest_play:
                self.position_latest_play = loc
            else:
                self.position_latest_play = {
                    True: loc, False: self.position_latest_play}
                [self.position_latest_play < loc]

    def _addEventMediaBufferingStart(self, event):
        self.buffer_start_events += 1

    def _addEventMediaBufferingEnd(self, event):
        if event.get('x_after_seek') == 'False':
            # only count buffering when not seeking
            return
        self.buffering_events += 1
        self.buffering_length += int(event.get('x_buffering_length', 0))
        if event.get('x_video_location'):
            loc = event['x_video_location']
            self.buffering_positions.append(loc)

        if event.get('x_auto'):
            if event['x_auto'] == 'true':
                self.auto_bitrate = True

    def _addEventMediaInitalBufferEnd(self, event):
        self.initial_buffering_length += int(event.get('x_buffering_length', 0))

    def _addEventMediaQualityChangeAuto(self, event):
        self.auto_bitrate_events += 1

    def _addEventMediaScrub(self, event):
        return

    def _addEventMediaQualityChangedProgrammatically(self, event):
        return

    def _addEventMediaQualityChange(self, event):
        self.user_bitrate_events += 1

    def _add_duration_event(self, etype, edate):
        # append dictionary of event type and timestamp
        # to the list of duration events
        self.duration_events.append({'etype': etype, 'edate': edate})

    def _calculate_duration(self):
        # sort duration events by timestamp
        self.duration_events.sort(key=lambda event: event['edate'])

        duration = 0
        start_time = None
        for event in self.duration_events:
            # if event is a start event, save event timestamp
            if event['etype'] in self.MEDIA_START_EVENTS:
                if not start_time:
                    start_time = event['edate']

            # if event is an end event, find time delta between
            # play and pause times and add to duration
            elif event['etype'] in self.MEDIA_ENDED_EVENTS:
                if start_time:
                    duration += self._total_seconds(
                        event['edate'] - start_time)
                    start_time = None

        # if no duration can be calculate, return None
        if duration == 0:
            duration = None

        return duration

    def _total_seconds(self, timedelta):
        """
        Replacement for timedelta.total_seconds() which
        is not supported in python 2.6
        """
        delta_seconds = timedelta.days * 24 * 3600
        delta_microseconds = (timedelta.seconds + delta_seconds) * 10 ** 6
        return (timedelta.microseconds + delta_microseconds) / 10 ** 6

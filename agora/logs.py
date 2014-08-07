# -*- coding: utf-8 -*-
import re
from dateutil.parser import parse


class GoonHillyLog(object):

    @staticmethod
    def parse_log_line(line):
        '''
        Parses a goonhilly log line and returns a dictionary of
        key value objects
        '''
        # attempt to get a valid date.  If no valid date, skip the line
        try:
            edate, etime, rline = line.split(' ', 2)
            event_date = " ".join((edate, etime.replace(',', '.')))
            # todo: convert date to UTC instead of local server time
            dateutil_event_date = parse(event_date)
            event_date = dateutil_event_date.strftime("%Y-%m-%d %H:%M:%S")
        except:
            # invalid date, skip the line
            # print 'skipping line'
            return None

        # just get the k,v part of the input line
        try:
            discard, data = rline.split('] ', 1)
        except:
            print line
            print '\n\n'
            print rline
            return None

        # get all the items
        # keys are allowed [a-zA-Z0-9_-]
        # values that are quoted can contain any character except double quotes
        # values that are not quotes cannot contain any spaces or
        # other whitespace
        matches = re.findall(r'[\w-]+=".+?"|[\w-]+=\S+', data)

        # partition each match at '=' and put a backslash in
        # front of all pipe chars '|'
        matches = [m.replace('|', '\|').split('=', 1) for m in matches]

        # use results to make a dict
        d = dict(matches)
        # add in the timestamp for consistency
        d['event_date'] = event_date

        # remove double quotes or single quotes from around values
        for k, v in d.iteritems():
            if v.startswith('"') and v.endswith('"'):
                d[k] = d[k][1:-1]

        # special transforms
        if d.get('x_session_id'):
            d['x_session_id'] = d['x_session_id'].lower()
        return d

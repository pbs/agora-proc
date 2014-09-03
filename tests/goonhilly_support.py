"""
This script takes in a number of GoonHilly formatted log files
and searches through them, aggregating which events/fields are
supported for a specific source_tag

NOTE: it is recommended that you first run zgrep
on all of the log files for the source_tag
you want and then pass that output into this script
or else it will take a very long time
"""
import argparse
from agora.logs import GoonHillyLog


def hilite(string, status, bold):
    """
    Converts string color to be either red or green
    """
    attr = []
    if status:
        # green
        attr.append('32')
    else:
        # red
        attr.append('31')
    if bold:
        attr.append('1')
    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)


def print_results(events, custom_fields, source_tag):
    """
    Prints results from aggregate event/field dictionaries
    """
    print '\nSOURCE: %s' % source_tag
    print '============================'
    sorted_event_keys = sorted(events.iterkeys())
    for key in sorted_event_keys:
        if events[key] > 0:
            result = hilite(str(events[key]), True, True)
        else:
            result = hilite(str(events[key]), False, True)

        print '%-40s:\t%s' % (key, result)

    print ''
    sorted_custom_field_keys = sorted(custom_fields.iterkeys())
    for key in sorted_custom_field_keys:
        if custom_fields[key] > 0:
            result = hilite(str(custom_fields[key]), True, True)
        else:
            result = hilite(str(custom_fields[key]), False, True)

        print '%-40s:\t%s' % (key, result)


def test_support(file_list, source_tag):
    events = {
        'MediaStarted': 0,
        'MediaEnded': 0,
        'MediaCompleted': 0,
        'MediaFailed': 0,
        'MediaQualityChange': 0,
        'MediaQualityChangeAuto': 0,
        'MediaQualityChangeProgramatically': 0,
        'MediaInitialBufferStart': 0,
        'MediaInitialBufferEnd': 0,
        'MediaBufferingStart': 0,
        'MediaBufferingEnd': 0,
        'MediaScrub': 0
    }

    custom_fields = {
        'x_useragent': 0,
        'x_tpmid': 0,
        'x_episode_title': 0,
        'x_program_title': 0,
        'x_producer': 0,
        'x_video_length': 0,
        'x_client_id': 0,
        'x_session_id': 0,
        'x_tracking_id': 0,
        'x_video_location': 0,
        'x_stream_size': 0,
        'x_flash_player': 0,
        'x_buffering_length': 0,
        'x_encoding_name': 0,
        'x_auto': 0,
        'x_bandwidth': 0,
        'x_after_seek': 0,
        'x_start_time': 0,
        'x_previous_quality': 0,
        'x_new_quality': 0
    }

    # Iterate over passed in files
    for filename in file_list:
        try:
            with open(filename, 'r') as f:
                print 'processing file...'

                # Read file line by line and aggregate all fields ecountered
                for line in f:
                    # Parse line into dict
                    fields = GoonHillyLog.parse_log_line(line)

                    # Skip line if event source tag is not what we are looking
                    # for
                    if fields.get('source_tag') != source_tag:
                        continue

                    # Iterate over all keys in the event
                    for key in fields.iterkeys():
                        # If the key is an event, increment counter for that
                        # event
                        if key == 'event_type' and fields.get(key) in events:
                            events[fields.get(key)] += 1

                        # If key is a custom field, increment counter for that
                        # field
                        elif key in custom_fields:
                            custom_fields[key] += 1
        except IOError:
            # Catch error if passed in file does not exist
            pass

    print_results(events, custom_fields, source_tag)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s',
                        required=True,
                        help='source tag to look for')

    parser.add_argument('-f',
                        nargs='*',
                        required=True,
                        help='files to search through')

    args = parser.parse_args()
    test_support(args.f, args.s)

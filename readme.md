Agora
=====

Agora is a batch analyzer of video stream logs. It heavily uses Amazon Web Services and is built using the open-source mrjob python module. It leverages AWS EMR to parallelize
the processing of client video player events.

Installation
------------
Pull down the repo and run
```
python setup.py install
```

Configuration
-------------
Before running Agora, you need to set up a configuration file to provide your AWS access keys and other information so that the mrjob module can access and pull down your log files to be processed. 

Usage
-----

#### Local usage
```
python agora.py <sample log file>
```

Performs the map-reduce locally. ```<sample log file>``` 
must be in your local file system

#### Online usages

#### Single job
```
python agora.py -v -r emr s3://bucket.name/path/to/input/ --output-dir=s3://bucket.name/path/to/output/ --no-output --conf-path=mrjob.conf
```

Creates an EMR cluster using the 'emr' runner configurations (specified in 'mrjob.conf'),
performs the map-reduce on the file at the path 's3://bucket.name/path/to/input/',
and stores the output at 's3://bucket.name/path/to/output/'
Note: the '--no-output' flag just enables "quiet" mode for emr job

#### Multiple job with ongoing cluster
Creates an EMR cluster, and then you can send multiple jobs to the cluster.
The configuration file has an idle timeout so remember to use it!

##### To start
```
python c:\Python27\Lib\site-packages\mrjob\tools\emr\create_job_flow.py --conf-path=mrjob.conf
```
This will return a flow id similar to: j-23M39HFR2PZCR

##### To submit a job
```
python agora.py -v -r emr --emr-job-flow-id=j-23M39HFR2PZCR s3://bucket.name/path/to/input --output-dir=s3://bucket.name/path/to/output/ --no-output --conf-path=mrjob.conf
```

##### To shutdown the cluster
```
python -m mrjob.tools.emr.terminate_job_flow j-23M39HFR2PZCR --conf-path=mrjob.conf
```

##### Automated Use
To setup Agora to run automatically, just create a new Cron Job that will run Agora
in Online Single Job mode and schedule the Job when you want it to run.

Events and Custom Fields
------
Agora's main purpose is to aggregate data for video player streaming events and any custom fields that have been defined.

### Event Types
Currently Agora is set up to listen for these event types:

**MediaStarted** – trigger this event anytime a user hits the play button on a video (could be multiple times per video if they are pausing the video and then continuing watching).

**MediaEnded** – trigger this event anytime a user hits the pause button (could also be multiple times per video).

**MediaCompleted** - trigger this event anytime a user completely finished watching a video.

**MediaFailed** – trigger this event anytime the video fails to work. 

**MediaInitialBufferStart** – trigger this event when the video player starts the initial buffering.

**MediaInitialBufferEnd** – trigger this event when the video player starts playing after the initial buffering event.

**MediaBufferingStart** – trigger this event anytime the video player experiences a buffering issue.

**MediaBufferingEnd** – trigger this event anytime the video begins playing again after a buffering event.

**MediaScrub** – trigger this event after a user has started and then completed a scrub/seek to a different time location in the video.

### Custom Fields
Currently Agora is set up to aggregate these custom fields:

**x_useragent**: the user agent where the video is playing

**x_tpmid**: video ID ***REQUIRED***

**x_episode_title**: video title

**x_program_title**: program slug

**x_producer**:  call letters of the producer of the video

**x_video_length**: video duration

**x_client_id**: unique number identifying the current client (unique per browser/device)

**x_session_id**: unique number identifying the current session (unique per client session)

**x_tracking_id**: unique number identifying distinct requests for an individual video (unique per single video watching session) ***REQUIRED***

**x_video_location**: the time location within the video when the event was triggered (in seconds)

**x_stream_size**: the current HLS stream being played (ie. 1172, 391, etc..)

**x_flash_player**: identifies if the user has flash enabled

**x_buffering_length**: the current HLS buffer size in milliseconds

**x_encoding_name**: video encoding type

**x_auto**: the video quality setting

**x_bandwidth**: the user’s bandwidth

**x_after_seek**: identifies if the event was triggered after a seek

**x_start_time**: the video’s start time in milliseconds

### Sample Data
Agora takes in a text file of logs that are broken into lines where each line represents a video player event and consists of a date timestamp and key-value event data pairs. here is what a sample line might look like:
NOTE: This is only a small example line
```
yyyy-mm-dd hh:mm:ss - [INFO] event_key_1="event data here" event_key_2="more data" x_tpmid="tpmid here" x_tracking_id="tracking id here"
```

### Defining Your Own Custom Fields
You can define or rename your own custom fields for agora to use by editing stats.py



Notes about S3 Paths
--------------------
For input
The input path can be a single file, a entire s3 'directory' but not a wildcard path.  The EMR job will recurse all keys in the S3 bucket that matches

* Single file
```
    s3://bucket.name/path/to/input/yyyy-mm-dd/logs.gz
```
* Directory
```
    s3://bucket.name/path/to/input/yyyy-mm-dd/
```

As a convenient convention, s3 file paths should be of the form:
```
	s3://bucket.name/path/to/input/yyyy-mm-dd
```
where yyyy-mm-dd refers to the date that file contains event logs for


Notes about AWS credentials
--------------------------
These can be placed in your mrjob.conf file or see the mrjob documentation

Other
-----
Uses [mrjob][1]

[1]:https://pythonhosted.org/mrjob/


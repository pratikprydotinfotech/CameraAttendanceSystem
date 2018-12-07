CameraAttendanceSystem
======================

Documentation
----

CameraAttendanceSystem v1.0.0.


Pi3CAM features
----

````
gCamera.annotate_text = "Hello"
gCamera.brightness = 70
gCamera.resolution = (1024, 768) 
gCamera.framerate = 30

````

MP4Box
----

**Overview**

The multimedia packager available in GPAC is called MP4Box.

It can be used for performing many manipulations on multimedia files like AVI, MPG, TS, but mostly on ISO media files (e.g. MP4, 3GP). 

Here we are use for file conversion from Raw .h264 file to .mp4 file. 

````
$ MP4Box -fps 30 -add video.h264 outfile.mp4'
````

Pi Camera Test Case
----

We need to decide fps as per our PiCam decided framerate.

Suppose, Picam framerate 30 fps and MP4Box conversion framerate 90 fps then 
your Video image result will be poor.

So,PiCam framerate must be equal to MP4Box conversion fps.

In PiCam Resolution limit is there.

**Here some test cases of Picam Video :**

Default video Resolution : w-1366 x h-768 

Default video fps : 25 

| Image / Video | Resolution |  Framerate |  Quality |
| --- | --- | --- | --- |
| Image  | Max : 2592 x 1944 | 50 | Excelent |
| Image  | Max : 2592 x 1944 | 60 | Color chnage on screen |
| Video   | 2,048 × 1,024 | 30 | Stuck camera preview & Pi also |
| Video   | 640 x 480 | 90 | Bad |
| Video   | 1024 x 768 | 30 | Good (4MB , 5 sec) |
| Video   | 1024 x 768 | 90 | Frame rate exceed |
| Video   | 1024 x 768  | 50 | Bad(6MB , 5sec) |


Localhost Server for testing 
----

````
$ python -m SimpleHTTPServer 8000
````
Using above command you can start localhost server for testing.



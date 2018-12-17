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

Raspberry pi GPIO Read pins
----
````
pi@turnout_iot:~ $ gpio readall

 |---|---|---|---|---|---|---|---|---|---|---|
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 |---|---|---|---|---|---|---|---|---|---|---|---|
 |     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
 |   2 |   8 |   SDA.1 |   IN | 1 |  3 || 4  |   |      | 5v      |     |     |
 |   3 |   9 |   SCL.1 |   IN | 1 |  5 || 6  |   |      | 0v      |     |     |
 |   4 |   7 | GPIO. 7 |   IN | 1 |  7 || 8  | 1 | ALT5 | TxD     | 15  | 14  |
 |     |     |      0v |      |   |  9 || 10 | 1 | ALT5 | RxD     | 16  | 15  |
 |  17 |   0 | GPIO. 0 |   IN | 0 | 11 || 12 | 0 | OUT  | GPIO. 1 | 1   | 18  |
 |  27 |   2 | GPIO. 2 |   IN | 0 | 13 || 14 |   |      | 0v      |     |     |
 |  22 |   3 | GPIO. 3 |   IN | 0 | 15 || 16 | 1 | OUT  | GPIO. 4 | 4   | 23  |
 |     |     |    3.3v |      |   | 17 || 18 | 0 | OUT  | GPIO. 5 | 5   | 24  |
 |  10 |  12 |    MOSI |   IN | 0 | 19 || 20 |   |      | 0v      |     |     |
 |   9 |  13 |    MISO |   IN | 0 | 21 || 22 | 1 | OUT  | GPIO. 6 | 6   | 25  |
 |  11 |  14 |    SCLK |   IN | 0 | 23 || 24 | 0 | OUT  | CE0     | 10  | 8   |
 |     |     |      0v |      |   | 25 || 26 | 1 | OUT  | CE1     | 11  | 7   |
 |   0 |  30 |   SDA.0 |   IN | 1 | 27 || 28 | 1 | IN   | SCL.0   | 31  | 1   |
 |   5 |  21 | GPIO.21 |   IN | 1 | 29 || 30 |   |      | 0v      |     |     |
 |   6 |  22 | GPIO.22 |   IN | 1 | 31 || 32 | 0 | IN   | GPIO.26 | 26  | 12  |
 |  13 |  23 | GPIO.23 |   IN | 0 | 33 || 34 |   |      | 0v      |     |     |
 |  19 |  24 | GPIO.24 |   IN | 0 | 35 || 36 | 0 | IN   | GPIO.27 | 27  | 16  |
 |  26 |  25 | GPIO.25 |   IN | 0 | 37 || 38 | 0 | IN   | GPIO.28 | 28  | 20  |
 |     |     |      0v |      |   | 39 || 40 | 0 | IN   | GPIO.29 | 29  | 21  |
 |---|---|---|---|---|---|---|---|---|---|---|---|
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 |---|---|---|---|---|---|---|---|---|---|---|

````



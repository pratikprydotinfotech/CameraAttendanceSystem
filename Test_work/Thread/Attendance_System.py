#-------------------------------------------------------------------------------------------------------------------------------------
#File Name 		   : Attendance_System.py 
#Author(s) 		   : Pratik Panchal
#Purpose of module : Attendance system provide some features like Record Video when door will open,
# 					 process on video and video will upload on server. 
#Date of creation  : 22/11/2018
#-------------------------------------------------------------------------------------------------------------------------------------
import threading, signal
import json
import csv
import os, sys
import pycurl   # pycurl module import
import wiringpi # wiringpi module import for GPIO 
import time     # time library module import
from StringIO import StringIO
from datetime import datetime 
from subprocess import check_output
from picamera import PiCamera # pi camera function use from picamera module
from time import sleep 		  # sleep function use from time library module      

RUNNING = True
threads = []

global giFlag 				  # globally define flag
giFlag = 1

global gOut

global giCount
giCount=0

global giTimeCount
giTimeCount=0

global gfDurationBuf
gfDurationBuf = 0

global giVidCount
giVidCount = 0

abs_path = os.getcwd()
abs_path = abs_path+'/'

url = "http://192.168.0.4:9128/upload"
DEFINE_INTERATION = 3 # Interation for Server busy status and Time out Status 
ENTRY_IMAGES = 7 # Door open then 5 images will capture and send on server 
READ_SWITCH = 23 # Reed_switch GPIO use 23 

LOG_PATH = abs_path+"Test_Log" # Log directory generation path
MP4_PATH = abs_path+"outfile.mp4" # Output .mp4 file generation path
LOG_FILE_PATH = abs_path+"Test_Log/log.csv" #log.csv file generation path
RAW_FILE_PATH = abs_path+'video.h264' # Raw .h264 file generation path

# define user-defined exceptions for Server Busy
class Error(Exception):
   """Base class for other exceptions"""
   pass

class ServerBusyError(Error):

   pass

def monitoring(tid, itemId=None, threshold=None):
    global RUNNING
    while(RUNNING):
        print "PID=", os.getpid(), ";id=", tid

        if tid == 1:
            Loop()
        
        if tid == 2:
            fun2()

        time.sleep(0.2)
    print "Thread stopped:", tid

def handler(signum, frame):
    print "Signal is received:" + str(signum)
    global RUNNING
    RUNNING=False
    #global threads

def fun2():
	print ('In Fun2 >>>>>>>')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: LogFileGeneration
# @ Parameter 	: void
# @ Return 		: void
# @ Brief 		: This Function is Genrate Log data file
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def LogFileGeneration():
	global gOut
	os.system('rm -rf Test_Log') # Old Test_Log directory remove when System will restart 
	os.mkdir( LOG_PATH, 0755 )  # New Test_Log directory generate
	gOut = csv.writer(open(LOG_FILE_PATH,"w"), delimiter=',' , quoting=csv.QUOTE_ALL) #log.csv file generate in Test_Log directory 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Setup
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is initialize GPIO ,Camera , Log data file
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Setup():
	global gCamera
	global giFlag 
	giFlag = 1
	LogFileGeneration()
	gOut.writerow([('Setup Function Intialize_%s' %(str(datetime.now())))])
	wiringpi.wiringPiSetupGpio()  
	wiringpi.pinMode(READ_SWITCH, 0) # Reed switch GPIO 23 as a Input direction     
	wiringpi.pullUpDnControl(READ_SWITCH,1) # e.g 1 - PullDown , 0 - PullUp
	wiringpi.wiringPiISR(READ_SWITCH, wiringpi.INT_EDGE_RISING, DoorEvent) # Interrupt ISR init by using Edge triggering in Rising edge 
	#gOut.writerow(['GPIO Init','Sucess']) 
	gCamera = PiCamera() # camera return : <picamera.camera.PiCamera object at 0x75a382a0>
	#gOut.writerow(['Camera Init','Sucess'])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: VideoTimeDuration
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function give time duration of Video
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def VideoTimeDuration():

	ucVideoDuration = str(check_output('ffprobe -i  "'+ MP4_PATH +'" 2>&1 |grep "Duration"',shell=True)) 

	ucVideoDuration = ucVideoDuration.split(",")[0].split("Duration:")[1].strip()

	h, m, s = ucVideoDuration.split(':')
	gfDurationBuf = int(h) * 3600 + int(m) * 60 + float(s)

	print(gfDurationBuf)
	gOut.writerow([('Time Duration_%s' %(str(datetime.now()))),gfDurationBuf])

	if gfDurationBuf <= 1.0:
		os.system('rm -rf VID_%d.mp4' %giVidCount)
		gOut.writerow([('Discard Video_%s' %(str(datetime.now()))),'VID_%d.mp4' %giVidCount])
	else:
		SendData()
		gOut.writerow([('Store Video_%s' %(str(datetime.now()))),'VID_%d.mp4' %giVidCount])
    
	os.system('rm -rf outfile.mp4 video.h264')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: SendData
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Sending Form data on server 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def SendData(): 
	global giCount
	global giTimeCount
	global giFlag
	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 		#Create pycurl instance 
	c.setopt(c.URL, url) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	#testing
	#~~~~~~~~~~~~~~~~~~~~
	send = [("file", (c.FORM_FILE, MP4_PATH)),("timestamp",str(datetime.now())),] # Sending Camera generated file and timestamp in the form of "Form data" formate
	#~~~~~~~~~~~~~~~~~~~~

	c.setopt(c.HTTPPOST,send) 		   # POST "form data" on server
	c.setopt(pycurl.CONNECTTIMEOUT, 1) # Timeout 1 second
	
# Try and Exception for Server Timeout 

	try:
		c.perform()
		c.setopt(c.URL, url)
		
	except pycurl.error, error:
		errno, errstr = error
		gOut.writerow([('An error occurred_%s' %(str(datetime.now()))), '%s' %errstr])
		print 'An error occurred: ', errstr  # An error occured : Connection timed out after 1001 milliseconds
		giTimeCount+=1
		if giTimeCount >= DEFINE_INTERATION: # 3 times time out interation check then flag will be zero and will go in ideal state 
				giTimeCount = 0
				giFlag = 0
		Loop()
    
	c.close() 
	
	ucContent = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
	
	j = json.loads(ucContent) 		# Decode json data
	
# Server status maintain in Log file.
	
	if j['success'] == False:
	 gOut.writerow([('Send Data on Server_%s' %(str(datetime.now()))),'Fail'])
	 gOut.writerow(['value %s' % ucContent])
	else:
	 gOut.writerow([('Send Data on Server_%s' %(str(datetime.now()))),'Sucess'])
	 gOut.writerow(['value %s' % ucContent])
 
# Try and Exception for Status of Server 

	try:

			if j['success'] == False:
				raise ServerBusyError
			else:
				gOut.writerow([('Server is Healthy_%s' %(str(datetime.now())))])

	except ServerBusyError:
			gOut.writerow([('Server Busy_%s' %(str(datetime.now())))])
			giCount+=1
			print ('Server Busy')
			print ('count %s' %giCount)
			if giCount >= DEFINE_INTERATION:
				giCount = 0
				gOut.writerow([('Server Busy overflaw_%s' %(str(datetime.now())))])
				giFlag = 0
			Loop()
giFlag = 0
					 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: CaptureVideo
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Capturing Video 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~		 
def CaptureVideo():		
			global giFlag
			global giVidCount
			gCamera.annotate_text = "Rydot infotech Attendance System"
			gCamera.brightness = 70
			gCamera.resolution = (1024, 768) 
			gCamera.framerate = 30
			gOut.writerow(['Video_Record_Start_%s' %(str(datetime.now()))])
			gCamera.start_recording(RAW_FILE_PATH)
			gOut.writerow(['Raw .h264 file generated_%s' %(str(datetime.now()))])	

			while wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1:  
					gCamera.wait_recording()
					#time.sleep(1)
					print ('Recording wait')
						
			gCamera.stop_recording()
			gOut.writerow(['Video_Record_Stop_%s' %(str(datetime.now()))])	
			os.system('MP4Box -fps 30 -add video.h264 outfile.mp4')
			os.system('cp outfile.mp4 VID_%d.mp4' %giVidCount)
			gOut.writerow(['MP4 file generated_%s' %(str(datetime.now()))])	
			VideoTimeDuration()
			giVidCount += 1
			
			
	
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: DoorEvent
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Interrupt Service Routine
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def DoorEvent():
	global giFlag
	giFlag = 1
	gOut.writerow([('In Interrupt_%s' %(str(datetime.now()))),'Door Event Init'])
	print ('In ISR')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Loop
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Looping System
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Loop():
	#while True:  
            
			print wiringpi.digitalRead(READ_SWITCH)
			time.sleep(0.2)	
			global giFlag
			global giCount
			print ('flag %s' %giFlag)
			print ('count %s' %giCount)				

			if wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1:   
					gOut.writerow([('Door Position_%s' %(str(datetime.now()))),'Open'])
					print ('OPEN')
					#time.sleep(0.2)	
					CaptureVideo()
					
					#giFlag = 0
			else:
				print ('CLOSE')
				#os.system('rm -rf outfile.mp4 video.h264')

			#	gOut.writerow([('Door Position_%s' %(str(datetime.now()))),'Close'])
			#	giFlag = 0

# def DoorEventThreadStart():
# 	t1 = threading.Thread(target=Loop, args=()) 
# 	t1.start() 
# 	while(RUNNING):
# 		print ('Main program is sleeping')
#         time.sleep(30)
#     #for thread in threads:
#         t1.join()

	#t1.join()  

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: main()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is main function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGALRM, handler)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGQUIT, handler)
    Setup()

    print "Starting all threads..."
    DoorEventThread = threading.Thread(target=monitoring, args=(1,), kwargs={'itemId':'1', 'threshold':60})
    DoorEventThread.start()
    threads.append(DoorEventThread)

    VideoProcessThread = threading.Thread(target=monitoring, args=(2,), kwargs={'itemId':'2', 'threshold':60})
    VideoProcessThread.start()
    threads.append(VideoProcessThread)

    while(RUNNING):
        print "Main program is sleeping."
        time.sleep(30)
    for thread in threads:
        thread.join()

    print "All threads stopped."
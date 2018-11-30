#-------------------------------------------------------------------------------------------------------------------------------------
#File Name 		   : test_vid.py 
#Author(s) 		   : Pratik Panchal
#Purpose of module : Attendance system provide some features like Record Video when door will open,
# 					 process on video and video will upload on server. 
#Date of creation  : 22/11/2018
#Last Modification : 30/11/2018
#-------------------------------------------------------------------------------------------------------------------------------------
import threading, signal
import pika
import json
import csv
import os, sys
import pycurl   # pycurl module import
import wiringpi # wiringpi module import for GPIO 
import time     # time library module import
import subprocess
from StringIO import StringIO
from datetime import datetime 
from subprocess import check_output #check_output subprocess creating for VideoDuration() function
from picamera import PiCamera # pi camera function use from picamera module
from time import sleep 		  # sleep function use from time library module      
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

global count # testing
count = 0  # testing

global InputFile
global MQRecPath

abs_path = os.getcwd()
abs_path = abs_path+'/'

url = "http://192.168.0.4:9128/upload"
DEFINE_MODE = 0 # image = 0 ; video = 1
ENTRY_IMAGES = 1 # Door open then 5 images will capture and send on server 
DEFINE_INTERATION = 3 # Interation for Server busy status and Time out Status 
READ_SWITCH = 23 # Reed_switch GPIO use 23 

IMAGE_DIR_PATH = abs_path+"Image"
LOG_DIR_PATH = abs_path+"Test_Log" # Log directory generation path
MP4_DIR_PATH = abs_path+"MP4_Video" # Output .mp4 file generation path
LOG_FILE_PATH = abs_path+"Test_Log/log.csv" #log.csv file generation path
RAW_DIR_PATH = abs_path+'Raw_Video' # Raw .h264 file generation path
WIFI_FILE_PATH = '$(echo $(pwd)/Test_Log/WifiNetLog.csv)' # WifiConnectivity log file path
MP4_FILE_PATH = (abs_path+'MP4_Video/VID_%s.mp4' %giVidCount)
MQ_IMAGE_PATH = (abs_path+'Image/image%s.jpg'% (giVidCount))
MQ_VIDEO_PATH = (abs_path+'Raw_Video/video%s.h264'% (giVidCount))
DATE_TIME = ('%s' %(str(datetime.now())))
TIMEOUT_SEC = 1 # Server Time out e.g 1 Sec  

# define user-defined exceptions for Server Busy
class Error(Exception):
   """Base class for other exceptions"""
   pass

class ServerBusyError(Error):

   pass

global flag
flag = 0
global fpLogFile

class GracefulKill:
  global gOut
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: LogFileGeneration()
# @ Parameter 	: void
# @ Return 		: void
# @ Brief 		: This Function is Genrate Log and Raw Video directory
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def LogFileGeneration():
	global gOut
	global fpLogFile
	os.system('rm -rf Test_Log')   # Test_Log directory remove 
	os.mkdir( LOG_DIR_PATH, 0755 )  # New Test_Log directory generate
	os.system('rm -rf Raw_Video')  # Raw_Video directory remove 
	os.mkdir( RAW_DIR_PATH, 0755 )  # New Raw_Video directory generate
	os.system('rm -rf MP4_Video') # MP4_Video directory remove 
	os.mkdir( MP4_DIR_PATH, 0755 )  # New MP$_Video directory generate
	os.system('rm -rf Image') # Image directory remove 
	os.mkdir( IMAGE_DIR_PATH, 0755 )  # New MP$_Video directory generate
	os.system('echo "Wifi_Internet_Connectivity_Status" >> '+WIFI_FILE_PATH)
	os.system('echo "Date&Time,Net_Connectivity" >> '+WIFI_FILE_PATH)
	fpLogFile = open(LOG_FILE_PATH,"w")
	gOut = csv.writer(fpLogFile, delimiter=',' , quoting=csv.QUOTE_ALL) #log.csv file generate in Test_Log directory 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Setup()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is initialize GPIO ,Camera,Log and Raw Video directory
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Setup():
	global gCamera
	global giFlag 
	giFlag = 1
	LogFileGeneration() # Generate Log and Raw file Video Directory
	gOut.writerow([DATE_TIME,'Setup Function Intialize'])
	wiringpi.wiringPiSetupGpio() # Initialize wiring GPIO   
	
	if DEFINE_MODE == 0:
		READ_SWITCH = 24
		wiringpi.pullUpDnControl(READ_SWITCH,1) # e.g 1 - PullDown , 0 - PullUp
		wiringpi.pinMode(READ_SWITCH, 0) # Reed switch GPIO 23 as a Input direction  
		wiringpi.wiringPiISR(READ_SWITCH, wiringpi.INT_EDGE_FALLING, DoorEventInterrupt) # Interrupt ISR init by using Edge triggering in Rising edge 
	if DEFINE_MODE == 1:
		READ_SWITCH = 23
		wiringpi.pullUpDnControl(READ_SWITCH,1) # e.g 1 - PullDown , 0 - PullUp
		wiringpi.pinMode(READ_SWITCH, 0) # Reed switch GPIO 23 as a Input direction  
		wiringpi.wiringPiISR(READ_SWITCH, wiringpi.INT_EDGE_RISING, DoorEventInterrupt) # Interrupt ISR init by using Edge triggering in Rising edge    
	gCamera = PiCamera() # camera return : <picamera.camera.PiCamera object at 0x75a382a0>
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: VideoTimeDuration()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function give time duration of Video and 
#				  Check if video Time duration <=1.0 Sec then discard video
#				  else Send video file on server.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def VideoTimeDuration():
	global giVidCount
	ucVideoDuration = str(check_output('ffprobe -i  "'+ (abs_path+'MP4_Video/VID_%s.mp4' %giVidCount) +'" 2>&1 |grep "Duration"',shell=True)) 

	ucVideoDuration = ucVideoDuration.split(",")[0].split("Duration:")[1].strip()

	h, m, s = ucVideoDuration.split(':')
	gfDurationBuf = int(h) * 3600 + int(m) * 60 + float(s)

	print(gfDurationBuf)
	gOut.writerow([DATE_TIME,'Time_Duration',gfDurationBuf])
	if gfDurationBuf <= 1.0:
		os.system('rm -rf MP4_Video/VID_%d.mp4' %giVidCount)
		gOut.writerow([DATE_TIME,'Discard_Video','MP4_Video/VID_%d.mp4' %giVidCount])
		os.system('rm -rf outfile.mp4')
	else:
		SendData(MP4_FILE_PATH)
		os.system('rm -rf outfile.mp4')
		gOut.writerow([DATE_TIME,'Store_Video','MP4_Video/VID_%d.mp4' %giVidCount])
	giVidCount += 1
		

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: SendData()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Sending Form data on server 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def SendData(SendFilePath): 
	global giCount
	global giTimeCount
	global giFlag
	global giVidCount

	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 		#Create pycurl instance 
	c.setopt(c.URL, url) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	send = [("file", (c.FORM_FILE,SendFilePath)),("timestamp",str(datetime.now())),] # Sending Camera generated file and timestamp in the form of "Form data" formate

	c.setopt(c.HTTPPOST,send) 		   # POST "form data" on server
	c.setopt(pycurl.CONNECTTIMEOUT, TIMEOUT_SEC) # Timeout 1 second
	
# Try and Exception for Server Timeout 

	try:
		c.perform()
		c.setopt(c.URL, url)
		
	except pycurl.error, error:
		errno, errstr = error
		gOut.writerow([DATE_TIME,'An error occured','%s' %errstr])
		print 'An error occurred: ', errstr  # An error occured : Connection timed out after 1001 milliseconds
		giTimeCount+=1
		if giTimeCount >= DEFINE_INTERATION: # 3 times time out interation check then flag will be zero and will go in ideal state 
				giTimeCount = 0
				giFlag = 0
		#Loop()
    
	c.close() 
	
	ucContent = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
	print (ucContent)
	j = json.loads(ucContent) 		# Decode json data
	
# Server status maintain in Log file.
	
	if j['success'] == False:
	 gOut.writerow([DATE_TIME,'Send Data on Server','Fail'])
	 gOut.writerow([DATE_TIME,'value %s' % ucContent])
	else:
	 gOut.writerow([DATE_TIME,'Send Data on Server','Sucess'])
	 gOut.writerow([DATE_TIME,'value %s' % ucContent])

# Try and Exception for Status of Server 

	try:

			if j['success'] == False:
				raise ServerBusyError
			else:
				gOut.writerow([DATE_TIME,'Server Status','Healthy'])
	except ServerBusyError:
			gOut.writerow([DATE_TIME,'Server Status','Busy'])
			giCount+=1
			print ('Server Busy')
			print ('count %s' %giCount)
			if giCount >= DEFINE_INTERATION:
				giCount = 0
				gOut.writerow([DATE_TIME,'Server Status','Busy_Overflaw'])
				giFlag = 0
			#Loop()
giFlag = 0
			 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: CaptureVideo()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Capturing Video when Door event occur.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~		 
def CaptureVideo():		
			global giFlag
			global giVidCount
			gCamera.annotate_text = ('Rydot infotech Attendance System_'+DATE_TIME)
			gCamera.brightness = 50
			gCamera.resolution = (1024, 768) 
			gCamera.framerate = 30
			gOut.writerow([DATE_TIME,'Video_Recording_Start'])
			gCamera.start_recording(abs_path+'Raw_Video/video%s.h264' %giVidCount)
			gOut.writerow([DATE_TIME,'Raw .h264 file generated'])
			while wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1:  
					gCamera.wait_recording()
						
			gCamera.stop_recording()
			gOut.writerow([DATE_TIME,'Video_Recording_Stop'])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: CaptureImage
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Capturing Image 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~		 
def CaptureImage():
			global count
			gOut.writerow(['Capture Image','Sucess'])
			gCamera.framerate = 15
			gCamera.resolution = (1024, 768) 
			gCamera.annotate_text = ('Rydot infotech Attendance System_'+DATE_TIME)
			gCamera.capture(abs_path+'Image/image%s.jpg'% count) 
			count+=1
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: MessageQueueSendFile()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This function will send video(n).h264 raw file path using  
#				  to MessageQueueRecFile() function.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def MessageQueueSendFile(MQSendPath):
	global InputFile
	print ('MsgQueue_Send_Count:%d'% giVidCount)
	InputFile = (MQSendPath) #Raw file video(n).h264 path

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue='key%s'% giVidCount) # Generate Key(n)	
	channel.basic_publish(exchange='', routing_key='key%s'% giVidCount, body=InputFile) #Send body as a video(n).h264 file path
	print('[x] Sent_path : %s' %(InputFile))
	print('[x] Key:%s' %(giVidCount))
	gOut.writerow([DATE_TIME,'MessageQueue: SendFilePath','%s' %InputFile])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: MessageQueueReceiveFile()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This function Receive generated raw.h264 file path and converting 
#				  raw.h264 to .mp4 video file and Call Videoduration() function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def MessageQueueReceiveFile():
	global giVidCount
	print ('MsgQueue_Rec_Count:%d'% giVidCount)
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost')) #Connection establish with RabbitMQ server
	channel = connection.channel()
	channel.queue_declare(queue=('key%s' %giVidCount)) #Generate Key

	def callback(ch, method, properties, body): #callback function is called by the Pika library. 
			print(" [x] Received %r" % body) #body argument collect message will print on the screen. 
			ch.stop_consuming() 
			MQRecPath = body
			print(" [x] data %r" % MQRecPath) # Get raw video path in MQRecPath buffer 

			if DEFINE_MODE == 0: #For Image Mode
				SendData(MQRecPath)
				giVidCount += 1
			if DEFINE_INTERATION == 1: #For Video Mode
				gOut.writerow([DATE_TIME,'MessageQueue: ReceiveFilePath','%s' %MQRecPath])
				os.system('MP4Box -fps 30 -add '+MQRecPath+' outfile.mp4') # raw.h264 to .mp4 Conversion
				time.sleep(1)
				os.system('cp outfile.mp4 MP4_Video/VID_%d.mp4' %giVidCount) # Copy current outfile.mp4 to number of VID_(n).mp4 
				gOut.writerow([DATE_TIME,'MP4 File Generated','MP4_Video/VID_%d.mp4' %giVidCount])
				VideoTimeDuration() #This Function will call for check Video time duration.

	channel.basic_consume(callback,				# Particular callback function should receive messages from our Key.
                      queue=('key%s' %giVidCount),
                      no_ack=True)
	print('[x] Key:%s' %(giVidCount))
	print(' [*] Waiting for messages. To exit press CTRL+C')
	channel.start_consuming() # Never-ending loop that waits for data and runs callbacks whenever necessary.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: DoorEventInterrupt()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Interrupt Service Routine. 
#				  ISR affected when Door posion is Open.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def DoorEventInterrupt():
	global giFlag
	giFlag = 1
	gOut.writerow([DATE_TIME,'Interrupt Event Occured'])
	print ('In ISR')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Loop()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Function will monitor Door position and capture Video and 
#				  send video path using MessageQueueSendFile()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def VideoLoop():
	while True:  
            
			#print wiringpi.digitalRead(READ_SWITCH)
			time.sleep(0.2)	
			global giFlag
			global giCount
			#print ('flag %s' %giFlag)
			#print ('count %s' %giCount)				
			print ('giVidCount %s' %giVidCount)
			if wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1:   
					gOut.writerow([DATE_TIME,'Door Position','Open'])
					print ('OPEN')
					CaptureVideo()
					MessageQueueSendFile(MQ_VIDEO_PATH)
			else:
				print ('CLOSE')
				gOut.writerow([DATE_TIME,'Door Position','Close'])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Loop()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Function will monitor Door position and capture Image and 
#				  send image path using MessageQueueSendFile()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def ImageLoop():
			print wiringpi.digitalRead(READ_SWITCH)
			time.sleep(0.2)	
			global giFlag
			global giInteration
			global giCount
			print ('flag %s' %giFlag)
			print ('count %s' %giCount)				
			print ('In Loop')
			if giFlag == 1:   
				for giInteration in range(ENTRY_IMAGES):
					gOut.writerow(['Door Position','Open'])
					time.sleep(0.2)	
					CaptureImage()
					MessageQueueSendFile(MQ_IMAGE_PATH)
					print ('Loop %s' %giInteration)	
					if giInteration <= (ENTRY_IMAGES - 1):
						giFlag = 0
			else:
				gOut.writerow(['Door Position','Close'])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: DoorEventThread()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Generate Video and Send Video path using message queue 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def DoorEventThread():
	while True:
		print("In thread1")
		if DEFINE_MODE == 0:
			ImageLoop()	
		if DEFINE_MODE == 1:
			VideoLoop()
		if flag == 1:
			break
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: VideoUploadThread()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Receive Video path using message queue 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def UploadThread():
    	while True: 
			print("In thread2")
			MessageQueueReceiveFile()
			if flag == 1:
				break

def InitThread():
	#Create Threads 
	gOut.writerow([DATE_TIME,'Create threads'])
	t1 = threading.Thread(target=UploadThread, args=())	
	t2 = threading.Thread(target=DoorEventThread, args=())
	#Start DoorEventThread
	gOut.writerow([DATE_TIME,'Start VideoUpload Thread'])
	t1.start()
	#Start ImageUploadThread
	gOut.writerow([DATE_TIME,'Start DoorEvent Thread']) 
	t2.start()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: main()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is main function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':
	global fpLogFile
	Setup()	
	InitThread()
	killer = GracefulKill()
	while True:
		time.sleep(1)
		subprocess.call(['./wifi_check.sh'])
		if killer.kill_now:
			flag=1
			fpLogFile.close()
			break
	iPid = os.getpid()
	os.system('kill -9 %s' %iPid)

	gOut.writerow([DATE_TIME,'Terminate Process by Signal'])
	# wait until DoorEventThread is completely executed 
	t1.join()
	# wait until ImageUploadThread is completely executed
	t2.join()
	#print "All threads stopped."

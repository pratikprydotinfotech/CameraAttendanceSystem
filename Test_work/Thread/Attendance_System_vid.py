#-------------------------------------------------------------------------------------------------------------------------------------
#File Name 		   : Attendance_System.py 
#Author(s) 		   : Pratik Panchal
#Purpose of module : Attendance system provide some features like Record Video when door will open,
# 					 process on video and video will upload on server. 
#Date of creation  : 22/11/2018
#-------------------------------------------------------------------------------------------------------------------------------------
import threading, signal
import pika
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
global giFlag 				  # globally define flag
giFlag = 1

global gOut

global giCount
giCount=0

global giTimeCount
giTimeCount=0

global gfDurationBuf
gfDurationBuf = 0

global SendCount
SendCount = 0
global RecCount
RecCount = 0
global giVidCount
giVidCount = 0
global InputFile
global VideoRecPath

abs_path = os.getcwd()
abs_path = abs_path+'/'

url = "http://192.168.0.4:9128/upload"
DEFINE_INTERATION = 3 # Interation for Server busy status and Time out Status 
ENTRY_IMAGES = 7 # Door open then 5 images will capture and send on server 
READ_SWITCH = 23 # Reed_switch GPIO use 23 


LOG_PATH = abs_path+"Test_Log" # Log directory generation path
MP4_PATH = abs_path+"outfile.mp4" # Output .mp4 file generation path
LOG_FILE_PATH = abs_path+"Test_Log/log.csv" #log.csv file generation path
RAW_FILE_PATH = abs_path+'Raw_Video' # Raw .h264 file generation path

# define user-defined exceptions for Server Busy
class Error(Exception):
   """Base class for other exceptions"""
   pass

class ServerBusyError(Error):

   pass

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
	os.system('rm -rf Raw_Video') # Old Test_Log directory remove when System will restart 
	os.mkdir( RAW_FILE_PATH, 0755 )  # New Test_Log directory generate
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
	global giVidCount
	ucVideoDuration = str(check_output('ffprobe -i  "'+ (abs_path+'VID_%s.mp4' %giVidCount) +'" 2>&1 |grep "Duration"',shell=True)) 

	ucVideoDuration = ucVideoDuration.split(",")[0].split("Duration:")[1].strip()

	h, m, s = ucVideoDuration.split(':')
	gfDurationBuf = int(h) * 3600 + int(m) * 60 + float(s)

	print(gfDurationBuf)
	gOut.writerow([('Time Duration_%s' %(str(datetime.now()))),gfDurationBuf])

	if gfDurationBuf <= 1.0:
		os.system('rm -rf VID_%d.mp4' %giVidCount)
		gOut.writerow([('Discard Video_%s' %(str(datetime.now()))),'VID_%d.mp4' %giVidCount])
		os.system('rm -rf outfile.mp4')
	else:
		SendData()
		os.system('rm -rf outfile.mp4')
		gOut.writerow([('Store Video_%s' %(str(datetime.now()))),'VID_%d.mp4' %giVidCount])
	giVidCount += 1
		

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
	global giVidCount

	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 		#Create pycurl instance 
	c.setopt(c.URL, url) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	#testing
	#~~~~~~~~~~~~~~~~~~~~
	send = [("file", (c.FORM_FILE, abs_path+'VID_%s.mp4' %giVidCount)),("timestamp",str(datetime.now())),] # Sending Camera generated file and timestamp in the form of "Form data" formate
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
		loop()
    
	c.close() 
	
	ucContent = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
	print (ucContent)
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
			loop()
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
			global SendCount
			gCamera.annotate_text = "Rydot infotech Attendance System"
			gCamera.brightness = 50
			gCamera.resolution = (1024, 768) 
			gCamera.framerate = 30
			gOut.writerow(['Video_Record_Start_%s' %(str(datetime.now()))])
			gCamera.start_recording(abs_path+'Raw_Video/video%s.h264' %giVidCount)
			gOut.writerow(['Raw .h264 file generated_%s' %(str(datetime.now()))])	

			while wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1:  
					gCamera.wait_recording()
					#time.sleep(1)
					#print ('Recording wait')
						
			gCamera.stop_recording()
			gOut.writerow(['Video_Record_Stop_%s' %(str(datetime.now()))])	
			

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: MessageQueueSendFile
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Door event thread generated file will send using 
#				  MessageQueueSendFile() function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def MessageQueueSendFile():
	global SendCount
	global InputFile
	print ('MsgQueue_Send_Count:%d'% giVidCount)
	InputFile = ('Raw_Video/video%s.h264'% (giVidCount))

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue='key%s'% giVidCount)	
	channel.basic_publish(exchange='', routing_key='key%s'% giVidCount, body=InputFile)
	print('[x] Sent_path : %s' %(InputFile))
	print('[x] Key:%s' %(giVidCount))
	gOut.writerow([('MessageQueue:InputFile_Sent_%s' %(str(datetime.now())))])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: MessageQueueReceiveFile
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Image process thread Receive File and process on Image 
#				  MessageQueueReceiveFile() function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def MessageQueueReceiveFile():
	global RecCount
	global giVidCount
	global SendCount
	global RecCount
	print ('MsgQueue_Rec_Count:%d'% giVidCount)
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue=('key%s' %giVidCount))

	def callback(ch, method, properties, body):
			print(" [x] Received %r" % body)
			ch.stop_consuming()
			VideoRecPath = body
			print(" [x] data %r" % VideoRecPath) 
			
			print ('MP4Box -fps 30 -add '+VideoRecPath+' outfile.mp4')
			os.system('MP4Box -fps 30 -add '+VideoRecPath+' outfile.mp4')
			os.system('cp outfile.mp4 VID_%d.mp4' %giVidCount)
			gOut.writerow(['MP4 file generated_%s' %(str(datetime.now()))])	
			VideoTimeDuration()
	
	channel.basic_consume(callback,
                      queue=('key%s' %giVidCount),
                      no_ack=True)
	print('[x] Key:%s' %(giVidCount))
	print(' [*] Waiting for messages. To exit press CTRL+C')
	channel.start_consuming()
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
	while True:  
            
			print wiringpi.digitalRead(READ_SWITCH)
			time.sleep(0.2)	
			global giFlag
			global giCount
			print ('flag %s' %giFlag)
			print ('count %s' %giCount)				
			print ('giVidCount %s' %giVidCount)
			if wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1:   
					gOut.writerow([('Door Position_%s' %(str(datetime.now()))),'Open'])
					print ('OPEN')
					#time.sleep(0.2)	
					CaptureVideo()
					MessageQueueSendFile()
					
					#giFlag = 0
			else:
				print ('CLOSE')
				#os.system('rm -rf outfile.mp4 video.h264')

			#	gOut.writerow([('Door Position_%s' %(str(datetime.now()))),'Close'])
			#	giFlag = 0
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: DoorEventThread()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Generate Image and Send image using message queue 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def DoorEventThread():
	while True:
		print("In thread1")
		Loop()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: ImageUploadThread()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Catch Image through message queue and Send it on server 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def VideoUploadThread():
    	while True: 
			print("In thread2")
			MessageQueueReceiveFile()
			
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: main()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is main function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':
 
	Setup()	
	#Create Threads 
	t1 = threading.Thread(target=DoorEventThread, args=())	
	t2 = threading.Thread(target=VideoUploadThread, args=())
	#Start DoorEventThread
	t1.start()
	#Start ImageUploadThread 
	t2.start()
	# wait until DoorEventThread is completely executed 
	t1.join()
	# wait until ImageUploadThread is completely executed
	t2.join()

print "All threads stopped."

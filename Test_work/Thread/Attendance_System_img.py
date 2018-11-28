#-------------------------------------------------------------------------------------------------------------------------------------
#File Name 		   : Attendance_System.py (Threading & Message_Queue)
#Author(s) 		   : Pratik Panchal
#Purpose of module : Attendance system provide some features like capture image when door will open,
# 					 process on image and image will upload on server. 
#Date of creation  : 16/11/2018
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
from picamera import PiCamera # pi camera function use from picamera module
from time import sleep 		  # sleep function use from time library module      

global giFlag 				  # globally define flag
giFlag = 1

global gOut

global giCount
giCount=0

global giTimeCount
giTimeCount=0

global giLooper
giLooper = 0 

global count # testing
count = 0  # testing

global SendCount
SendCount = 0
global RecCount
RecCount = 0
global InputFile
global ImageRecPath
abs_path = os.getcwd()
abs_path = abs_path+'/'

url = "http://192.168.0.4:9128/upload"
DEFINE_INTERATION = 3 # Interation for Server busy status and Time out Status 
ENTRY_IMAGES = 1 # Door open then 5 images will capture and send on server 
READ_SWITCH = 23 # Reed_switch GPIO use 23 
LOG_PATH = abs_path+"Test_Log"
IMG_PATH = abs_path+"Image" 
LOG_FILE_PATH = abs_path+"Test_Log/log.csv"
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
	os.system('rm -rf Image') # Old Test_Log directory remove when System will restart 
	os.mkdir( LOG_PATH, 0755 )  # New Test_Log directory generate
	os.mkdir( IMG_PATH, 0755 )  # Image directory generate
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
	gOut.writerow(['Setup Function Intialize\n'])
	wiringpi.wiringPiSetupGpio()  
	wiringpi.pinMode(READ_SWITCH, 0) # Reed switch GPIO 23 as a Input direction     
	wiringpi.pullUpDnControl(READ_SWITCH,1) # e.g 1 - PullDown , 0 - PullUp
	wiringpi.wiringPiISR(READ_SWITCH, wiringpi.INT_EDGE_RISING, DoorEventInterrupt) # Interrupt ISR init by using Edge triggering in Rising edge 
	gCamera = PiCamera() # camera return : <picamera.camera.PiCamera object at 0x75a382a0>
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: SendData
# @ Parameter   : ImageRecPath
# @ Return      : void
# @ Brief       : This Function is Sending Form data on server 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def SendData(ImageRecPathh): 
	global giCount
	global giTimeCount
	global giFlag
	global count # testing
	global SendCount
	global RecCount
	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 		#Create pycurl instance 
	c.setopt(c.URL, url) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	print ('[x] buffer %s' %ImageRecPathh) 
	send = [("file", (c.FORM_FILE,ImageRecPathh)),("timestamp",str(datetime.now())),] # Sending Camera generated file and timestamp in the form of "Form data" formate
	c.setopt(c.HTTPPOST,send) 		   # POST "form data" on server
	c.setopt(pycurl.CONNECTTIMEOUT, 1) # Timeout 1 second
	
# Try and Exception for Server Timeout 

	try:
		c.perform()
		c.setopt(c.URL, url)
		
	except pycurl.error, error:
		errno, errstr = error
		gOut.writerow(['An error occurred', '%s' %errstr])
		print 'An error occurred: ', errstr  # An error occured : Connection timed out after 1001 milliseconds
		giTimeCount+=1
		if giTimeCount >= DEFINE_INTERATION: # 3 times time out interation check then flag will be zero and will go in ideal state 
				giTimeCount = 0
				giFlag = 0
		Loop()
    
	c.close() 
	
	ucContent = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
	
	j = json.loads(ucContent) 		# Decode json data
	
	print ('value %s' % ucContent)
# Server status maintain in Log file.
	
	if j['success'] == False:
	 gOut.writerow(['Send Data on Server','Fail'])
	 gOut.writerow(['value %s' % ucContent])
	else:
	 gOut.writerow(['Send Data on Server','Sucess'])
	 gOut.writerow(['value %s' % ucContent])
 
# Try and Exception for Status of Server 

	try:

			if j['success'] == False:
				raise ServerBusyError
			else:
				gOut.writerow(['Server is Healthy'])

	except ServerBusyError:
			gOut.writerow(['Server Busy'])
			giCount+=1
			print ('Server Busy')
			print ('count %s' %giCount)
			if giCount >= DEFINE_INTERATION:
				giCount = 0
				gOut.writerow(['Server Busy overflaw'])
				giFlag = 0
			Loop()
	
	SendCount+=1
	RecCount+=1
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
			gCamera.capture(abs_path+'Image/image%s.jpg'% count) 
			count+=1
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
	print ('MsgQueue_Send_Count:%d'% SendCount)
	InputFile = (abs_path+'Image/image%s.jpg'% (SendCount))

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue='key%s'% SendCount)	
	channel.basic_publish(exchange='', routing_key='key%s'% SendCount, body=InputFile)
	print('[x] Sent_path : %s' %(InputFile))
	print('[x] Key:%s' %(SendCount))
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
	print ('MsgQueue_Rec_Count:%d'% RecCount)
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue=('key%s' %RecCount))

	def callback(ch, method, properties, body):
			print(" [x] Received %r" % body)
			ch.stop_consuming()
			ImageRecPath = body
			print(" [x] data %r" % ImageRecPath) 
			SendData(ImageRecPath) # Send data on server
	
	channel.basic_consume(callback,
                      queue=('key%s' %RecCount),
                      no_ack=True)
	print('[x] Key:%s' %(RecCount))
	# os.system('rm outputimage.jpg')
	print(' [*] Waiting for messages. To exit press CTRL+C')
	channel.start_consuming()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: DoorEventInterrupt
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Interrupt Service Routine
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def DoorEventInterrupt():
	global giFlag
	giFlag = 1
	gOut.writerow(['In Interrupt','Door Event Init'])
	print ('In ISR')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Loop
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is monitor Door position and accordingly do action
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Loop():
  
			print wiringpi.digitalRead(READ_SWITCH)
			time.sleep(0.2)	
			global giFlag
			global giLooper
			global giCount
			print ('flag %s' %giFlag)
			print ('count %s' %giCount)				
			print ('In Loop')
			if wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1:   
				for giLooper in range(ENTRY_IMAGES):
					gOut.writerow(['Door Position','Open'])
					time.sleep(0.2)	
					CaptureImage()
					MessageQueueSendFile()
					print ('Loop %s' %giLooper)	
					if giLooper <= (ENTRY_IMAGES - 1):
						giFlag = 0
			else:
				gOut.writerow(['Door Position','Close'])
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
def ImageUploadThread():
	global buffer
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
	t2 = threading.Thread(target=ImageUploadThread, args=())
	#Start DoorEventThread
	t1.start()
	#Start ImageUploadThread 
	t2.start()
	# wait until DoorEventThread is completely executed 
	t1.join()
	# wait until ImageUploadThread is completely executed
	t2.join()

print "All threads stopped."

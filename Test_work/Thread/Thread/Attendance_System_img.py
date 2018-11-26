#-------------------------------------------------------------------------------------------------------------------------------------
#File Name 		   : Attendance_System.py
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

RUNNING = True
threads = []

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

global InputFile
global OutputFile

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

def monitoring(tid, itemId=None, threshold=None):
    global RUNNING
    while(RUNNING):
        #print "PID=", os.getpid(), ";id=", tid

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

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Log_File_Generation
# @ Parameter 	: void
# @ Return 		: void
# @ Brief 		: This Function is Genrate Log data file
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Log_File_Generation():
	global gOut
	os.system('rm -rf Test_Log') # Old Test_Log directory remove when System will restart 
	os.system('rm -rf Image') # Old Test_Log directory remove when System will restart 
	os.mkdir( LOG_PATH, 0755 )  # New Test_Log directory generate
	os.mkdir( IMG_PATH, 0755 ) 
	gOut = csv.writer(open(LOG_FILE_PATH,"w"), delimiter=',' , quoting=csv.QUOTE_ALL) #log.csv file generate in Test_Log directory 
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: setup
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is initialize GPIO ,Camera , Log data file
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Setup():
	global gCamera
	Log_File_Generation()
	gOut.writerow(['Setup Function Intialize\n'])
	wiringpi.wiringPiSetupGpio()  
	wiringpi.pinMode(READ_SWITCH, 0) # Reed switch GPIO 23 as a Input direction     
	wiringpi.pullUpDnControl(READ_SWITCH,1) # e.g 1 - PullDown , 0 - PullUp
	wiringpi.wiringPiISR(READ_SWITCH, wiringpi.INT_EDGE_RISING, Door_event) # Interrupt ISR init by using Edge triggering in Rising edge 
	gCamera = PiCamera() # camera return : <picamera.camera.PiCamera object at 0x75a382a0>
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Send_data
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Sending Form data on server 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def Send_data(): 
	global giCount
	global giTimeCount
	global giFlag
	global count # testing
	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 		#Create pycurl instance 
	c.setopt(c.URL, url) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	#testing
	#~~~~~~~~~~~~~~~~~~~~
	img = ("Image/image%s.jpg" % (count - 1)) 
	send = [("file", (c.FORM_FILE, abs_path+img)),("timestamp",str(datetime.now())),]
	#~~~~~~~~~~~~~~~~~~~~
	#send = [("file", (c.FORM_FILE, "image.jpg")),("timestamp",str(datetime.now())),] # Sending Camera generated file and timestamp in the form of "Form data" formate
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
					 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: capture_image
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Capturing Image 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~		 
def capture_image():
			global count
			gOut.writerow(['Capture Image','Sucess'])
			#gCamera.capture(IMG_PATH)
			gCamera.framerate = 15
			#testing
			#~~~~~~~~~~~~~~~~~~~~
			gCamera.capture(abs_path+'Image/image%s.jpg'% count) 
			count+=1
			#~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: MessageQueueSendFile
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Door event thread generated file will send using 
#				  MessageQueueSendFile() function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	

def MessageQueueSendFile():
	global count
	global InputFile
	print ('MsgQueue_Send_Count:%d'% count)
	fpInputFile = open(abs_path+'Image/image%s.jpg'% count,"rb")
	InputFile = fpInputFile.read()

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()

	channel.queue_declare(queue='key%s'% count)	
	channel.basic_publish(exchange='', routing_key='key%s'% count, body=InputFile)
	print(" [x] Sent 'Test'")
	gOut.writerow([('MessageQueue:InputFile_Sent_%s' %(str(datetime.now())))])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: MessageQueueReceiveFile
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Image process thread Receive File and process on Image 
#				  MessageQueueReceiveFile() function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def MessageQueueReceiveFile():
	global count
	global OutputFile
	print ('MsgQueue_Rec_Count:%d'% count)
	fpOutputFile = open("outputimage.jpg","wb")
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue='key%s'% count)	

	def callback(ch, method, properties, body):
    		fpOutputFile.write(body)
    		fpOutputFile.close()
    #print(" [x] Received %r" % body)
	channel.basic_consume(callback,
                      queue='key%s'% count,
                      no_ack=True)

	print(' [*] Waiting for messages. To exit press CTRL+C')
	channel.start_consuming()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Door_event
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Interrupt Service Routine
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def Door_event():
	global giFlag
	giFlag = 1
	gOut.writerow(['In Interrupt','Door Event Init'])
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
			global giLooper
			global giCount
			print ('flag %s' %giFlag)
			print ('count %s' %giCount)				
			print ('In Loop')
			if wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1:   
				for giLooper in range(ENTRY_IMAGES):
					gOut.writerow(['Door Position','Open'])
					time.sleep(0.2)	
					capture_image()
					MessageQueueSendFile():
					#Send_data()
					print ('Loop %s' %giLooper)	
					if giLooper <= (ENTRY_IMAGES - 1):
						giFlag = 0
			else:
				gOut.writerow(['Door Position','Close'])
			#gOut.writerow(['Door Position','Close'])
			#gOut.writerow(['Flag','%s' %giFlag])
			#gOut.writerow(['count', '%s' %giCount])
			#gOut.writerow(['GPIO','%d' % wiringpi.digitalRead(READ_SWITCH)])
def fun2():
		print "In fun2 >>>>"

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

    ImageProcessThread = threading.Thread(target=monitoring, args=(2,), kwargs={'itemId':'2', 'threshold':60})
    ImageProcessThread.start()
    threads.append(ImageProcessThread)

    while(RUNNING):
        print "Main program is sleeping."
        time.sleep(60)
    for thread in threads:
        thread.join()

print "All threads stopped."

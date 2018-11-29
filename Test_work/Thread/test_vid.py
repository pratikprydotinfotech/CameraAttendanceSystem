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

global giVidCount
giVidCount = 0

global InputFile
global VideoRecPath

abs_path = os.getcwd()
abs_path = abs_path+'/'

url = "http://192.168.0.4:9128/upload"
DEFINE_INTERATION = 3 # Interation for Server busy status and Time out Status 
READ_SWITCH = 23 # Reed_switch GPIO use 23 


LOG_DIR_PATH = abs_path+"Test_Log" # Log directory generation path
MP4_DIR_PATH = abs_path+"MP4_Video" # Output .mp4 file generation path
LOG_FILE_PATH = abs_path+"Test_Log/log.csv" #log.csv file generation path
RAW_DIR_PATH = abs_path+'Raw_Video' # Raw .h264 file generation path

# define user-defined exceptions for Server Busy
class Error(Exception):
   """Base class for other exceptions"""
   pass

class ServerBusyError(Error):

   pass

global flag
flag = 0
global f

class GracefulKill:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True
  print "End of the program. I was killed gracefully :)"
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: LogFileGeneration()
# @ Parameter 	: void
# @ Return 		: void
# @ Brief 		: This Function is Genrate Log and Raw Video directory
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def LogFileGeneration():
	global gOut
	global f
	os.system('rm -rf Test_Log') # Old Test_Log directory remove when System will restart 
	os.mkdir( LOG_DIR_PATH, 0755 )  # New Test_Log directory generate
	os.system('rm -rf Raw_Video') # Old Test_Log directory remove when System will restart 
	os.mkdir( RAW_DIR_PATH, 0755 )  # New Test_Log directory generate
	os.system('rm -rf MP4_Video') # Old Test_Log directory remove when System will restart 
	os.mkdir( MP4_DIR_PATH, 0755 )  # New Test_Log directory generate
	
	f = open(LOG_FILE_PATH,"w")
	gOut = csv.writer(f, delimiter=',' , quoting=csv.QUOTE_ALL) #log.csv file generate in Test_Log directory 
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
	gOut.writerow([('Setup Function Intialize_%s' %(str(datetime.now())))])
	wiringpi.wiringPiSetupGpio() # Initialize wiring GPIO   
	wiringpi.pinMode(READ_SWITCH, 0) # Reed switch GPIO 23 as a Input direction     
	wiringpi.pullUpDnControl(READ_SWITCH,1) # e.g 1 - PullDown , 0 - PullUp
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
	gOut.writerow([('Time Duration_%s' %(str(datetime.now()))),gfDurationBuf])

	if gfDurationBuf <= 1.0:
		os.system('rm -rf MP4_Video/VID_%d.mp4' %giVidCount)
		gOut.writerow([('Discard Video_%s' %(str(datetime.now()))),'MP4_Video/VID_%d.mp4' %giVidCount])
		os.system('rm -rf outfile.mp4')
	else:
		SendData()
		os.system('rm -rf outfile.mp4')
		gOut.writerow([('Store Video_%s' %(str(datetime.now()))),'MP4_Video/VID_%d.mp4' %giVidCount])
	giVidCount += 1
		

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: SendData()
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
	send = [("file", (c.FORM_FILE,abs_path+'MP4_Video/VID_%s.mp4' %giVidCount)),("timestamp",str(datetime.now())),] # Sending Camera generated file and timestamp in the form of "Form data" formate
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
# @Function 	: CaptureVideo()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Capturing Video when Door event occur.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~		 
def CaptureVideo():		
			global giFlag
			global giVidCount
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
# @Function 	: MessageQueueSendFile()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This function will send video(n).h264 raw file path using  
#				  to MessageQueueRecFile() function.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def MessageQueueSendFile():
	global InputFile
	print ('MsgQueue_Send_Count:%d'% giVidCount)
	InputFile = ('Raw_Video/video%s.h264'% (giVidCount)) #Raw file video(n).h264 path

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue='key%s'% giVidCount) # Generate Key(n)	
	channel.basic_publish(exchange='', routing_key='key%s'% giVidCount, body=InputFile) #Send body as a video(n).h264 file path
	print('[x] Sent_path : %s' %(InputFile))
	print('[x] Key:%s' %(giVidCount))
	gOut.writerow([('MessageQueue:SendFilePath_Sent_%s' %(str(datetime.now()))),'%s' %InputFile])
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
			VideoRecPath = body
			print(" [x] data %r" % VideoRecPath) # Get raw video path in VideoRecPath buffer 
			gOut.writerow([('MessageQueue:ReceiveFilePath_%s' %(str(datetime.now()))),'%s' %VideoRecPath])
			os.system('MP4Box -fps 30 -add '+VideoRecPath+' outfile.mp4') # raw.h264 to .mp4 Conversion
			time.sleep(1)
			os.system('cp outfile.mp4 MP4_Video/VID_%d.mp4' %giVidCount) # Copy current outfile.mp4 to number of VID_(n).mp4 
			gOut.writerow(['MP4 file generated_%s' %(str(datetime.now())),'MP4_Video/VID_%d.mp4' %giVidCount])	
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
	gOut.writerow([('In Interrupt_%s' %(str(datetime.now()))),'Door Event Init'])
	print ('In ISR')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Loop()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Function will monitor Door position and capture Video and 
#				  send video path using MessageQueueSendFile()
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
					CaptureVideo()
					MessageQueueSendFile()
			else:
				print ('CLOSE')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: DoorEventThread()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Generate Video and Send Video path using message queue 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def DoorEventThread():
	while True:
		print("In thread1")
		Loop()
		if flag == 1:
			break
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: VideoUploadThread()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Receive Video path using message queue 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def VideoUploadThread():
    	while True: 
			print("In thread2")
			MessageQueueReceiveFile()
			if flag == 1:
				break
			
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: main()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is main function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':
	global f
	Setup()	
	#Create Threads 
	t1 = threading.Thread(target=VideoUploadThread, args=())	
	t2 = threading.Thread(target=DoorEventThread, args=())
	#Start DoorEventThread
	t1.start()
	#Start ImageUploadThread 
	t2.start()
	killer = GracefulKill()
	while True:
		print("In loop")
		print os.getpid()
		time.sleep(1)
		if killer.kill_now:
			flag=1
			f.close()
			break
	pid = os.getpid()
    
	os.system('kill -9 %s' %pid)
	gOut.writerow([('Termination by Signal_%s' %(str(datetime.now())))])
	# wait until DoorEventThread is completely executed 
	t1.join()
	# wait until ImageUploadThread is completely executed
	t2.join()

print "All threads stopped."

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
from datetime import datetime as dt
from subprocess import check_output #check_output subprocess creating for VideoDuration() function
from picamera import PiCamera # pi camera function use from picamera module
from time import sleep 		  # sleep function use from time library module
import objectpath #objectpath is useful module for decode Json objects
import Adafruit_CharLCD as LCD # 16x2 LCD Supported Library import

# Raspberry Pi pin configuration:
lcd_rs        = 25  # Note this might need to be changed to 21 for older revision Pi's.
lcd_en        = 24
lcd_d4        = 23
lcd_d5        = 17
lcd_d6        = 18
lcd_d7        = 22
lcd_backlight = 4

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

#Define LCD Pin Parameters
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                           lcd_columns, lcd_rows, lcd_backlight)

global giFlag 				  # globally define Interrupt flag
giFlag = 0

global giOpenFlag 			  # globally define Open flag for monitor VideoLength duration
giOpenFlag = 0

global giKillFlag			  #Kill flag is use for terminate process abnormally or Signally
giKillFlag = 0

global fpLogFile			  #File pointer use to generate .csv Log File

global gOut					  #Object of .csv log file

global giCount				  #Counter identify Server status while Server Busy
giCount=0

global giTimeCount			  #Counter identify TimeOut of Server
giTimeCount=0

global gfDurationBuf		  #Video Duration value get in this buffer
gfDurationBuf = 0

global giVidCount			  #Counter provide different number of Image/Video for differentiate easily No. of Videos/Images   
giVidCount = 0

global count # testing
count = 0  # testing

global InputFile

global ImageRecPath
global VideoRecPath

global ucContent

global VideoLength
global ucMediaType

abs_path = os.getcwd()
abs_path = abs_path+'/'

#Url for data transfering on server 
url = "http://192.168.0.4:3000/upload"
register_url = 'http://192.168.0.4:9128/api/ams/public/devices/register'
configuration_url = 'http://192.168.0.4:9128/api/ams/public/devices/get-configuration'

#No. of event monitoring Macros
ENTRY_IMAGES = 1 # Door open then 5 images will capture and send on server 
DEFINE_INTERATION = 3 # Interation for Server busy status and Time out Status 

#GPIO for switching related Macro
READ_SWITCH = 0 # Reed_switch GPIO 

#Media Parameter Macros
BRIGHTNESS = 50 
RESOLUTION_H = 1024
RESOLUTION_W = 768
VIDEO_FRAMERATE = 30
IMAGE_FRAMERATE = 15
# Files related Macros
IMAGE_DIR_PATH = abs_path+"Image"
LOG_DIR_PATH = abs_path+"Test_Log" # Log directory generation path
MP4_DIR_PATH = abs_path+"MP4_Video" # Output .mp4 file generation path
LOG_FILE_PATH = abs_path+"Test_Log/log.csv" #log.csv file generation path
RAW_DIR_PATH = abs_path+'Raw_Video' # Raw .h264 file generation path
WIFI_FILE_PATH = '$(echo $(pwd)/Test_Log/WifiNetLog.csv)' # WifiConnectivity log file path
MP4_FILE_PATH = (abs_path+'MP4_Video/VID_%s.mp4' %giVidCount)
DATE_TIME = ('%s' %(str(dt.now())))
TIMEOUT_SEC = 1 # Server Time out e.g 1 Sec  



# define user-defined exceptions for Server Busy
class Error(Exception):
   """Base class for other exceptions"""
   pass

class ServerBusyError(Error):

   pass

class GracefulKill:
  global gOut
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: GetCpuId()
# @ Parameter 	: void
# @ Return 		: string
# @ Brief 		: This Function is Get Raspberry pi CPU ID
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def GetCpuId():
  # Extract serial from cpuinfo file
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    cpuserial = "ERROR000000000"
 
  return cpuserial
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
# @Function 	: LCDInit()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Initialise LCD by this function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def LCDInit():
# Initialize the LCD using the pins above.
	lcd.set_backlight(0)
	str_pad = " " * 16
	station = str_pad + 'Rydot Infotech Ltd.'
	for i in range (0, (len(station)+1)):
		lcd.clear()
		lcd_text = station[i:(i+16)]
		lcd.message(lcd_text)
		time.sleep(0.2)

	lcd.message('Rydot Info. Ltd.')
	time.sleep(2)	

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Setup()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is initialize GPIO ,Camera,Log and Raw Video directory
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Setup():
	global gCamera
	global giFlag
	global READ_SWITCH 
	LogFileGeneration() # Generate Log and Raw file Video Directory
	gOut.writerow([DATE_TIME,'Setup Function Intialize'])
	wiringpi.wiringPiSetupGpio() # Initialize wiring GPIO
	LCDInit()   
	GetConfiguration() # Get VideoLength duration and MediaType : Image/Video
	if ucMediaType == "image": # For Image
		giFlag = 0
		READ_SWITCH = 21
		wiringpi.pinMode(READ_SWITCH, 0) # Reed switch GPIO 21 as a Input direction     
		wiringpi.pullUpDnControl(READ_SWITCH,1) # e.g 1 - PullDown , 0 - PullUp
		wiringpi.wiringPiISR(READ_SWITCH, wiringpi.INT_EDGE_FALLING, DoorEventInterrupt) # Interrupt ISR init by using Edge triggering in Falling edge 
		lcd.clear()
		lcd.message('Ready to take\nPicture')
	if ucMediaType == "moving": # For Video
		giFlag = 0
		READ_SWITCH = 27
		wiringpi.pinMode(READ_SWITCH, 0) # Reed switch GPIO 27 as a Input direction     
		wiringpi.pullUpDnControl(READ_SWITCH,1) # e.g 1 - PullDown , 0 - PullUp
		wiringpi.wiringPiISR(READ_SWITCH, wiringpi.INT_EDGE_FALLING, DoorEventInterrupt) # Interrupt ISR init by using Edge triggering in Falling edge    
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
		SendData(abs_path+'MP4_Video/VID_%s.mp4' %giVidCount)
		os.system('rm -rf outfile.mp4')
		gOut.writerow([DATE_TIME,'Store_Video','MP4_Video/VID_%d.mp4' %giVidCount])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: VideoLengthLimit(seconds)
# @ Parameter 	: Seconds
# @ Return 		: void
# @ Brief 		: Record Video as per provide senconds in parameter
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def VideoLengthLimit(seconds):
	gOut.writerow([DATE_TIME,'VideoRecording Play',seconds])
	global gCamera
	global giOpenFlag
	start = time.time()
	time.clock()
	elapsed = 0
	while elapsed < seconds and (wiringpi.digitalRead(READ_SWITCH) == 0):
		elapsed = time.time() - start
		gCamera.wait_recording()
		time.sleep(1)
	giOpenFlag = 0
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: GetConfiguration()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Get VideoLength and MediaType : Image/Video  
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def GetConfiguration():
	global VideoLength
	global ucMediaType
	gOut.writerow([DATE_TIME,'Enter in GetConfiguration'])

	SerialNumber = GetCpuId()
	ApiKey = "key-de0bd007143f9e4fb9b628d52fb084f741f"
	ApiSecret = "secret-a0e0ab24569f819036014a587ff9f3b3"

	data = "{\"serialNumber\":"+('\"%s\"' %SerialNumber)+",\"apiKey\":"+('\"%s\",' %ApiKey)+"\"apiSecret\":"+('\"%s\"}' %ApiSecret)
	print data
	#data = '{"serialNumber":"1234567890","apiKey":"key-de0bd007143f9e4fb9b628d52fb084f741f","apiSecret":"secret-a0e0ab24569f819036014a587ff9f3b3"}'

	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 	#Create pycurl instance 
	c.setopt(c.URL, configuration_url) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	c.setopt(c.HTTPHEADER,['Content-Type: application/json'])

	c.setopt(pycurl.POSTFIELDS,data)

	# Try and Exception for Server Timeout 
	try:
		c.perform()
		c.setopt(c.URL, configuration_url)
	except pycurl.error, error:
		errno, errstr = error
		print 'An error occurred: ', errstr  # Conection refused Error
	c.close() 
		
	ucConfigData = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
	print (ucConfigData)
	j = json.loads(ucConfigData) 		# Decode json data

	jsonnn_tree = objectpath.Tree(j['item'])
	# Config = tuple(jsonnn_tree.execute('$..configuration'))
	# print Config
	video_length = tuple(jsonnn_tree.execute('$..videoLength'))
	Image_Type = tuple(jsonnn_tree.execute('$..imageType'))

	for VideoLength in video_length:
		print(VideoLength)
		gOut.writerow([DATE_TIME,'VideoLength','%d' %VideoLength])
	for ucMediaType in Image_Type:
		print(ucMediaType)
		gOut.writerow([DATE_TIME,'MediaType','%s' %ucMediaType])

	#ucMediaType = "image"

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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: SendData()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Sending Form data on server 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def SendData(RecPath): 
	global giCount
	global giTimeCount
	global giFlag
	global ucContent
	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 		#Create pycurl instance 
	c.setopt(c.URL, url) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	print ('[x] buffer %s' %RecPath) 
	send = [("file", (c.FORM_FILE,RecPath)),("timestamp",str(dt.now())),] # Sending Camera generated file and timestamp in the form of "Form data" formate
	c.setopt(c.HTTPPOST,send) 		   # POST "form data" on server
	c.setopt(pycurl.CONNECTTIMEOUT, 1) # Timeout 1 second
	
# Try and Exception for Server Timeout 

	try:
		c.perform()
		c.setopt(c.URL, url)
	except pycurl.error, error:
		errno, errstr = error
		gOut.writerow(['Timeout error occurred', '%s' %errstr])
		print 'Timeout error occurred: ', errstr  # An error occured : Connection timed out after 1001 milliseconds
		giTimeCount+=1
		if giTimeCount >= DEFINE_INTERATION: # 3 times time out interation check then flag will be zero and will go in ideal state 
				giTimeCount = 0
				giFlag = 0
		#Loop()
    
	c.close() 
	
	ucContent = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
	print ('value %s' % ucContent)
	try:
		j = json.loads(ucContent) 		# Decode json data
	except ValueError, e:
            print ('Json Error : %s'%e)

	
	if j['success'] == False:
	 gOut.writerow([DATE_TIME,'Send Data on Server','Fail'])
	 gOut.writerow(['value %s' % ucContent])
	else:
	 gOut.writerow([DATE_TIME,'Send Data on Server','Sucess'])
	 gOut.writerow(['value %s' % ucContent])
 
# Try and Exception for Status of Server 
	try:

			if j['success'] == False:
				raise ServerBusyError
			else:
				gOut.writerow([DATE_TIME,'Server is Healthy'])

	except ServerBusyError:
			gOut.writerow(['Server Busy'])
			giCount+=1
			print ('Server Busy')
			print ('count %s' %giCount)
			if giCount >= DEFINE_INTERATION:
				giCount = 0
				gOut.writerow([DATE_TIME,'Server Busy overflaw'])
				giFlag = 0
				lcd.clear()
				lcd.message('Server is Busy...')

	if ucMediaType == "image" and j['success'] == True:
		lcd.clear()
		lcd.message('Upload Sucessful\n***Thank you***')
		time.sleep(2)
		lcd.clear()
		lcd.message('Ready to take\nPicture')
	else:
		lcd.message('Server is Busy')
	gOut.writerow([DATE_TIME,'Door Position','Close'])
				 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: CaptureVideo()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Capturing Video when Door event occur.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~		 
def CaptureVideo():		
			global giFlag
			global giVidCount
			global ucMediaType
			global VideoLength
			global giOpenFlag
			gCamera.annotate_text = ('Rydot infotech Attendance System_'+DATE_TIME)
			gCamera.brightness = BRIGHTNESS
			gCamera.resolution = (RESOLUTION_H, RESOLUTION_W) 
			gCamera.framerate = VIDEO_FRAMERATE
			gOut.writerow([DATE_TIME,'Video_Recording_Start'])
			gCamera.start_recording(abs_path+'Raw_Video/video%s.h264' %giVidCount)
			gOut.writerow([DATE_TIME,'Raw .h264 file generated'])
			# if giOpenFlag == 1:  
			# 	VideoLengthLimit(VideoLength)
			while wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1:  
			    	VideoLengthLimit(VideoLength)
				if giOpenFlag == 0:
					break
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
			gCamera.framerate = IMAGE_FRAMERATE
			gCamera.resolution = (RESOLUTION_H, RESOLUTION_W) 
			gCamera.annotate_text = ('Rydot infotech Attendance System_'+DATE_TIME)
			gCamera.capture(abs_path+'Image/image%s.jpg'% count)
			gOut.writerow([DATE_TIME,'Capture_Image','Success'])
			gOut.writerow([DATE_TIME,'Capture_Image_path',abs_path+'Image/image%s.jpg'% count]) 
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
	global giVidCount
	print ('MsgQueue_Send_Count:%d'% giVidCount)
	InputFile = (MQSendPath) #Raw file video(n).h264 path

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue='key%s'% (giVidCount-1)) # Generate Key(n)	
	channel.basic_publish(exchange='', routing_key='key%s'% (giVidCount-1), body=InputFile) #Send body as a video(n).h264 file path
	print('[x] Sent_path : %s' %(InputFile))
	print('[x] Key:%s' %(giVidCount-1))
	gOut.writerow([DATE_TIME,'MessageQueue: SendFilePath','%s' %InputFile])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: MessageQueueReceiveFile
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Image process thread Receive File and process on Image 
#				  MessageQueueReceiveFile() function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def MessageQueueReceiveFile():
	global giVidCount
	global ImageRecPath
	global VideoRecPath
	print ('MsgQueue_Rec_Count:%d'% giVidCount)
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue=('key%s' %giVidCount))

	def callback(ch, method, properties, body):
			print(" [x] Received %r" % body)
			ch.stop_consuming()
			ImageRecPath = body
			VideoRecPath = body
			print(" [x] data %r" % ImageRecPath) 
			if ucMediaType == "image":
				SendData(ImageRecPath) # Send data on server
			if ucMediaType == "moving":
				gOut.writerow([DATE_TIME,'MessageQueue: ReceiveFilePath','%s' %VideoRecPath])
				os.system('MP4Box -fps 30 -add '+VideoRecPath+' outfile.mp4') # raw.h264 to .mp4 Conversion
				#time.sleep(1)
				os.system('cp outfile.mp4 MP4_Video/VID_%d.mp4' %giVidCount) # Copy current outfile.mp4 to number of VID_(n).mp4 
				gOut.writerow([DATE_TIME,'MP4 File Generated','MP4_Video/VID_%d.mp4' %giVidCount])
				VideoTimeDuration() #This Function will call for check Video time duration.

	channel.basic_consume(callback,
                      queue=('key%s' %giVidCount),
                      no_ack=True)
	print('[x] Key:%s' %(giVidCount))
	# os.system('rm outputimage.jpg')
	print(' [*] Waiting for messages. To exit press CTRL+C')
	giVidCount+=1
	channel.start_consuming()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: DoorEventInterrupt()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Interrupt Service Routine. 
#				  ISR affected when Door posion is Open.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def DoorEventInterrupt():
	global giFlag
	global giOpenFlag
	giFlag = 1
	giOpenFlag = 1
	gOut.writerow([DATE_TIME,'Interrupt Event Occured'])
	print ('In ISR')
	time.sleep(1)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: VideoLoop()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Function will monitor Door position and capture Video and 
#				  send video path using MessageQueueSendFile()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def VideoLoop():
	while True:  
			print wiringpi.digitalRead(READ_SWITCH)
			time.sleep(0.2)	
			global giFlag
			global giCount
			global giVidCount
			global giOpenFlag
			print ('video_Mode')
			print ('flag %s' %giFlag)
			#print ('count %s' %giCount)				
			print ('giOpenFlag %s' %giOpenFlag)
			print ('giVidCount %s' %giVidCount)
			lcd.clear()
			lcd.message('Rydot Info. Ltd.\n%s'%(str(dt.now())))
			if wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1 and giOpenFlag == 1:   
					gOut.writerow([DATE_TIME,'Door Position','Open'])
					print ('OPEN')
					CaptureVideo()
					MessageQueueSendFile(abs_path+'Raw_Video/video%s.h264'% (giVidCount))
					giFlag = 0
					giOpenFlag = 0
			elif wiringpi.digitalRead(READ_SWITCH) == 1:
					giFlag = 0
					giOpenFlag = 0
				# print ('CLOSE')
			# 	gOut.writerow([DATE_TIME,'Door Position','Close'])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: ImageLoop()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Function will monitor Door position and capture Image and 
#				  send image path using MessageQueueSendFile()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def ImageLoop():
			
			global giFlag
			global giInteration
			global giCount
			global giVidCount
			print wiringpi.digitalRead(READ_SWITCH)
			time.sleep(0.2)	
			print ('Image_Mode')
			print ('flag %s' %giFlag)
			print ('count %s' %giCount)
			print ('giVidCount %s' %giVidCount)				
			print ('In Loop')
			if giFlag == 1:   
				for giInteration in range(ENTRY_IMAGES):
					gOut.writerow([DATE_TIME,'Door Position','Open'])
					#time.sleep(0.2)	
					CaptureImage()
					MessageQueueSendFile(abs_path+'Image/image%s.jpg' % (giVidCount-1))
					print ('Loop %s' %giInteration)	
					if giInteration <= (ENTRY_IMAGES - 1):
						giFlag = 0
						gOut.writerow([DATE_TIME,'Door Position','Close'])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: DoorEventThread()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Generate Video and Send Video path using message queue 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def DoorEventThread():
	while True:
		print("In thread1")
		if ucMediaType == "image":
			ImageLoop()	
		if ucMediaType == "moving":
			VideoLoop()
		if giKillFlag == 1:
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
		if giKillFlag == 1:
			break

def InitThread():
	#Create Threads 
	gOut.writerow([DATE_TIME,'Create threads'])
	t1 = threading.Thread(target=UploadThread, args=())	
	t2 = threading.Thread(target=DoorEventThread, args=())
	#Start DoorEventThread
	gOut.writerow([DATE_TIME,'Start Upload Thread'])
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
		#time.sleep(1)
		subprocess.call(['./wifi_check.sh'])
		if killer.kill_now:
			giKillFlag=1
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

#-------------------------------------------------------------------------------------------------------------------------------------
#File Name 		   : Attendance_system.py 
#Author(s) 		   : Pratik Panchal
#Type 			   : In Entry
#Purpose of module : Attendance System provide two different modes choice (i) Image capturing for attendance 
#					 (ii) Video recording for In and Out. Both choice purely depend on Configuration URL.  					 
#Date of creation  : 22/11/2018
#Last Modification : 08/01/2019
#-------------------------------------------------------------------------------------------------------------------------------------
import threading, signal
import schedule
import urllib2
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

lcd_rs        = 7  # Note this might need to be changed to 21 for older revision Pi's.
lcd_en        = 8
lcd_d4        = 25
lcd_d5        = 24
lcd_d6        = 23
lcd_d7        = 18

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

#Define LCD Pin Parameters
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                           lcd_columns, lcd_rows)

global giRegFlag			  # User Registration Flag
giRegFlag = 0				  

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

global count
count = 0

global gfDurationBuf		  #Video Duration value get in this buffer
gfDurationBuf = 0

global giVidCount			  #Counter provide different number of Image/Video for differentiate easily No. of Videos/Images   
giVidCount = 0

global InputFile

global ImageRecPath
global VideoRecPath

global ucContent
ucContent = " "

global VideoLength
VideoLength = 8

global giSkipJson
giSkipJson = 0

global ucMediaType 		# Default MediaType is "image" 
ucMediaType = "static"

global iServerResponse 
iServerResponse = True

global giPendingCount
giPendingCount = 0

global giRegImgCount
giRegImgCount = 0

global giCurrentEmployee
giCurrentEmployee = 0

global giNumPhotos
giNumPhotos = 0

global giRegEmployeeName
giRegEmployeeName = 0

global RegImg
RegImg = 0

PendingImages = { }
Images = { }
abs_path = os.getcwd()+'/'
#abs_path = abs_path+'/'

#Url for data transfering on server

#url = ('http://0.0.0.0:%s' %(sys.argv[1])) # testing server

# 192.168.0.4:9128 (Test)
# 104.237.4.152:9128 (Live)
url = "http://104.237.4.152:9128/api/ams/devices/let-me-in"
RegisterUrl = "http://104.237.4.152:9128/api/ams/public/devices/register"
UserRegisterUrl = "http://104.237.4.152:9128/api/ams/public/devices/register-employee"
ConfigurationUrl = 'http://104.237.4.152:9128/api/ams/public/devices/get-configuration'
#EnableDisableUrl = 'http://104.237.4.152:9128/api/ams/public/devices/registration/enable'

#No. of event monitoring Macros
ENTRY_IMAGES = 1 # Door open then 1 images will capture and send on server 
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
REG_IMAGE_DIR_PATH = abs_path+"RegImage"
LOG_DIR_PATH = abs_path+"Test_Log" # Log directory generation path
MP4_DIR_PATH = abs_path+"MP4_Video" # Output .mp4 file generation path
LOG_FILE_PATH = abs_path+("Test_Log/log.csv") #log.csv file generation path
RAW_DIR_PATH = abs_path+'Raw_Video' # Raw .h264 file generation path
WIFI_FILE_PATH = '$(echo $(pwd)/Test_Log/WifiNetLog.csv)' # WifiConnectivity log file path
MP4_FILE_PATH = (abs_path+'MP4_Video/VID_%s.mp4' %giVidCount)

TIMEOUT_SEC = 1 # Server Time out e.g 1 Sec  
CONFIG_SCHEDULE_TIME = 5
# define user-defined exceptions for Server Busy
class Error(Exception):
   """Base class for other exceptions"""
   pass

class ServerBusyError(Error):

   pass
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: class GracefulKill
# @ Parameter 	: void
# @ Return 		: void
# @ Brief 		: Terminate to Main Thread by using SIGTERM Signal
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
	#os.system('rm -rf Test_Log')   # Test_Log directory remove 
	#os.mkdir( LOG_DIR_PATH, 0777 )  # New Test_Log directory generate
	os.system('rm -rf Raw_Video')  # Raw_Video directory remove 
	os.mkdir( RAW_DIR_PATH, 0777 )  # New Raw_Video directory generate
	os.system('rm -rf MP4_Video') # MP4_Video directory remove 
	os.mkdir( MP4_DIR_PATH, 0777 )  # New MP$_Video directory generate
	os.system('rm -rf Image') # Image directory remove 
	os.mkdir( IMAGE_DIR_PATH, 0777 )  # New MP$_Video directory generate
	os.system('rm -rf RegImage') # Registration directory remove 
	os.mkdir( REG_IMAGE_DIR_PATH, 0777 )  # Registration directory generate
	os.system('echo "Wifi_Internet_Connectivity_Status" >> '+WIFI_FILE_PATH)
	os.system('echo "Date&Time,Net_Connectivity" >> '+WIFI_FILE_PATH)
	fpLogFile = open(LOG_FILE_PATH,"a")
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
# @Function 	: ScrollingLCD(Name)
# @ Parameter   : String
# @ Return      : void
# @ Brief       : Char Scrolling LCD Display
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def ScrollingLCD(Name):
	# Initialize the LCD using the pins above.
	str_pad = " " * 16
	ScrollName = str_pad + Name
	for i in range (0, (len(ScrollName)+1)):
		lcd.clear()
		lcd_text = ScrollName[i:(i+16)]
		lcd.message(lcd_text)
		time.sleep(0.2)
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
	global ucMediaType
	global giOpenFlag
	LogFileGeneration() # Generate Log and Raw file Video Directory
	gOut.writerow([("**************************************************")])
	gOut.writerow([('%s' %(str(dt.now()))),'Setup Function Intialize'])
	gOut.writerow([("**************************************************")])
	wiringpi.wiringPiSetupGpio() # Initialize wiring GPIO
	LCDInit() 
	#EnableDisable()  
	SystemRegistration()
	#GetConfiguration() # Get VideoLength duration and MediaType : Image/Video
	if ucMediaType == "static": # For Image
		giFlag = 0
		READ_SWITCH = 21
		wiringpi.pinMode(READ_SWITCH, 0) # Reed switch GPIO 21 as a Input direction     
		wiringpi.pullUpDnControl(READ_SWITCH,1) # e.g 1 - PullDown , 0 - PullUp
		wiringpi.wiringPiISR(READ_SWITCH, wiringpi.INT_EDGE_FALLING, DoorEventInterrupt) # Interrupt ISR init by using Edge triggering in Falling edge 
		lcd.clear()
		lcd.message('Press Switch for\ntake a picture')
	if ucMediaType == "moving": # For Video
		giFlag = 0
		giOpenFlag = 0
		READ_SWITCH = 20
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
	gOut.writerow([('%s' %(str(dt.now()))),'Time_Duration',gfDurationBuf])
	if gfDurationBuf <= 1.0:
		os.system('rm -rf MP4_Video/VID_%d.mp4' %giVidCount)
		gOut.writerow([('%s' %(str(dt.now()))),'Discard_Video','MP4_Video/VID_%d.mp4' %giVidCount])
		os.system('rm -rf outfile.mp4')
	else:
		SendData(abs_path+'MP4_Video/VID_%s.mp4' %giVidCount)
		os.system('rm -rf outfile.mp4')
		gOut.writerow([('%s' %(str(dt.now()))),'Store_Video','MP4_Video/VID_%d.mp4' %giVidCount])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: VideoLengthLimit(seconds)
# @ Parameter 	: Seconds
# @ Return 		: void
# @ Brief 		: Record Video as per provide senconds in parameter
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def VideoLengthLimit(seconds):
	gOut.writerow([('%s' %(str(dt.now()))),'VideoRecording Play',(seconds-1)])
	global gCamera
	global giOpenFlag
	lcd.clear()
	lcd.message('Door is Open')
	start = time.time()
	time.clock()
	elapsed = 0
	while elapsed < (seconds-1) and (wiringpi.digitalRead(READ_SWITCH) == 0):
		elapsed = time.time() - start
		gCamera.wait_recording()
		time.sleep(1)
	giOpenFlag = 0
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Enable Disable Url for testing 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def EnableDisable():
	print "In EnableDisable Function"

	data = '{"employee":"5c2b3b88aaab8a3614e3c95e","numPhotos":10}'

	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 	#Create pycurl instance 
	c.setopt(c.URL, EnableDisableUrl) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	c.setopt(c.HTTPHEADER,['Content-Type: application/json','x-api-key: key-9acc61be5b2fe7f347908a9ced1f638f','x-api-secret: secret-835e6ed8dbcffcb7fa00a7b22be39e5e'])
	c.setopt(c.POSTFIELDS,data)
	c.perform()
	c.setopt(c.URL, EnableDisableUrl)
	c.close() 
	
	ucConfigData = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
	print ('Registration enable/Disable : %s' %ucConfigData)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: SystemRegistration()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : System registeration by ApiKey,ApiSecret,SerialNumber 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def SystemRegistration():
	global VideoLength
	global ucMediaType
	global ucContent
	lcd.clear()
	lcd.message('Registration\nStart')
	time.sleep(2)
	gOut.writerow([('%s' %(str(dt.now()))),'Enter in SystemRegistration'])

	SerialNumber = GetCpuId()
	#ApiKey = "key-de0bd007143f9e4fb9b628d52fb084f741f"
	#ApiSecret = "secret-a0e0ab24569f819036014a587ff9f3b3"

	ApiKey = "key-9acc61be5b2fe7f347908a9ced1f638f"
	ApiSecret = "secret-835e6ed8dbcffcb7fa00a7b22be39e5e"

	data = "{\"serialNumber\":"+('\"%s\"' %SerialNumber)+",\"apiKey\":"+('\"%s\",' %ApiKey)+"\"apiSecret\":"+('\"%s\"}' %ApiSecret)
	
	#data = '{"serialNumber":"1234567890","apiKey":"key-de0bd007143f9e4fb9b628d52fb084f741f","apiSecret":"secret-a0e0ab24569f819036014a587ff9f3b3"}'

	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 	#Create pycurl instance 
	c.setopt(c.URL, RegisterUrl) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	c.setopt(c.HTTPHEADER,['Content-Type: application/json'])
	c.setopt(pycurl.POSTFIELDS,data)

	# Try and Exception for Server Timeout 
	try:
		c.perform()
		c.setopt(c.URL, RegisterUrl)
	except pycurl.error, error:
		errno, errstr = error
		print 'An error occurred: ', errstr  # Conection refused Error
		lcd.clear()
		ScrollingLCD('Waiting for connection to complete setup')
		SystemRegistration()
		
	c.close() 
		
	ucConfigData = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
	print (ucConfigData)

	j = json.loads(ucConfigData) 		# Decode json data

	if j['success'] == False:
		gOut.writerow(['System Registeration >>>>>'])
		gOut.writerow(['Send Data on Server','Fail'])
		gOut.writerow(['value %s' % ucConfigData])
		lcd.clear()
		lcd.message('Registration\nFailed')
		time.sleep(1)
		SystemRegistration()
	else:
		gOut.writerow(['System Registeration >>>>>'])
		gOut.writerow(['Send Data on Server','Sucess'])
		gOut.writerow(['value %s' % ucConfigData])
		lcd.clear()
		lcd.message('Registration\nSucessful')
		time.sleep(1)
		lcd.clear()
		lcd.message('Configuration\nStart')
		time.sleep(1)
		ConfRet = GetConfiguration() # If Registration Sucess then calling GetComfiguration.
		if ConfRet == True:
			lcd.clear()
			lcd.message('Configuration\nSucessful')
			time.sleep(1)
	try:
			if j['success'] == False:
				Error = j['errors'][0]['code']
				if Error == "common.errors.internal_error":
					lcd.clear()
					lcd.message('Registration\nError')
					time.sleep(1)
					SystemRegistration()
				elif Error == "common.errors.url_not_found":
					lcd.clear()
					lcd.message('Registration\nError')
					time.sleep(1)
					SystemRegistration()
				else:
					raise ServerBusyError
			else:
				gOut.writerow([('%s' %(str(dt.now()))),'Server is Healthy'])

	except ServerBusyError:
			gOut.writerow(['Server Busy'])
			giCount+=1
			print ('Server Busy')
			print ('count %s' %giCount)
			if giCount >= DEFINE_INTERATION:
				giCount = 0
				gOut.writerow(['Server Busy overflaw'])
				giFlag = 0
				lcd.clear()
				ScrollingLCD('Waiting for connection to complete setup')
				SystemRegistration()
	
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: UserRegistration()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Empolyee Registration Function 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def UserRegistration():
	global giRegFlag
	global Images
	global giNumPhotos
	global giCurrentEmployee
	global giRegEmployeeName

	try:
		from io import BytesIO
	except ImportError:
		from StringIO import StringIO as BytesIO
		buffer = BytesIO()

	lcd.clear()
	lcd.message('wait for\nProcessing...')
	
	storage = StringIO()
	c = pycurl.Curl()
	c.setopt(c.URL, UserRegisterUrl)
	c.setopt(c.WRITEFUNCTION, storage.write)
	c.setopt(c.POST, 1)
	c.setopt(c.HTTPHEADER,['x-api-key: key-9acc61be5b2fe7f347908a9ced1f638f','x-api-secret: secret-835e6ed8dbcffcb7fa00a7b22be39e5e'])
	
	send = []
	for i in range(giNumPhotos):
		print Images[i]
		send.append(("files", (c.FORM_FILE,Images[i])))

	c.setopt(c.HTTPPOST,send) 
	c.perform()
	content = storage.getvalue()
	j = json.loads(content)
	if j['success'] == True:
		gOut.writerow([('%s' %(str(dt.now()))),'Registration Success for %s Employee',giCurrentEmployee])
		lcd.clear()
		ScrollingLCD('Congratulation, %s' %giRegEmployeeName)
	elif j['success'] == False:
		lcd.clear()
		lcd.message('Please do\nRegistrationtion Again')
		time.sleep(1)
		gOut.writerow([('%s' %(str(dt.now()))),'Registration Fail for %s Employee',giCurrentEmployee])
	print i
	print content 
	print "---------------------"
	c.close()
	Images = { }
	giRegImgCount = 0
	giRegFlag = 0
	giFlag = 0
	RegImg = 0

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: GetConfiguration()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Configuration by ApiKey,ApiSecret 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def GetConfiguration():
	global VideoLength
	global ucMediaType
	global ucContent
	global giRegFlag
	global giCurrentEmployee
	global giNumPhotos
	global giRegEmployeeName
	global giRegImgCount
	global giFlag
	global count
	gOut.writerow([('%s' %(str(dt.now()))),'Enter in GetConfiguration'])

	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 	#Create pycurl instance 
	c.setopt(c.URL, ConfigurationUrl) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	#c.setopt(c.HTTPHEADER,['Content-Type: application/json'])
	c.setopt(c.HTTPHEADER,['x-api-key: key-9acc61be5b2fe7f347908a9ced1f638f','x-api-secret: secret-835e6ed8dbcffcb7fa00a7b22be39e5e'])
	c.setopt(pycurl.POSTFIELDS,"")

	# Try and Exception for Server Timeout 
	try:
		c.perform()
		c.setopt(c.URL, ConfigurationUrl)
	except pycurl.error, error:
		errno, errstr = error
		print 'An error occurred: ', errstr  # Conection refused Error
		lcd.clear()
		ScrollingLCD('Waiting for connection to complete setup')
		
	c.close() 
		
	ucConfigData = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
	print (ucConfigData)

	j = json.loads(ucConfigData) 		# Decode json data
		
	if j['success'] == False:
		gOut.writerow(['Comfiguration >>>>>'])
		gOut.writerow(['Send Data on Server','Fail'])
		gOut.writerow(['value %s' % ucConfigData])
		lcd.clear()
		lcd.message('Configuration\nFailed')
		SystemRegistration()  # if Configuration Fail then again going to check Systemregistration
	else:
		gOut.writerow(['Configuration >>>>>'])
		gOut.writerow(['Send Data on Server','Sucess'])
		gOut.writerow(['value %s' % ucConfigData])

	try:
			if j['success'] == False:
				Error = j['errors'][0]['code']
				if Error == "common.errors.internal_error":
					lcd.clear()
					lcd.message('Configuration\nError.')
				elif Error == "common.errors.url_not_found":
					lcd.clear()
					lcd.message('Configuration\nError')
				else:
					raise ServerBusyError
			else:
				gOut.writerow([('%s' %(str(dt.now()))),'Server is Healthy'])

	except ServerBusyError:
			gOut.writerow(['Server Busy'])
			giCount+=1
			print ('Server Busy')
			print ('count %s' %giCount)
			if giCount >= DEFINE_INTERATION:
				giCount = 0
				gOut.writerow(['Server Busy overflaw'])
				giFlag = 0

	Enabled = j['item']['registration']['enabled']
	VideoLength = j['item']['configuration']['videoLength']
	ucMediaType = j['item']['configuration']['imageType']
	giCurrentEmployee = j['item']['registration']['currentEmployee']
	giNumPhotos = j['item']['registration']['numPhotos']

	gOut.writerow([('%s' %(str(dt.now()))),'%s' %Enabled])
	gOut.writerow([('%s' %(str(dt.now()))),'%s' %VideoLength])
	gOut.writerow([('%s' %(str(dt.now()))),'%s' %ucMediaType])
	gOut.writerow([('%s' %(str(dt.now()))),'%s' %giCurrentEmployee])
	gOut.writerow([('%s' %(str(dt.now()))),'%s' %giNumPhotos])

	print 'VideoLength : %d' %VideoLength
	print 'MediaType : %s' %ucMediaType
	print Enabled
	print giCurrentEmployee
	print giNumPhotos
	print giRegEmployeeName

	#ucMediaType = "static" # For testing change Media Type here
	
	if Enabled == False:
		giRegFlag = 0
		giRegImgCount = 0
		giFlag = 0
		count = 0
		lcd.clear()
		lcd.message('Registration\nDisable')
		time.sleep(1)
		lcd.clear()
		lcd.message('Press Switch for\ntake a picture')
	elif Enabled == True:
		giRegFlag = 1
		lcd.clear()
		lcd.message('Registration\nEnable')
		time.sleep(1)
		giRegEmployeeName = j['item']['registration']['currentEmployee']['name']
		gOut.writerow([('%s' %(str(dt.now()))),'%s' %giRegEmployeeName])
		lcd.clear()
		ScrollingLCD('Registration for %s' %giRegEmployeeName)

	return (j['success'])
	

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
	global giSkipJson
	SerialNumber = GetCpuId()
	ucStorage = StringIO() 	#setup a "ucStorage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 		#Create pycurl instance 
	c.setopt(c.URL, url) 	# URL
	c.setopt(c.WRITEFUNCTION, ucStorage.write)  # write data into "ucStorage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	print ('[x] buffer %s' %RecPath) 
	c.setopt(c.HTTPHEADER,['x-api-key: key-9acc61be5b2fe7f347908a9ced1f638f','x-api-secret: secret-835e6ed8dbcffcb7fa00a7b22be39e5e'])
	send = [("file", (c.FORM_FILE,RecPath)),("serialNumber",SerialNumber),("timestamp",str(dt.now())),] # Sending Camera generated file and timestamp in the form of "Form data" formate
	c.setopt(c.HTTPPOST,send) 		   # POST "form data" on server
	c.setopt(pycurl.CONNECTTIMEOUT, 1) # Timeout 1 second
	giSkipJson = 0
# Try and Exception for Server Timeout 

	try:
		c.perform()
		c.setopt(c.URL, url)
	except pycurl.error, error:
		errno, errstr = error
		gOut.writerow([('%s' %(str(dt.now()))),'Timeout error occurred', '%s' %errstr])
		print 'Timeout error occurred: ', errstr  # An error occured : Connection timed out after 1001 milliseconds
		giSkipJson = 1
		giTimeCount+=1
		if giTimeCount >= DEFINE_INTERATION: # 3 times time out interation check then flag will be zero and will go in ideal state 
				giTimeCount = 0
				giFlag = 0
				lcd.clear()
				ScrollingLCD('Waiting for connection to complete setup')
	c.close() 

	ucContent = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
	print ('value %s' % ucContent)

	if giSkipJson == 0:
		iServerResponse = True
		j = json.loads(ucContent) 		# Decode json data
		
		if j['success'] == False:
			gOut.writerow([('%s' %(str(dt.now()))),'Send Data on Server','Fail'])
			gOut.writerow(['value %s' % ucContent])
		else:
			gOut.writerow([('%s' %(str(dt.now()))),'Send Data on Server','Sucess'])
			gOut.writerow(['value %s' % ucContent])                                                             

	# Try and Exception for Status of Server 
		try:

				if j['success'] == False:
					Error = j['errors'][0]['code']
					if Error == "common.errors.internal_error":
						lcd.clear()
						lcd.message("Sorry,Please\ntry again.")
						time.sleep(1)
					else:
						raise ServerBusyError
				else:
					gOut.writerow([('%s' %(str(dt.now()))),'Server is Healthy'])

		except ServerBusyError:
				gOut.writerow(['Server Busy'])
				giCount+=1
				print ('Server Busy')
				print ('count %s' %giCount)
				if giCount >= DEFINE_INTERATION:
					giCount = 0
					gOut.writerow([('%s' %(str(dt.now()))),'Server Busy overflaw'])
					giFlag = 0
					lcd.clear()
					ScrollingLCD('Waiting for connection to complete setup')

		if ucMediaType == "static" and j['success'] == True:
			if j['message'] == "Sorry authentication failed.":
				lcd.clear()
				lcd.message("Sorry,Please\ntry again")
				time.sleep(1)
			else:
				lcd.clear()
				ScrollingLCD(j['message'])
				time.sleep(1)
				lcd.clear()
				lcd.message('***Thank you***')
				time.sleep(2)
		elif ucMediaType == "static" and j['success'] == False:
			lcd.clear()
			lcd.message("Sorry can not\nDetecting...")
			time.sleep(1)

	elif giSkipJson == 1:
		print 'Pending Images Data'
		global giPendingCount
		iServerResponse = False
		PendingImages[giPendingCount] = RecPath 
		gOut.writerow([('%s' %(str(dt.now()))),'Pending Image Stored',PendingImages[giPendingCount]])
		giPendingCount+=1
		lcd.clear()
		lcd.message('Your Pending\nImage Stored')
	# for i in range(giVidCount):
	# 	print ('\n %s' %PendingImages[i])
	# 	print ("Array_Size:%d"%(len(PendingImages)))

	gOut.writerow([('%s' %(str(dt.now()))),'SendData Function Finish'])
				 
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
			gCamera.annotate_text = ('Rydot infotech Attendance System_'+('%s' %(str(dt.now()))))
			gCamera.brightness = BRIGHTNESS
			gCamera.resolution = (RESOLUTION_H, RESOLUTION_W) 
			gCamera.framerate = VIDEO_FRAMERATE
			gOut.writerow([('%s' %(str(dt.now()))),'Video_Recording_Start'])
			gCamera.start_recording(abs_path+'Raw_Video/video%s.h264' %giVidCount)
			gOut.writerow([('%s' %(str(dt.now()))),'Raw .h264 file generated'])
			# if giOpenFlag == 1:  
			# 	VideoLengthLimit(VideoLength)
			while wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1:  
			    	VideoLengthLimit(VideoLength)
				if giOpenFlag == 0:
					break
					#gCamera.wait_recording()

			gCamera.stop_recording()
			gOut.writerow([('%s' %(str(dt.now()))),'Video_Recording_Stop'])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: CaptureImage
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Capturing Image 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~		 
def CaptureImage():
			print ('Camera giVidcount %d' %giVidCount)
			gCamera.framerate = IMAGE_FRAMERATE
			gCamera.resolution = (RESOLUTION_H, RESOLUTION_W) 
			gCamera.annotate_text = ('Rydot infotech Attendance System_'+('%s' %(str(dt.now()))))
			gCamera.capture(abs_path+'Image/image%s.jpg'% (giVidCount-1))
			gOut.writerow([('%s' %(str(dt.now()))),'Capture_Image','Success'])
			gOut.writerow([('%s' %(str(dt.now()))),'Capture_Image_path',abs_path+'Image/image%s.jpg'% (giVidCount-1)])
			return (abs_path+'Image/image%s.jpg'% (giVidCount-1))
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: RegCaptureImages
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Register Capturing Image 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def RegCaptureImage():
			global RegImg
			print ('Camera giVidcount %d' %RegImg)
			gCamera.framerate = IMAGE_FRAMERATE
			gCamera.resolution = (RESOLUTION_H, RESOLUTION_W) 
			gCamera.annotate_text = ('Rydot infotech Attendance System_'+('%s' %(str(dt.now()))))
			gCamera.capture(abs_path+'RegImage/image%s.jpg'% (RegImg))
			gOut.writerow([('%s' %(str(dt.now()))),'Capture_Image','Success'])
			gOut.writerow([('%s' %(str(dt.now()))),'Capture_Image_path',abs_path+'RegImage/image%s.jpg'% (RegImg)])
			return (abs_path+'RegImage/image%s.jpg'% (RegImg))
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
	print ('MsgQueue_Send_Count>>>>>>:%d'% giVidCount)
	InputFile = (MQSendPath) #Raw file video(n).h264 path

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue='key%s'% (giVidCount-1)) # Generate Key(n)	
	channel.basic_publish(exchange='', routing_key='key%s'% (giVidCount-1), body=InputFile) #Send body as a video(n).h264 file path
	print('[x] Sent_path : %s' %(InputFile))
	print('[x] Sending Key:%s' %(giVidCount-1))
	gOut.writerow([('%s' %(str(dt.now()))),'MessageQueue: SendFilePath','%s' %InputFile])
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
	print ('MsgQueue_Rec_Count@@@@@@:%d'% giVidCount)
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue=('key%s' %giVidCount))
	def callback(ch, method, properties, body):
			print(" [x] Received %r" % body)
			ch.stop_consuming()
			ImageRecPath = body
			VideoRecPath = body
			print(" [x] data %r" % ImageRecPath) 
			if ucMediaType == "static":
				SendData(ImageRecPath) # Send data on server
				gOut.writerow([('%s' %(str(dt.now()))),'MessageQueue: ReceiveFilePath','%s' %ImageRecPath])
			if ucMediaType == "moving":
				gOut.writerow([('%s' %(str(dt.now()))),'MessageQueue: ReceiveFilePath','%s' %VideoRecPath])
				os.system('MP4Box -fps 30 -add '+VideoRecPath+' outfile.mp4') # raw.h264 to .mp4 Conversion
				#time.sleep(1)
				os.system('cp outfile.mp4 MP4_Video/VID_%d.mp4' %giVidCount) # Copy current outfile.mp4 to number of VID_(n).mp4 
				gOut.writerow([('%s' %(str(dt.now()))),'MP4 File Generated','MP4_Video/VID_%d.mp4' %giVidCount])
				VideoTimeDuration() #This Function will call for check Video time duration.

	channel.basic_consume(callback,
                      queue=('key%s' %giVidCount),
                      no_ack=True)
	print('[x] Receive Key:%s' %(giVidCount))
	giVidCount+=1
	time.sleep(0.2)
	if ucMediaType == 'static':
		lcd.clear()
		lcd.message('Press Switch for\ntake a picture')
	# os.system('rm outputimage.jpg')
	print(' [*] Waiting for messages. To exit press CTRL+C')
	channel.start_consuming()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: DoorEventInterrupt()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Interrupt Service Routine. 
#				  ISR affected when Door posion is Open.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def DoorEventInterrupt():
	# global giFlag
	# global giOpenFlag
	# if giFlag == 0:
	# 	giFlag = 1
	# 	giOpenFlag = 1
	# 	gOut.writerow([('%s' %(str(dt.now()))),'Interrupt Event Occured'])
	# 	print ('In ISR')
	# time.sleep(1)
	global giFlag
	global giOpenFlag
	if giFlag == 0:
		time.sleep(0.2)
		print "giflag = ", giFlag, "in ISR"
		giFlag = 1
	 	giOpenFlag = 1
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: VideoLoop()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Function will monitor Door position and capture Video and 
#				  send video path using MessageQueueSendFile()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def VideoLoop():
			print wiringpi.digitalRead(READ_SWITCH)
			time.sleep(0.2)	
			global giFlag
			global giCount
			global giVidCount
			global giOpenFlag
			print ('video_Mode')
			print ('flag %s' %giFlag)			
			print ('giOpenFlag %s' %giOpenFlag)
			print ('giVidCount %s' %giVidCount)
			lcd.clear()
			lcd.message('Rydot Info. Ltd.\n%s'%(str(dt.now())))
			if wiringpi.digitalRead(READ_SWITCH) == 0 and giFlag == 1 and giOpenFlag == 1:   
					gOut.writerow([('%s' %(str(dt.now()))),'Door Position','Open'])
					print ('OPEN')
					CaptureVideo()
					MessageQueueSendFile(abs_path+'Raw_Video/video%s.h264'% (giVidCount))
					giFlag = 0
					giOpenFlag = 0
			elif wiringpi.digitalRead(READ_SWITCH) == 1:
					giFlag = 0
					giOpenFlag = 0
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: ImageLoop()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Function will monitor Door position and capture Image and 
#				  send image path using MessageQueueSendFile()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def ImageLoop():
			
			global giFlag
			global giRegFlag
			global giInteration
			global giCount
			global giVidCount
			global giRegImgCount
			global giCurrentEmployee
			global giNumPhotos
			global RegImg
			global count
			global giRegEmployeeName
			print wiringpi.digitalRead(READ_SWITCH)
			time.sleep(0.2)	
			print ('Image_Mode')
			print ('flag %s' %giFlag)
			print ('Regflag %s' %giRegFlag)
			print ('RegCount %s' %giRegImgCount)
			#print ('count %s' %giCount)
			print ('giVidCount %s' %giVidCount)
			#print ('Argument : %s' %(sys.argv[1]))			
			print ('In Loop')

			if giFlag == 1 and giRegFlag == 0 and wiringpi.digitalRead(READ_SWITCH) == 0:  
				count = 0  
				#for giInteration in range(ENTRY_IMAGES):
				gOut.writerow([('%s' %(str(dt.now()))),'Switch Press'])
				#time.sleep(0.2)	
				CaptureImage()
				lcd.clear()
				lcd.message('Wait for a\nProcess...')
				MessageQueueSendFile(abs_path+'Image/image%s.jpg' % (giVidCount-1))
				#time.sleep(1)
				#print ('Loop %s' %giInteration)	
				#if giInteration <= (ENTRY_IMAGES - 1):
				giFlag = 0
				gOut.writerow([('%s' %(str(dt.now()))),'Switch Release'])
			if giRegFlag == 1 and giFlag == 1:
				count = 0
				print "In Registration"
				print 'Reg_Image_count:%s' %giRegImgCount
				if giRegImgCount <= (giNumPhotos-1):
					RegImgPath = RegCaptureImage()
					Images[giRegImgCount] = RegImgPath
					print RegImgPath
					giRegImgCount+=1
					RegImg+=1
					giFlag = 0
					if giRegImgCount >= giNumPhotos:
						count = 0
						UserRegistration()
						os.system('rm -rf RegImage') # Registration directory remove 
						os.mkdir( REG_IMAGE_DIR_PATH, 0777 )  # Registration directory generate
						giFlag = 0
						RegImg = 0
						lcd.clear()
						lcd.message('Press Switch for\ntake a picture')
			if giRegFlag == 1 and giFlag == 0:
				if giRegImgCount >= giNumPhotos:
					lcd.clear()
					lcd.message('Press switch for\nSend Images')
				else:
					lcd.clear()
					lcd.message('Press switch for\nReg. Image:%s' %giRegImgCount)
			#elif giRegFlag == 0 and giFlag == 0:
			#		GetConfiguration()
				
				
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: DoorEventThread()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : Generate Video and Send Video path using message queue 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def DoorEventThread():
	while True:
		global count
		global giRegFlag
		global giRegImgCount
		global RegImg
		global giFlag
		global ucMediaType
		print("In thread1")
		if wiringpi.digitalRead(READ_SWITCH) == 1 and count<=10 and giRegFlag != 1 and ucMediaType == "static":
			giFlag = 0
			count+=1
			print 'count:%s' %count
			time.sleep(1)
			if count == 9:
				lcd.clear()
				lcd.message('Wait for\nProcessing...')
			if count >=10:
				giRegImgCount = 0
				RegImg = 0 
				giFlag = 0
				time.sleep(3)
				GetConfiguration()
				count = 0
		elif wiringpi.digitalRead(READ_SWITCH) == 1 and count<=10 and giRegFlag == 1 and ucMediaType == "static":
			giFlag = 0
			count+=1
			print 'count:%s' %count
			time.sleep(1)
			if count == 9:
				lcd.clear()
				lcd.message('Wait for\nProcessing...')
			if count >= 10:
				lcd.clear()
				lcd.message('Press Switch for\ntake a picture')
				giRegFlag = 0
				giFlag = 0
				giRegImgCount = 0
				RegImg = 0
				count = 0
				time.sleep(3)

		elif ucMediaType == "static":
			ImageLoop()	
			time.sleep(0.2)
		elif ucMediaType == "moving":
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
	gOut.writerow([('%s' %(str(dt.now()))),'Create threads'])
	t1 = threading.Thread(target=UploadThread, args=())	
	t2 = threading.Thread(target=DoorEventThread, args=())
	#Start DoorEventThread
	gOut.writerow([('%s' %(str(dt.now()))),'Start Upload Thread'])
	t1.start()
	#Start ImageUploadThread
	gOut.writerow([('%s' %(str(dt.now()))),'Start DoorEvent Thread']) 
	t2.start()
	
	#schedule.every(CONFIG_SCHEDULE_TIME).seconds.do(GetConfiguration)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: main()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is main function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':
	global fpLogFile
	global gOut
	Setup()	
	InitThread()
	killer = GracefulKill()
	# Main Thread : Check Wifi Status and Pending Media sent on Server and also kill it self by SIGTERM Signal 
	while True:
		fpLogFile = open(LOG_FILE_PATH,"a")
		gOut = csv.writer(fpLogFile, delimiter=',' , quoting=csv.QUOTE_ALL)
		#schedule.run_pending()
		subprocess.call(['./wifi_check.sh'])
		print 'Return: %s',iServerResponse
		if (len(PendingImages)) > 0 and iServerResponse == True:
			for i in range(len(PendingImages)):
				SendData(PendingImages[i])
				print 'Pending Image sent: %d',PendingImages[i]
				gOut.writerow([('%s' %(str(dt.now()))),'Pending Image sent',PendingImages[i]])
				gOut.writerow([('%s' %(str(dt.now()))),'PendingImage_Buffer',len(PendingImages)])
			if i == ((len(PendingImages))-1):
				lcd.clear()
				lcd.message("Pending Images\nUpload Sucesful")
				PendingImages = { }
				gOut.writerow([('%s' %(str(dt.now()))),'PendingImage_Buffer',len(PendingImages)])
				giPendingCount = 0 
				if ucMediaType == 'static' and giRegFlag == 0:
					lcd.clear()
					lcd.message('Press Switch for\ntake a picture')
				gOut.writerow([('%s' %(str(dt.now()))),'PendingImage_Buffer',len(PendingImages)])
		else:
			if iServerResponse == True:
				# if ucMediaType == 'static':
				# 	lcd.message('Ready to take\nPicture')
				if ucMediaType == 'moving':
					lcd.clear()
					lcd.message('Rydot Info. Ltd.\n%s'%(str(dt.now())))
				#count = 0
			else:
				lcd.clear()
	   			ScrollingLCD('Waiting for connection to complete setup')

		if killer.kill_now:
			giKillFlag=1
			fpLogFile.close()
			break
	iPid = os.getpid()
	os.system('kill -9 %s' %iPid)

	gOut.writerow([('%s' %(str(dt.now()))),'Terminate Process by Signal'])
	# wait until DoorEventThread is completely executed 
	t1.join()
	# wait until ImageUploadThread is completely executed
	t2.join()
	#print "All threads stopped."


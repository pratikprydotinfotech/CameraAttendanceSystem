#-------------------------------------------------------------------------------------------------------------------------------------
#File Name 		   : wire_pi.py
#Author(s) 		   : Pratik Panchal
#Purpose of module : Attendance system provide some features like capture image when door will open,
# 					 process on image and perfect image upload on server. 
#Date of creation  : 16/11/2018
#-------------------------------------------------------------------------------------------------------------------------------------
import json
import csv
import os, sys
import pycurl   # pycurl module import
import wiringpi # wiringpi module import for GPIO   
import time     # time library module import
import cStringIO
from StringIO import StringIO
from datetime import datetime 
from picamera import PiCamera # pi camera function use from picamera module
from time import sleep 		  # sleep function use from time library module      
global flag 				  # globally define flag
flag = 1
global out

global count
count=0

url = "http://192.168.0.4:3000/upload"
DEFINE_INTERATION = 3

# define user-defined exceptions for Server Busy
class Error(Exception):
   """Base class for other exceptions"""
   pass

class ServerBusyError(Error):

   pass

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Log_File_Generation
# @ Parameter 	: void
# @ Return 		: void
# @ Brief 		: This Function is Genrate Log data file
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def Log_File_Generation():
	global out
	os.system('rm -rf Test_Log')
	path = "/home/pi/Desktop/Test_Log"
	os.mkdir( path, 0755 )
	out = csv.writer(open("/home/pi/Desktop/Test_Log/log.csv","w"), delimiter=',' , quoting=csv.QUOTE_ALL)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: setup
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is initialize GPIO ,Camera , Log data file
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def setup():
	global camera
	Log_File_Generation()
	out.writerow(['Setup Function Intialize\n'])
	wiringpi.wiringPiSetupGpio()  
	wiringpi.pinMode(23, 0) # Reed switch GPIO 23      
	wiringpi.pullUpDnControl(23,1) # e.g 1 - PullDown , 0 - PullUp
	wiringpi.wiringPiISR(23, wiringpi.INT_EDGE_RISING, Door_event) # Interrupt ISR init by using Edge triggering in Rising edge 
	out.writerow(['GPIO Init','Sucess'])
	camera = PiCamera()
	out.writerow(['Camera Init','Sucess'])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Send_data
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Sending Form data on server 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def Send_data(): 
	global count
	buf = cStringIO.StringIO()
	storage = StringIO() 	#setup a "storage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 		#Create pycurl instance 
	c.setopt(c.URL, url) 	# URL
	c.setopt(c.WRITEFUNCTION, storage.write)  # write data into "storage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	send = [("file", (c.FORM_FILE, "log.csv")),("timestamp",str(datetime.now())),] # Sending Camera generated file and timestamp in the form of "Form data" formate
	c.setopt(c.HTTPPOST,send) # POST "form data" on server
	c.setopt(pycurl.CONNECTTIMEOUT, 1)
	c.setopt(pycurl.TIMEOUT, 1)
	
	try:
		c.perform()
		c.setopt(c.URL, "http://192.168.0.4:3000/upload")
		
	except pycurl.error, error:
		errno, errstr = error
		out.writerow(['An error occurred', '%s' %errstr])
		#print 'An error occurred: ', errstr
    
	c.close() 
	
#	content = storage.getvalue() 	#Data colect in content string from storage buffer
#	print buf.getvalue()
	
#	j = json.loads(content) 		# Decode json data
#	print j['success']
	
#	if j['success'] == False:
#	 out.writerow(['Send Data on Server','Fail'])
#	 out.writerow(['value %s' % content])
#	else:
#	 out.writerow(['Send Data on Server','Sucess'])
#	 out.writerow(['value %s' % content])
	 
	# Try and Exception for Status of Server 
#	try:
	
#			if j['success'] == False:
#				raise ServerBusyError
#			else:
#				out.writerow(['Server is Healthy'])

#	except ServerBusyError:
#			out.writerow(['Server Busy'])
#			count+=1
#			if count >= DEFINE_INTERATION:
#				count = -1
#				out.writerow(['Server Busy overflaw'])
#				loop()
				
	 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: capture_image
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Capturing Image 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~		 
def capture_image():
			out.writerow(['Capture Image','Sucess'])
			camera.capture('/home/pi/Desktop/image.jpg')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: Door_event
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Interrupt Service Routine
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	
def Door_event():
	global flag
	flag = 1
	out.writerow(['In Interrupt','Door Event Init'])
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: loop
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is Looping System
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def loop():
	while True:  
            
			print wiringpi.digitalRead(23)
			time.sleep(0.2)	
			global flag
			print ('flag %s' %flag)
			print ('count %s' %count)				

			if wiringpi.digitalRead(23) == 0 and flag == 1:   
				out.writerow(['Door Position','Open'])
				capture_image()
				Send_data()
				flag = 0
				
			out.writerow(['Door Position','Close'])
			out.writerow(['Flag','%s' %flag])
			out.writerow(['count', '%s' %count])
			out.writerow(['GPIO','%d' % wiringpi.digitalRead(23)])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @Function 	: main()
# @ Parameter   : void
# @ Return      : void
# @ Brief       : This Function is main function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':
		
		setup()
		
		try:
				loop()
				#GPIO.wait_for_edge(18, GPIO.FALLING)
		except KeyboardInterrupt:
			    print 'keyboard interrupt detected'
			    out.writerow(['keyboard interrupt detected','Exit'])
			    GPIO.cleanup()	
	

#-------------------------------------------------------------------------------------------------------------------------------------
#File Name 		   : wire_pi.py
#Author(s) 		   : Pratik Panchal
#Purpose of module : Attendance system provide some features like capture image when door will open,
# 					 process on image and perfect image upload on server. 
#Date of creation  : 16/11/2018
#-------------------------------------------------------------------------------------------------------------------------------------

import pycurl   # pycurl module import
import wiringpi # wiringpi module import for GPIO   
import time     # time library module import
from StringIO import StringIO
from datetime import datetime
from picamera import PiCamera # pi camera function use from picamera module
from time import sleep 		  # sleep function use from time library module      
global flag 				  # globally define flag
flag = 1

DEFINE_INTERATION = 3

#try:
#    from io import BytesIO
#except ImportError:
#    from StringIO import StringIO as BytesIO
#    buffer = BytesIO()
    
def setup():  # Setup() is initialize GPIO with some GPIO controll features
	global camera
	wiringpi.wiringPiSetupGpio()  
	wiringpi.pinMode(23, 0) # Reed switch GPIO 23      
	wiringpi.pullUpDnControl(23,1) # e.g 1 - PullDown , 0 - PullUp
	wiringpi.wiringPiISR(23, wiringpi.INT_EDGE_RISING, Door_event) # Interrupt ISR init by using Edge triggering in Rising edge 
	camera = PiCamera()
	
def Send_data(): # After Capture image send it on Server 
	storage = StringIO() 	#setup a "storage" buffer in the form of a StringIO object 
	c = pycurl.Curl() 		#Create pycurl instance 
	c.setopt(c.URL, "http://192.168.0.4:3000/upload") # URL
	c.setopt(c.WRITEFUNCTION, storage.write)  # write data into "storage" data buffer using WRITEFUNCTION (Number of bytes written)
	c.setopt(c.POST, 1)  # 1 - URL query parameters
	send = [("file", (c.FORM_FILE, "image.jpg")),("timestamp",str(datetime.now())),] # Sending Camera generated file and timestamp in the form of "Form data" formate
	c.setopt(c.HTTPPOST,send) # POST "form data" on server
	#c.setopt(pycurl.HTTPHEADER, ['Accept-Language: en'])
	c.perform() #perform() file transfer return nothing
	
	print('\n Status: %d' % c.getinfo(c.RESPONSE_CODE))  # HTTP response code, e.g. 200.
	
	print('Status: %f' % c.getinfo(c.TOTAL_TIME)) # Elapsed time for the transfer.
	
	c.close() 
	
	content = storage.getvalue()
	print ('~~~~~~~~~~~~~~~~~~~~~~')
	print content

	sucess = content.find('data')
	print ("result index:",sucess)

	if sucess == -1:
	 print ('FAIL')
	else:
	 print ('SUCESS')
	 
	
def capture_image():
			print('Open')
			#path = ('/home/pi/Desktop/image_%s.jpg'%str(datetime.now()))
			#time.sleep(0.2)
			#camera.start_preview()
			#sleep(5)
			camera.capture('/home/pi/Desktop/image.jpg')
			#camera.capture(path)
			#camera.stop_preview()


def Door_event():
	global flag
	print ('In ISR')
	flag = 1



def loop():
	while True:  

			print wiringpi.digitalRead(23)
			time.sleep(0.2)	
			global flag
			print ('flag %s' %flag)			
			#if wiringpi.digitalRead(23) == 1 and flag == 0:    
			#	print ('Close')
			#	time.sleep(0.2)  
			if wiringpi.digitalRead(23) == 0 and flag == 1:   
				print ('Open') 
				capture_image()
				time.sleep(0.2)
				#Send_data()
				flag = 0


if __name__ == '__main__':
		
		setup()
		
		try:
				loop()
				#GPIO.wait_for_edge(18, GPIO.FALLING)
		except KeyboardInterrupt:
			    print 'keyboard interrupt detected'
			    GPIO.cleanup()	
	

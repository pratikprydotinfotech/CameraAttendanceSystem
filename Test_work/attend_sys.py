import pycurl
from datetime import datetime
import RPi.GPIO as GPIO
import time
from picamera import PiCamera
from time import sleep
global run_state
run_state = False

DEFINE_INTERATION = 3

	try:
		from io import BytesIO
	except ImportError:
		from StringIO import StringIO as BytesIO
		buffer = BytesIO()
    
def setup():
	global camera
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(18,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
	GPIO.add_event_detect(18,GPIO.RISING, callback=Door_event, bouncetime=2000)
	camera = PiCamera()

def Send_data():
	c = pycurl.Curl()
	c.setopt(c.URL, "http://192.168.0.4:3000/upload")
	c.setopt(c.POST, 1)
	send = [("file", (c.FORM_FILE, "image.jpg")),("timestamp",str(datetime.now())),]
	c.setopt(c.HTTPPOST,send)
	#c.setopt(pycurl.HTTPHEADER, ['Accept-Language: en'])
	c.perform()
	# HTTP response code, e.g. 200.
	print('\n Status: %d' % c.getinfo(c.RESPONSE_CODE))
	# Elapsed time for the transfer.
	print('Status: %f' % c.getinfo(c.TOTAL_TIME))
	# TimeStamp 
	print(datetime.now())
	c.close()

def Door_event(channel):
	global run_state
	run_state = True
	print('Edge detection channel %s'%channel)   

def capture_image():
			print('Open')
			#path = ('/home/pi/Desktop/image_%s.jpg'%str(datetime.now()))
			time.sleep(0.2)
			camera.start_preview()
			#sleep(5)
			camera.capture('/home/pi/Desktop/image.jpg')
			#camera.capture(path)
			camera.stop_preview()
    
def loop():
	global run_state
	while True:
			
		if run_state == True:
			capture_image()
			time.sleep(0.2)
			Send_data()
			run_state = False
		else:
			time.sleep(0.2)
			print ('Door_close')

if __name__ == '__main__':
		
		setup()
		
		try:
				loop()
				#GPIO.wait_for_edge(18, GPIO.FALLING)
		except KeyboardInterrupt:
			    print 'keyboard interrupt detected'
			    GPIO.cleanup()
			    

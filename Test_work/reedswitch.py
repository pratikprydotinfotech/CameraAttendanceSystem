import RPi.GPIO as GPIO
import time

def Door_event(channel):
	print('Door_open')

print ('Using GPIO.BCM notation for IO')
GPIO.setmode(GPIO.BCM)

print ('Using 18 GPIO, pull down')
GPIO.setup(18,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(18,GPIO.FALLING, callback=Door_event, bouncetime=1000)
def loop():	
	while True:
		
		time.sleep(0.1)
		print GPIO.input(18)
      
	  
if __name__ == '__main__':
		
		#setup()
		
		try:
			    
				loop()
				#GPIO.wait_for_edge(18, GPIO.FALLING)
		except KeyboardInterrupt:
			    print 'keyboard interrupt detected'
			    GPIO.cleanup()

from picamera import PiCamera
from time import sleep

camera = PiCamera()
global count
count = 0

#while True: 
camera.resolution = (2592,1944)
camera.framerate = 60
camera.start_preview()
sleep(5)
#camera.capture('/home/pi/Desktop/image%s.jpg'% count)
camera.capture('/home/pi/Desktop/image.jpg')
camera.stop_preview()
#count+=1

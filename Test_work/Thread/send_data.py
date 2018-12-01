import os, sys
import json
import pycurl
from StringIO import StringIO
from datetime import datetime 

register_url = 'http://192.168.0.4:9128/api/ams/public/devices/register'
configuration_url = 'http://192.168.0.4:9128/api/ams/public/devices/get-configuration'

data = '{"serialNumber":"1234567890","apiKey":"key-de0bd007143f9e4fb9b628d52fb084f741f","apiSecret":"secret-a0e0ab24569f819036014a587ff9f3b3"}'

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
	print 'An error occurred: ', errstr  # An error occured : Connection timed out after 1001 milliseconds
c.close() 
	
ucContent = ucStorage.getvalue() 	#Data collect in ucContent string from ucStorage buffer
print (ucContent)
j = json.loads(ucContent) 		# Decode json data
	
# Server status maintain in Log file.
print j['success']

if j['success'] == False:
 	print('Fail')
else:
 	print('Sucess')


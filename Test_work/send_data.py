import os, sys
import json
import pycurl
import os
import random
import string
import secrets
from StringIO import StringIO
from datetime import datetime 
import objectpath

register_url = 'http://192.168.0.4:9128/api/ams/public/devices/register'
configuration_url = 'http://192.168.0.4:9128/api/ams/public/devices/get-configuration'

def getserial():
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

SerialNumber = getserial()
# ApiKey = 'key-'+os.urandom(16).encode("hex")
# ApiSecret = 'apiSecret-'+secrets.token_hex(16)

# string_ = "\"serialNumber\":"+('\"%s\"' %SerialNumber)+",\"apiKey\":"+('\"%s\",' %ApiKey)+"\"apiSecret\":"+('\"%s\"' %ApiSecret)
# print string_

data = '{"serialNumber":"1234567890","apiKey":"key-de0bd007143f9e4fb9b628d52fb084f741f","apiSecret":"secret-a0e0ab24569f819036014a587ff9f3b3"}'

def flatten_hook(obj):
    for key, value in obj.iteritems():
        if isinstance(value, basestring):
            try:
                obj['item'] = json.loads(value, object_hook=flatten_hook)
            except ValueError:
                pass
    return obj

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

jsonnn_tree = objectpath.Tree(j['item'])
Config = tuple(jsonnn_tree.execute('$..configuration'))
print Config
video_length = tuple(jsonnn_tree.execute('$..videoLength'))
print video_length
Image_Type = tuple(jsonnn_tree.execute('$..imageType'))
print Image_Type

for x in Config:
  print(x)
# Server status maintain in Log file.
#data2 = j['item']
#print data2

if j['success'] == False:
 	print('Fail')
else:
 	print('Sucess')


import os
import random
import string
import secrets

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

def generate_key(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

if __name__ == '__main__':
    # ApiKey = generate_key(16)
    # print Apikey
    print (getserial())
    print ('apiKey-'+os.urandom(16).encode("hex"))

    print ('apiSecret-'+secrets.token_hex(16))
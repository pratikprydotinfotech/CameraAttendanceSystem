import pycurl 

c = pycurl.Curl()
c.settimeout(5)   # 5 seconds
try:
    c.connect(('192.168.0.4:', 3000))         # "random" IP address and port
except socket.error, exc:
    print "Caught exception socket.error : %s" % exc

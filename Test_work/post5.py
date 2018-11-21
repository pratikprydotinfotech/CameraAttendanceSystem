from StringIO import StringIO
import pycurl

DEFINE_INTERATION = 3

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO
    buffer = BytesIO()

storage = StringIO()
c = pycurl.Curl()
c.setopt(c.URL, "http://192.168.0.4:3000/upload")
c.setopt(c.WRITEFUNCTION, storage.write)
c.setopt(c.POST, 1)
c.setopt(c.HTTPPOST, [("file", (c.FORM_FILE, "image.jpg"))])
#c.setopt(pycurl.HTTPHEADER, ['Accept-Language: en']) 
c.setopt(pycurl.CONNECTTIMEOUT, 300)
c.setopt(pycurl.TIMEOUT, 300)
try:
    c.perform()
 
    c.setopt(c.URL, "http://192.168.0.4:3000/upload")
    c.setopt(c.POSTFIELDS, 'foo=bar&bar=foo')
except pycurl.error, error:
    errno, errstr = error
    print 'An error occurred: ', errstr

# HTTP response code, e.g. 200.
print('\n Status: %d' % c.getinfo(c.RESPONSE_CODE))
# Elapsed time for the transfer.
print('Status: %f' % c.getinfo(c.TOTAL_TIME))

c.close()
content = storage.getvalue()
print ('~~~~~~~~')
print content

sucess = content.find('data')
print ("result index:",sucess)

if sucess == -1:
	 print ('FAIL')
else:
	 print ('SUCESS')



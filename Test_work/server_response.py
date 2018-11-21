import pycurl, random, socket

class ConnectionRejected(Exception):
    pass

def opensocket(curl, purpose, curl_address):
    # always fail
    curl.exception = ConnectionRejected('Rejecting connection attempt in opensocket callback')
    return pycurl.SOCKET_BAD

    # the callback must create a socket if it does not fail,
    # see examples/opensocketexception.py

c = pycurl.Curl()
c.setopt(c.URL, "http://192.168.0.4:3000/upload")
c.exception = None
c.setopt(c.OPENSOCKETFUNCTION,
    lambda purpose, address: opensocket(c, purpose, address))

try:
    c.perform()
except pycurl.error as e:
    if e.args[0] == pycurl.E_COULDNT_CONNECT and c.exception:
        print(c.exception)
    else:
        print(e)

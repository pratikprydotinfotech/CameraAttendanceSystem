global count
count=0
# define Python user-defined exceptions
class Error(Exception):
   """Base class for other exceptions"""
   pass

class ServerBusyError(Error):

   pass


# our main program
# user guesses a number until he/she gets it right

# you need to guess this number
server = 11

while True:
   try:
       i_num = int(input("Server status: "))
       if i_num != server:
           raise ServerBusyError
       else:
           print ("Server Healthy")
       #break
   except ServerBusyError:
	   print("ServerBusy")
	   count = count + 1
	   if count >= 3:
			break

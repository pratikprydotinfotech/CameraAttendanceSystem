
# Python program to illustrate the concept 
# of threading 
# importing the threading module 
import threading 
import time

def thread1(num): 
    """ 
    function to print square of given num 
    """
    while True:
        print("In thread1")
        time.sleep(1) 

def thread2(num): 
    """ 
    function to print cube of given num 
    """
    while True:
        print("In thread2")
        time.sleep(1) 
 
if __name__ == "__main__": 
    # creating thread 
    t1 = threading.Thread(target=thread1, args=(10,)) 
    t2 = threading.Thread(target=thread2, args=(10,)) 
  
    # starting thread 1 
    t1.start() 
    # starting thread 2 
    t2.start() 
  
    # wait until thread 1 is completely executed 
    t1.join() 
    # wait until thread 2 is completely executed 
    t2.join() 
 
    # both threads completely executed 
    print("Done!") 


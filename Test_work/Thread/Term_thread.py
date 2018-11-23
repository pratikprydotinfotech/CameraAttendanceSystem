import threading, signal, time, os


RUNNING = True
threads = []

def monitoring(tid, itemId=None, threshold=None):
    global RUNNING
    while(RUNNING):
        print "PID=", os.getpid(), ";id=", tid

        if tid == 1:
            fun1()
        
        if tid == 2:
            fun2()

        
        time.sleep(2)
    
    print "Thread stopped:", tid

def fun1():
    print ('In fun1')

def fun2():
    print ('In fun2')   


def handler(signum, frame):
    print "Signal is received:" + str(signum)
    global RUNNING
    RUNNING=False
    #global threads

if __name__ == '__main__':
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGALRM, handler)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGQUIT, handler)

    print "Starting all threads..."
    thread1 = threading.Thread(target=monitoring, args=(1,), kwargs={'itemId':'1', 'threshold':60})
    thread1.start()
    threads.append(thread1)
    thread2 = threading.Thread(target=monitoring, args=(2,), kwargs={'itemId':'2', 'threshold':60})
    thread2.start()
    threads.append(thread2)
    while(RUNNING):
        print "Main program is sleeping."
        time.sleep(30)
    for thread in threads:
        thread.join()

    print "All threads stopped."











































# import time
# import threading
# import signal
 
 
# class Job(threading.Thread):
 
#     def __init__(self):
#         threading.Thread.__init__(self)
 
#         # The shutdown_flag is a threading.Event object that
#         # indicates whether the thread should be terminated.
#         self.shutdown_flag = threading.Event()
#         print ('Init')
#         # ... Other thread setup code here ...
 
#     def run(self):
#         print ('Run')
#         print('Thread #%s started' % self.ident)
 
#         while not self.shutdown_flag.is_set():
#             # ... Job code here ...
#             time.sleep(0.5)
 
#         # ... Clean shutdown code here ...
#         print('Thread #%s stopped' % self.ident)
 
 
# class ServiceExit(Exception):
#     """
#     Custom exception which is used to trigger the clean exit
#     of all running threads and the main program.
#     """
#     pass
 
 
# def service_shutdown(signum, frame):
#     print('Caught signal %d' % signum)
#     raise ServiceExit
 
 
# def main():
 
#     # Register the signal handlers
#     signal.signal(signal.SIGTERM, service_shutdown)
#     signal.signal(signal.SIGINT, service_shutdown)
 
#     print('Starting main program')
 
#     # Start the job threads
#     try:
#         j1 = Job()
#         j2 = Job()
#         j1.start()
#         j2.start()
 
#         # Keep the main thread running, otherwise signals are ignored.
#         while True:
#             print ('In Loop')
#             time.sleep(0.5)
 
#     except ServiceExit:
#         # Terminate the running threads.
#         # Set the shutdown flag on each thread to trigger a clean shutdown of each thread.
#         j1.shutdown_flag.set()
#         j2.shutdown_flag.set()
#         # Wait for the threads to close...
#         j1.join()
#         j2.join()
 
#     print('Exiting main program')
 
 
# if __name__ == '__main__':
#     main()


























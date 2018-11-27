import threading
import pika
import time
from time import sleep

global answer

def thread1():
    while True:
	send()
	print("In thread1")
	time.sleep(1)


def thread2():
    while True:
	receive()
	print("In thread2")
	time.sleep(1)

def send():
    f = open("image.jpg","rb")
    i = f.read()
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='toJ')
    channel.basic_publish(exchange='', routing_key='toJ', body=i)
    connection.close()

def receive():
	fd=open("outputimage.jpg","wb")

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()

	channel.queue_declare(queue='toJ')

	def callback(ch, method, properties, body):
	    fd.write(body)
	    fd.close()
	    print(" [x] Received %r" % body)
	    ch.stop_consuming()

	channel.basic_consume(callback,
		              queue='toJ',
		              no_ack=True)
#	channel.start_consuming()
if __name__ == '__main__':
#	send()
#	receive()
	t1 = threading.Thread(target=thread1, args=())
	t2 = threading.Thread(target=thread2, args=())
	t1.start()
	t2.start()
	t1.join()
	t2.join()
	print ("done")


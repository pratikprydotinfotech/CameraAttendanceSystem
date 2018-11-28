#!/usr/bin/python
import pika
f = open("image.jpg","rb")
i = f.read()

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='key1')
channel.queue_declare(queue='key2')
channel.queue_declare(queue='key3')

ret1 = channel.basic_publish(exchange='', routing_key='key1', body='MSG_QUEUE_TEST')
print(" [x] Sent 'Test'")
print ret1

ret2 = channel.basic_publish(exchange='', routing_key='key2', body='Hello')
print(" [x] Sent 'Hello'")
print ret2

ret3 = channel.basic_publish(exchange='', routing_key='key3', body=i)
print(" [x] Sent 'File'")
print ret3
connection.close()


#!/usr/bin/python
import threading, signal
import pika
import simplejson as json
import csv
import os, sys
import pycurl   # pycurl module import
import wiringpi # wiringpi module import for GPIO 
import time     # time library module import
from StringIO import StringIO
from datetime import datetime 
from picamera import PiCamera # pi camera function use from picamera module
from time import sleep 		  # sleep function use from time library module      


f=open("outputimage.jpg","wb")

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='key1')
channel.queue_declare(queue='key2')
channel.queue_declare(queue='key3')

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)

channel.basic_consume(callback,
                      queue='key1',
                      no_ack=True)


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)


channel.basic_consume(callback,
                      queue='key2',
                      no_ack=True)

def callback(ch, method, properties, body):
    f.write(body)
    f.close()
    #print(" [x] Received %r" % body)

channel.basic_consume(callback,
                      queue='key3',
                      no_ack=True)
          


print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()

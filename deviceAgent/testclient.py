import pika,time
from messagestream import delimitingStream,delimitedStream
from wire_pb2 import *
import threading

credentials = pika.PlainCredentials('admin','123456')
connection = pika.BlockingConnection(pika.ConnectionParameters(
    '10.2.1.67',5672,'/',credentials,heartbeat_interval=10))
# connection.add_on_open_callback(open1)
channel = connection.channel()

# 声明queue
# channel.queue_declare(queue='balance',exclusive=True,auto_delete=True)

# n RabbitMQ a message can never be sent directly to the queue, it always needs to go through an exchange.
channel = connection.channel()
channel.exchange_declare(exchange='serverNotify',exchange_type='fanout')
channel.basic_publish(exchange='serverNotify',
                      routing_key='',
                      body='hahahahhaahahahah')
while True:
    time.sleep(1)

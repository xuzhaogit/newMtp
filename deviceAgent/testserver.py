import pika,time
from messagestream import delimitingStream,delimitedStream
from wire_pb2 import *
import multiprocessing

import threading
import eventlet
eventlet.monkey_patch()
# You may ask why we declare the queue again ‒ we have already declared it in our previous code.
# We could avoid that if we were sure that the queue already exists. For example if send.py program
# was run before. But we're not yet sure which program to run first. In such cases it's a good
# practice to repeat declaring the queue in both programs.
# channel.queue_declare(queue='provider',auto_delete=True)


# def callback(ch, method, properties, body):

#     msg=delimitedStream(body)
#     e=Envelope()
#     e.ParseFromString(msg)
#     print(" [x] Received %r %s" %(e.type,time.time()))

def nottt():
    def _callBack(ch, method, properties, body):
        print ('hhahahhahahahahahahahahhahah',body)
        # self.deviceHehehe()
    print ('aaa1')
    credentials = pika.PlainCredentials('admin','123456')
    print ('aaa2')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='10.2.1.67',port=5672,virtual_host='/',credentials=credentials))
    print ('aaa3')
    channel=connection.channel()

    channel.exchange_declare(exchange='serverNotify',exchange_type='fanout')
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='serverNotify',queue=queue_name)
    channel.basic_consume(_callBack,queue=queue_name)
    print ('aaa6')
    print ('reciveNotify thread start')
    channel.start_consuming()


def bbb2():
    # import eventlet
    # eventlet.monkey_patch()
    print ('bbb')
    while True:
        time.sleep(1)
credentials = pika.PlainCredentials('admin','123456')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='10.2.1.67',port=5672,virtual_host='/',credentials=credentials))
channel = connection.channel()
t=threading.Thread(target=nottt)
t.start()
time.sleep(2)
p=multiprocessing.Process(target=bbb2)
p.daemon=True
p.start()
print (t,p)
while True:
    time.sleep(1)
    channel.basic_publish(exchange='',routing_key='provider',body='adsad')
# 2:22:30
# print ('reciveNotify thread start')
# channel.start_consuming()




# channel.basic_consume(callback,
#                       queue='provider',
#                       no_ack=True)

# print(' [*] Waiting for messages. To exit press CTRL+C')

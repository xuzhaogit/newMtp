import pika,time
from deviceAgent.messagestream import delimitingStream,delimitedStream
from deviceAgent.wire_pb2 import *
from multiprocessing import Process
import threading 
import sys

print (sys.path,'b')
from .util import db

# from threading import Thread as Process



class ProviderHandler(Process):
    def __init__(self,config):
        Process.__init__(self)
        self.config=config
        self.heartBeats=0
        self._credentials = pika.PlainCredentials(self.config.MQ_USER,self.config.MQ_PWD)
    def msgCallback(self,ch, method, properties, body):
        msg=delimitedStream(body)
        envelop=Envelope()
        envelop.ParseFromString(msg)
        print (" [x] Received %s"%envelop.type)
        if envelop.type==5:
            self.heartBeats=time.time()
    def ttt(self):
        while True:
            if time.time()-self.heartBeats>4:
                print ('onfline'*10,time.time())
            time.sleep(3)

    def pub_initMessage(self):
        print ('init message')
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            self.config.MQ_HOST,self.config.MQ_PORT,'/',self._credentials,heartbeat=60))
        channel = connection.channel()
        channel.exchange_declare(exchange='serverNotify',exchange_type='fanout')
        channel.basic_publish(exchange='serverNotify',
                              routing_key='',
                              body='hahahahhaahahahah')
        connection.close()
    def run(self):
        # _credentials = pika.PlainCredentials(self.config.MQ_USER,self.config.MQ_PWD)
        _connection = pika.BlockingConnection(pika.ConnectionParameters(
            self.config.MQ_HOST,self.config.MQ_PORT,'/',self._credentials,heartbeat=60))
        _channel = _connection.channel()
        _channel.queue_declare(queue='provider',auto_delete=True)
        _channel.basic_consume(self.msgCallback,queue='provider',)

        self.pub_initMessage()
        target=threading.Thread(target=self.ttt)
        target.daemon=True
        target.start()
        print(' [*] Waiting for messages. To exit press CTRL+C')
        _channel.start_consuming()






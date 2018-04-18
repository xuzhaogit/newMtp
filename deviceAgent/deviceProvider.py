import time,json,logging,signal
import socket,os,sys
sys.path.append('../')
from multiprocessing import Manager,Process
# import multiprocessing
from adbkit import Adbkit
from messagestream import delimitingStream,delimitedStream
from wire_pb2 import *
import pika,json
from config import Config
import threading
# import eventlet
# eventlet.monkey_patch()
from device import aaa,Device


class Provider():
    def __init__(self):
        self.logger = self.initlogging()
        self._hostname = socket.gethostname()
        self._host = self._getHost()
        self._adbkit = Adbkit()
        # self._credentials = pika.PlainCredentials(Config.MQ_USER,Config.MQ_PWD)
        # self._channel = self.connectMQ(self._credentials)

        # m=Manager().dict()
        self.deviceMap2={}

    def initlogging(self):
        logger = logging.getLogger('deviceProvider')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('provider.log')
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger

    def _getHost(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    def connectMQ(self):
        credentials = pika.PlainCredentials(Config.MQ_USER,Config.MQ_PWD)
        connection = pika.BlockingConnection(pika.ConnectionParameters(Config.MQ_HOST,Config.MQ_PORT,'/',credentials))
        channel = connection.channel()
        # channel.queue_declare(queue='provider')
        return channel

    def sentMessage(self,type,msgCls):
        credentials = pika.PlainCredentials(Config.MQ_USER,Config.MQ_PWD)
        connection = pika.BlockingConnection(pika.ConnectionParameters(Config.MQ_HOST,Config.MQ_PORT,'/',credentials))
        channel = connection.channel()
        envelop=Envelope()
        envelop.type=type
        envelop.message=msgCls.SerializeToString()
        message=envelop.SerializeToString()
        body=delimitingStream(message)
        channel.basic_publish(exchange='',routing_key='provider',body=body)
        connection.close()

    def heartBeat(self):
        while True:
            msg=ProviderHeartbeatMsg()
            msg.host=self._host
            msg.deviceList=json.dumps(self.devicesMap)
            self.sentMessage(PROVIDER_HEARTBEAT_MSG,msg)
            time.sleep(3)
            del msg

    def reciveNotify(self):
        def _callBack(ch, method, properties, body):
            print ('hhahahhahahahahahahahahhahah',body)
            self.deviceHehehe(ch)
        cre=pika.PlainCredentials(Config.MQ_USER,Config.MQ_PWD)
        connection = pika.BlockingConnection(pika.ConnectionParameters(Config.MQ_HOST,Config.MQ_PORT,'/',cre))
        channel=connection.channel()
        channel.exchange_declare(exchange='serverNotify',exchange_type='fanout')
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange='serverNotify',queue=queue_name)
        channel.basic_consume(_callBack,queue=queue_name)
        print ('reciveNotify thread start')
        print ('aaa3')
        channel.start_consuming()

    def deviceHehehe(self,ch):
        msg=ProviderRegisterMsg()
        msg.hostname=self._hostname
        msg.host=self._host

        envelop=Envelope()
        envelop.type=PROVIDER_REGISTER_MSG
        envelop.message=msg.SerializeToString()
        message=envelop.SerializeToString()
        body=delimitingStream(message)
        ch.basic_publish(exchange='',routing_key='provider',body=body)
        self._cacheList=[]     

    def deviceAbsent(self,serial):
        msg=DeviceAbsentMsg()
        msg.serial=serial
        p=self.deviceMap2.pop(serial)
        if p:
            p.terminate()
            print ('kill %s'%serial)
        self.sentMessage(DEVICE_ABSENT_MSG,msg)

    def aaa(self):
        print ('start a process')
        while True:
            time.sleep(1)
    def devicePresent(self,serial,status):
        msg=DevicePresentMsg()
        msg.serial=serial
        msg.status=status

        print ('present ',self.deviceMap2)
        d=Device(serial,self.deviceMap2)
        d.daemon=True
        d.start()
        # p=Process(target=aaa,args=(serial,))
        # p.daemon=True
        # p.start()
        self.deviceMap2[serial]=d
        self.sentMessage(DEVICE_PRESENT_MSG,msg)



    def loop(self):
        print ('loop',time.time())
        self.devicesMap=self._adbkit.getAvailableDevices()
        # t=threading.Thread(target=self.heartBeat)
        # t.daemon=True
        # t.start()
        t=threading.Thread(target=self.reciveNotify)
        t.daemon=True
        t.start()
        print (t)
        time.sleep(2)

        _cacheAvaliableList=[]
        _cacheOnlineList=[]
        self._cacheList=[]
        _cacheMap=None
        while True:
            self.devicesMap=self._adbkit.getAvailableDevices()
            devices=list(self.devicesMap.keys())
            presentDevices=list(set(devices).difference(set(self._cacheList)))
            absentDevices=list(set(self._cacheList).difference(set(devices)))
            for d in presentDevices:
                self.devicePresent(d,'online')
                print ('add device %s'%d)
            for d in absentDevices:
                self.deviceAbsent(d)
                print ('remove device %s'%d)

            # msg=ProviderHeartbeatMsg()
            # msg.host=self._host
            # msg.deviceList=json.dumps(self.devicesMap)
            # self.sentMessage(PROVIDER_HEARTBEAT_MSG,msg)

            self._cacheList=devices
            time.sleep(0.5)



    # def loop2(self):
    #     _cachelist=[]
    #     while True:
    #         st=time.time()
    #         devicesMap=self.adbkit.getDevices()

    #         devices=list(d.keys())
    #         if self._cachelist!=devices:
    #             print (self.temp,devices)
    #             new_devices=list(set(devices).difference(set(self.temp)))
    #             remove_devices=list(set(self.temp).difference(set(devices)))
    #             print (_cachelist,devices,new_devices,remove_devices)
    #             if new_devices:
    #                 self.add_devices(new_devices)
    #                 # print ('add',self.temp,devices,new_devices)
    #             if remove_devices:
    #                 self.remove_devices(remove_devices)
    #             # eventlet.spawn(self.add_devices(),new_devices)
    #             # eventlet.spawn(self.remove_devices(),remove_devices)
    #             # t=threading.Thread(target=self.device_update,args=(new_devices,remove_devices))
    #             # t.setDaemon(True)
    #             # t.start()
    #             self.temp=devices
    #             print (self.temp,devices,'fff')
    #         # elif self.default_check_count>3000:
    #         #   t=threading.Thread(target=self.device_default_check,args=(devices,))
    #         #   t.setDaemon(True)
    #         #   t.start()
    #         #   self.default_check_count=0
    #         time.sleep(0.5)
    #         self.default_check_count+=1
    # def add_devices(self,devices):
    #     print ('ADD',devices)
    #     # db.addDevices(devices)
    #     for serial in devices:
    #         ports=self.m.init(serial)
    #     socketio.emit('change','hehe',namespace='/default')
    # def remove_devices(self,devices):
    #     print ('REMOVE',devices)
    #     st=time.time()
    #     db.removeDevices(devices)
    #     socketio.emit('change','hehe',namespace='/default')
    #     print (time.time()-st,'remove')

if __name__=='__main__':
    p=Provider()
    p.loop()
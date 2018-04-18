# from rmqUtil import RmqConnection
from multiprocessing import Process
from openstf.minicap import Minicap
import threading

from adbkit import Adbkit
import socketio
import pika
# from config import Config

import time
# import eventlet
# eventlet.monkey_patch()
def aaa(serial):
    # import eventlet
    # eventlet.monkey_patch()
    d=Device(serial)
    d.run()




class Device(Process):
    def __init__(self,serial,d=None):
        Process.__init__(self)
        self._serial=serial
        self.routing_key='abcd'
        self.d=d
    def heartBeat(self):
        pass


    def startThread(self,fn):
        t=threading.Thread(target=fn)
        t.daemon=True
        t.start()

    def callback(self):
        pass

    def subMessage(self):
        connection=RmqConnection().getConnection()
        channel=connection.channel()
        channel.exchange_declare(exchange='device',exchange_type='direct')
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange='device',queue=queue_name,routing_key=self.routing_key)
        channel.basic_consume(self.callback,queue=queue_name)
        channel.start_consuming()

    def pushMessage(self,type,msgCls):
        envelop=Envelope()
        envelop.type=type
        envelop.message=msgCls.SerializeToString()
        message=envelop.SerializeToString()
        body=delimitingStream(message)
        self.channel.basic_publish(exchange='',routing_key='provider',body=body)  


    def createWebSocketServer(self):
        self.sio = socketio.Server(async_mode='eventlet')
        app = socketio.Middleware(self.sio)
        import eventlet
        eventlet.wsgi.server(eventlet.listen(('', 8000)), app,log_output=False)

    def run(self):
        print ('run device %s'%self._serial)
        self.startThread(self.subMessage)
        self.startThread(self.createWebSocketServer)

        self._credentials = pika.PlainCredentials(Config.MQ_USER,Config.MQ_PWD)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            Config.MQ_HOST,Config.MQ_PORT,'/',self._credentials))
        self.channel = self.connection.channel()


        _device=Adbkit().getDevice(self._serial)
        class Handlers():
            notifyHandler=lambda data: print (data)
            # self.sio.emit('imgdata',data,namespace='/screen')
            dataHandler=lambda data: self.sio.emit('imgdata',data,namespace='/screen')
            rotaionChangeHandler=lambda rotation:print (rotation)
        minicap=Minicap(_device,Handlers,1300)
        minicap.start()
        while True:
            time.sleep(2)
        # print (self.d)
        print ('out device %s'%self._serial)


# eventlet.monkey_patch()
class aaa():
    def ata(self):
        self.sio = socketio.Server(async_mode='tthreading')
        app = socketio.Middleware(self.sio)
        import eventlet
        eventlet.wsgi.server(eventlet.listen(('', 8000)), app,log_output=False)
    def loop(self):
        t=threading.Thread(target=self.ata) 
        t.start()

        time.sleep(1)
        while True:
            time.sleep(1)
            self.sio.emit('imgdata','ddd',namespace='/screen')        
            print ('ddd')    




if __name__=='__main__':
    a=aaa()
    a.loop()











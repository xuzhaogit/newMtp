# # from messagestream import delimitingStream,delimitedStream
# # from wire_pb2 import *
# # import sys,json,time
# # st=time.time()
# # sys.path.append('../')
# # from config import config
# # c=DevicePresentMsg()
# # c.serial='abc'
# # c.status=json.dumps({'a':1})
# # envelop=Envelope()
# # envelop.type=DEVICE_PRESENT_MSG
# # envelop.message=c.SerializeToString()

# # sss=envelop.SerializeToString()
# # print (sss)
# # sss2=delimitingStream(sss)

# # # ss2=b'\x02\x12\x12\n\x08bc7'
# # print (sss2)

# # sss3=delimitedStream(sss2)
# # print (sss3)
# # e=Envelope()
# # e.ParseFromString(sss3)
# # print (e.type)
# # c=DevicePresentMsg()
# # print (c.ParseFromString(e.message))
# # print (json.loads(c.status))
# # print (time.time()-st)

# # import numpy
import threading
import pika
import eventlet,time
eventlet.monkey_patch()

def ttt():
    print ('a')
    credentials = pika.PlainCredentials('admin','123456')
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='10.2.1.67',port=5672,virtual_host='/',credentials=credentials))
    channel = connection.channel()
    print ('b')
credentials = pika.PlainCredentials('admin','123456')
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='10.2.1.67',port=5672,virtual_host='/',credentials=credentials))
channel = connection.channel()
t=threading.Thread(target=ttt)
t.start()
while True:
    time.sleep(1)
# t.join()
# caseList=[]
# import random


# for i in range(10):
#     _temp=[]
#     for i in range(5):
#         name=random.choice(['A','B'])[0]
#         _temp.append('Level%s-%s'%(i+1,name))
#     name=random.choice(['A','B','C','D','E'])[0]
#     casename=''.join(random.sample('abcdefghijklmnopqrstuvwxya',10))
#     _temp.append('case-%s'%casename)

#     caseList.append(_temp)
# # print (caseList)


# # for i in caseList:
# #     print (i)
# s=caseList
# m={}



# maxLevel=len(s[0])
# print (maxLevel,'maxlevel')
# for s1 in s:
#     # m=d
#     for index,s2 in enumerate(s1[:-1]):
#         level=m.get(s2)
#         if not level:
#             m[s2]={}
#         if index==maxLevel-2:
#             m[s2]=s1[-1]
#             break
#         else:
#             m=m[s2]


# print (m)
# # l1=d.keys()
# # print (l1)
# import threading
# import socketio
# import eventlet
# import time
# eventlet.monkey_patch()
# sio = socketio.Server(async_mode='eventlet')
# app = socketio.Middleware(sio)
# import eventlet
# def ttt():
#     print ('ttt')
#     eventlet.wsgi.server(eventlet.listen(('', 8000)), app)
#     print ('ttt2')
# def ttt2():
#     while True:
#         print ('ttt2')
#         time.sleep(2)
# pool = eventlet.GreenPool()
# t=pool.spawn_n(ttt2)
# t=pool.spawn(ttt)
# # t.start()
# # t.daemon=True
# # t.start()
# for i in range(20):
#     # sio.emit('imgdata','aaa',namespace='/screen')
#     print ('emit')
#     time.sleep(1)
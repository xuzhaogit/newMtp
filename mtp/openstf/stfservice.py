import logging
import stfutil
from . import stfutil
from .error import *
import queue
import time
import threading
import socket
from .wire_pb2 import *
from .messagestream import *
import traceback
import google.protobuf.message

class STFService():
    def __init__(self,device,handlers,rotaionChangeHandler,localPort,logger=None,timeout=3600):
        self.device=device
        self.handlers=handlers
        self.rotaionChangeHandler=rotaionChangeHandler
        self.localPort=localPort
        self.logger=logger if logger else self.__getlogger()
        self.timeout=timeout

        self.resourceInfo=self.__getResourceInfo()
        self.desiredState=stfutil.StateQueue()
        self.serviceQueue=queue.Queue(500)

        self.runningStatus=stfutil.STOPPED
        self.sendStatus=stfutil.STOPPED
        self.monitorStatus=stfutil.STOPPED

        self.response={}
        self.__stfagentProcess=None
        
        self.StreamHandler=StreamHandler()
    def __getlogger(self):
        logger=logging.getLogger('[stfservice:%s]'%self.device.serial)
        if not logger.handlers:
            formatter=logging.Formatter('%(asctime)s-%(filename)s:%(lineno)s-%(levelname)s---#%(name)s:%(message)s')
            stream_handler=logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
            logger.setLevel(logging.DEBUG)
        return logger

    # notify
    def __notify(self,event,data={}):
        self.logger.info('STFSERVICE %s %s'%(event,data))
        self.handlers.notifyHandler({'event':event,'data':data})

    def __getResourceInfo(self):
        return {
            'requiredVersion': '1.0.2',
            'pkg': 'jp.co.cyberagent.stf',
            'main': 'jp.co.cyberagent.stf.Agent',
            'apk': 'mtp/vendor/STFService/STFService.apk',
            'startIntent': {
                'action': 'jp.co.cyberagent.stf.ACTION_START',
                'component': 'jp.co.cyberagent.stf/.Service'
            }
        }

    # check STfservice.apk is installed
    def __isInstalledSTFserviceResource(self):
        output=self.device.shell('pm list packages').strip()
        return True if self.resourceInfo['pkg'] in output else False

    # install STfservice.apk
    def installSTFserviceResource(self,replace=False):
        if replace or not self.__isInstalledSTFserviceResource():
            res=self.device.install(self.resourceInfo['apk'])
            if res:
                self.logger.debug('install stfservice resource')
            else:
                raise STFserviceError('stfservice install failed')

    # check STFservice is started
    def __isStartedSTFservice(self):
        output=self.device.shell("ps |grep 'jp.co.cyberagent.stf' |grep -v grep").strip()
        if not output:
            return None
        output = output.split('\n')
        if len(output)>1:
            pids=[o.split()[1] for o in output]
            self.logger.warning('get multi stfservice pid%s'%pids)
            return pids
        else:
            return output[0].split()[1]

    # check STFagent is istarted
    def __isStartedSTFagent(self):
        output=self.device.shell("ps |grep 'stf.agent' |grep -v grep").strip()
        if not output:
            return None
        output = output.split('\n')
        if len(output)>1:
            pids=[o.split()[1] for o in output]
            self.logger.warning('get multi stfagent pid%s'%pids)
            return pids
        else:
            return output[0].split()[1]

    # kill stfservice service
    def __killSTFservice(self,pid=None):
        pid = pid if pid else self.__isStartedSTFservice()
        if pid:
            self.device.shell("am force-stop '%s'"%self.resourceInfo['pkg'])
            self.logger.debug('kill stfservice')

    # kill STFagent
    def __killSTFagent(self,pid=None):
        pid = pid if pid else self.__isStartedSTFagent()
        if pid:
            if type(pid)==list:
                for subpid in pid:                    
                    self.device.shell('kill -9 %s'%subpid)
                    self.logger.debug('kill stfagent service: %s'%subpid)
            else:
                self.device.shell('kill -9 %s'%pid)
                self.logger.debug('kill stfagent service: %s'%pid)        

    # start stf service and agent
    def __startSTFservice(self):
        if not self.__isInstalledSTFserviceResource():
            raise STFserviceError('stfservice can not found')
        self.__killSTFservice()
        self.__killSTFagent()
        self.device.shell("am startservice --user 0 -a '%s' -n '%s'"%(self.resourceInfo['startIntent']['action'],self.resourceInfo['startIntent']['component']),nowait=True)
        output=self.device.shell("pm path %s"%self.resourceInfo['pkg']).strip()
        if not output:
            raise STFserviceError('stfservice can not found')
        pkgpath=output.split(':')[-1]
        self.__stfagentProcess=self.device.shell("export CLASSPATH='%s'\; \exec app_process /system/bin '%s'"%(pkgpath,self.resourceInfo['main']),nowait=True)

    # adb forward
    def _adbForwardSTFservice(self,localPort):
        self.device.forward('tcp:%s'%localPort,'localabstract:stfservice')
        self.logger.debug('add adb forward %s'%localPort)

    # adb forward
    def _adbForwardSTFagent(self,localPort):
        self.device.forward('tcp:%s'%(localPort+1),'localabstract:stfagent')
        self.logger.debug('add adb forward %s'%(localPort+1))

    # remove forward socket connection
    def _removeAdbForwardSTFservice(self,localPort):
        self.device.forward_remove('tcp:%s'%localPort)
        self.logger.debug('remove adb forward %s'%localPort) 

    # remove forward socket connection
    def _removeAdbForwardSTFagent(self,localPort):
        self.device.forward_remove('tcp:%s'%(localPort+1))
        self.logger.debug('remove adb forward %s'%(localPort+1)) 

    # event handler
    def eventHandler(self,stream):
        data=self.StreamHandler.delimitedStream(stream)
        envelop=Envelope()
        if not data:
            self.logger.warning('data empty')
            return
            # raise PbDecodeError()
        envelop.ParseFromString(data)
        if envelop.id:
            self.response[str(envelop.id)]=envelop
        else:
            etype=envelop.type
            if etype==EVENT_BATTERY:
                temp=BatteryEvent()
                temp.ParseFromString(envelop.message)
                self.logger.info('BatteryEvent %s %s %s %s'%(temp.status,temp.health,temp.level,type(temp)))
            elif etype==EVENT_AIRPLANE_MODE:
                temp=AirplaneModeEvent()
                temp.ParseFromString(envelop.message)
                self.logger.info('AirplaneModeEvent %s'%temp.enabled)
            elif etype==EVENT_BROWSER_PACKAGE:
                temp=BrowserPackageEvent()
                temp.ParseFromString(envelop.message)
                self.logger.info('BrowserPackageEvent %s'%temp.selected)
                for app in temp.apps:
                    self.logger.info('app %s %s'%(app.name,app.component))
            elif etype==EVENT_CONNECTIVITY:
                temp=ConnectivityEvent()
                temp.ParseFromString(envelop.message)
                self.logger.info('ConnectivityEvent %s'%temp.connected)
            elif etype==EVENT_PHONE_STATE:
                temp=PhoneStateEvent()
                temp.ParseFromString(envelop.message)
                self.logger.info('PhoneStateEvent %s'%temp.state)
            elif etype==EVENT_ROTATION:
                temp=RotationEvent()
                temp.ParseFromString(envelop.message)
                self.__notify('rotationChange',{'rotation':temp.rotation})
                self.handlers.rotaionChangeHandler(temp.rotation)
                self.logger.info('RotationEvent %s'%temp.rotation)
            elif etype==DO_IDENTIFY:
                temp=DoIdentifyResponse()
                temp.ParseFromString(envelop.message)
                self.logger.info('IdentifyResponse %s'%temp.success)
            else:
                self.logger.info('unKnown event %s'%envelop.type)

    # connect STF service & agent
    def __connectService(self):
        localPort = self.localPort or 1100
        self._adbForwardSTFservice(localPort)
        self._adbForwardSTFagent(localPort)
        time.sleep(0.5)
        _s_service=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        _s_service.connect(('localhost',localPort))
        # _s_service.settimeout(0.5)

        def _monitor():
            _isError=False
            self.monitorStatus=stfutil.STARTED
            self.logger.debug('(monitor thread): STARTED')
            try:
                timeout=time.time()+self.timeout
                while self.runningStatus!=stfutil.STOPPING and time.time()<timeout:
                    try:
                        data=_s_service.recv(1024)
                        if data:
                            self.eventHandler(data)
                        else:
                            if self.__isStartedSTFservice():
                                time.sleep(0.5)
                            else:
                                raise STFserviceError('stf service already dead & get empty socket data')
                    except socket.timeout:
                        pass
                else:
                    if time.time()>timeout:
                        raise STFserviceError('timeout')

                    # except PbDecodeError as e: 
                    #     self.logger.debug('protobuf decode warning %s data:%s'%(e,data))
                    #     data+=_s_service.recv(1024)
                    #     self.eventHandler(data)
                    # except google.protobuf.message.DecodeError as e: 
                    #     self.logger.debug('protobuf decode warning %s data:%s'%(e,data))
                    #     data+=_s_service.recv(1024)
                    #     self.eventHandler(data)
            except Exception as e:
                if  self.runningStatus!=stfutil.STOPPING and self.sendStatus==stfutil.STARTED:
                    _isError=True
                    traceback.print_exc()
                    self.logger.error('data:%s error:%s'%(data,e))
            finally:
                self.logger.debug('(monitor thread): STOPED')
                self._removeAdbForwardSTFservice(localPort)
                self.monitorStatus=stfutil.STOPPED
                _s_service.close()
            if _isError:
                self.__stopSTFservice()

        t=threading.Thread(target=_monitor)
        t.setDaemon(True)
        t.start()


        _s_agent=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        _s_agent.connect(('localhost',localPort+1))     

        def _send():
            _isError=False
            self.sendStatus=stfutil.STARTED
            self.logger.debug('(send thread): STARTED')
            try:
                while self.monitorStatus==stfutil.STARTED:
                    try:
                        data=self.serviceQueue.get(timeout=0.01)
                        if data[0]=='agent':
                            _s_agent.send(data[1])
                        else:
                            _s_service.send(data[1])
                    except queue.Empty:
                        if self.__stfagentProcess.poll() is None:
                            continue
                        else:
                            raise STFserviceError('stf agent service already dead')                    
            except Exception as e:
                if self.runningStatus!=stfutil.STOPPING and self.monitorStatus==stfutil.STARTED:
                    _isError=True
                    if self.__stfagentProcess.poll() is None:
                        self.__stfagentProcess.kill()
                        self.logger.error('(send thread): ERROR %s, kill stf agent service myself'%str(e).strip())
                    else:
                        self.logger.debug('%s'%self.__stfagentProcess.stdout.read())
                        self.logger.error('(send thread): ERROR %s, stf agent service already dead'%str(e).strip())
            finally:
                _s_agent.close()
                self._removeAdbForwardSTFagent(localPort)
                self.logger.debug('(send thread): STOPPED')
                self.sendStatus=stfutil.STOPPED
                if _isError:
                    self.__stopSTFservice()            

        t=threading.Thread(target=_send)
        t.setDaemon(True)
        t.start()

    # stop STF service & agent
    def __stopSTFservice(self,pid=None):
        self.__killSTFservice()
        self.__killSTFagent()
        # self.pid=None
        for i in range(40):
            if self.sendStatus==stfutil.STOPPED and self.monitorStatus==stfutil.STOPPED and self.runningStatus!=stfutil.STOPPED : 
                self.runningStatus=stfutil.STOPPED           
                self.__notify('STOPPED')
                break
            else:
                time.sleep(0.05)
        else:
            self.logger.warning("stop stf service timeout")


    def _ensureState(self):
        if self.desiredState.isEmpty():
            return
        if self.runningStatus==stfutil.STARTING or self.runningStatus==stfutil.STOPPING:
            self.logger.warning('WAIT')
            return 
        elif self.runningStatus==stfutil.STOPPED:
            if self.desiredState.get()=='START':
                try:
                    self.runningStatus=stfutil.STARTING
                    self.__startSTFservice()
                    self.__connectService()
                    self.runningStatus=stfutil.STARTED
                    self.__notify('STARTED')
                except Exception as e:
                    if self.runningStatus!=stfutil.STOPPED:
                        traceback.print_exc()
                        self.logger.error('stfservice start failed: %s'%str(e))
                        self.runningStatus=stfutil.STOPPING
                        self.__stopSTFservice()
                finally:
                    self._ensureState()
            else:
                self.logger.warning('get STOP command but service is stopped')
        elif self.runningStatus==stfutil.STARTED:
            if self.desiredState.get()=='STOP':
                try:
                    self.runningStatus=stfutil.STOPPING
                    self.__stopSTFservice()
                finally:
                    self._ensureState()
            else:
                self.logger.warning('get START command but service is started')

    def __getResponse(self,mid):
        for i in range(10):
            envelop=self.response.pop(str(mid),None)
            if envelop:
                if envelop.type==GET_PROPERTIES:
                    temp=GetPropertiesResponse()
                    temp.ParseFromString(envelop.message)
                    self.phone=temp.properties
                    return (temp)
                elif envelop.type==GET_BROWSERS:
                    temp=GetBrowsersResponse()
                    temp.ParseFromString(envelop.message)
                    return (temp,temp.selected)
                elif envelop.type==SET_KEYGUARD_STATE:
                    temp=SetKeyguardStateResponse()
                    temp.ParseFromString(envelop.message)
                    return (temp)                    
                else:
                    return ('else response')
                    return
                break
            else:
                time.sleep(0.1)
        else:
            return 'can not get response'

    def __runAgentCommand(self,type,message):
        envelop=Envelope()
        envelop.type=type
        envelop.message=message
        self.serviceQueue.put(['agent',delimitingStream(envelop.SerializeToString())])

    def __runServiceCommand(self,mid,typeT,message):
        envelop=Envelope()
        envelop.type=typeT
        envelop.message=message
        envelop.id=mid
        self.serviceQueue.put(['service',delimitingStream(envelop.SerializeToString())])
        return self.__getResponse(mid)

    def getProperties(self,data):
        d=GetPropertiesRequest()
        d.properties.extend([
            'imei', 'phoneNumber', 'iccid', 'network'
        ])
        mid='%s%s'%((time.time()*1000000),random.randint(10001,99999))
        res=self.__runServiceCommand(mid,GET_PROPERTIES,d.SerializeToString())
        self.logger.info('get response: %s'%res)
        return res

    def GetBrowsersRequest(self,data):
        d=GetBrowsersRequest()
        mid='%s%s'%((time.time()*1000000),random.randint(10001,99999))
        res=self.__runServiceCommand(mid,GET_PROPERTIES,d.SerializeToString())
        self.logger.info('get response: %s'%res)
        return res
    def setlockStatue(self,data):

        d=SetKeyguardStateRequest()
        if data['enabled']==True or data['enabled']=='true':
            d.enabled=True
        else:
            d.enabled=False
        mid='%s%s'%((time.time()*1000000),random.randint(10001,99999))
        res=self.__runServiceCommand(mid,GET_PROPERTIES,d.SerializeToString())
        self.logger.info('get response: %s'%res)
        return res


    def __getkey(self,keyname):
        key=stfutil.keyMap.get('KEYCODE_'+keyname.upper())
        if key:
            return key
        else:
            self.logger.warning('unKnown key:%s'%keyname)
            return None

    def type(self,data):
        d=DoTypeRequest()
        d.text=data['text']
        self.runAgentCommand(DO_TYPE,d.SerializeToString())

    def keyDown(self,data):
        d=KeyEventRequest()
        d.event=DOWN
        key=self.__getkey(data['key'])
        if key:
            d.keyCode=key   
            self.__runAgentCommand(DO_KEYEVENT,d.SerializeToString())
            
    def keyUp(self,data):
        d=KeyEventRequest()
        d.event=UP
        key=self.__getkey(data['key'])
        if key:
            d.keyCode=key   
            self.__runAgentCommand(DO_KEYEVENT,d.SerializeToString())

    def keyPress(self,data):
        print('home',time.time())
        d=KeyEventRequest()
        d.event=PRESS
        key=self.__getkey(data['key'])
        if key:
            d.keyCode=key   
            self.__runAgentCommand(DO_KEYEVENT,d.SerializeToString())

    def wake(self,data):
        d=DoWakeRequest()
        self.__runAgentCommand(DO_WAKE,d.SerializeToString())


    def rotate(self,data):
        d=SetRotationRequest()
        d.rotation=data['rotation']
        d.lock=data['lock']
        self.__runAgentCommand(SET_ROTATION,d.SerializeToString())



    def start(self):
        self.logger.info('STFSERVICE STARTING')
        self.desiredState.push('START')
        self._ensureState()
    def stop(self):
        self.logger.info('STFSERVICE STOPPING')
        self.desiredState.push('STOP')
        self._ensureState()
    def restart(self):
        self.stop()
        self.start()

if __name__=='__main__':

    import sys
    sys.path.append('../')
    from adbkit.adbkit import Adbkit
    serial='bc766a71'
    device=Adbkit().getDevice(serial)
    m=STFService(device)
    m.startSTFservice()




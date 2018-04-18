import logging
from . import stfutil
from .error import *
import queue
import time
import threading
import socket

class Minitouch():
    def __init__(self,device,handlers,localPort=1111,logger=None):
        self.device=device
        self.logger=logger if logger else self.__getlogger()
        self.resourceInfo=self.__getResourceInfo(device.deviceInfo)
        self.__minitouchProcess=None
        self.__pid=None
        self.runningStatus=stfutil.STOPPED
        self.localPort=localPort
        self.desiredState=stfutil.StateQueue()
        self.touchQueue=queue.Queue(500)

        self.sendStatus=stfutil.STOPPED
        self.actionStatus=None
        self.handlers=handlers

    def __getlogger(self):
        logger=logging.getLogger('[minitouch:%s]'%self.device.serial)
        if not logger.handlers:
            formatter=logging.Formatter('%(asctime)s-%(filename)s:%(lineno)s-%(levelname)s---#%(name)s:%(message)s')
            stream_handler=logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
            logger.setLevel(logging.DEBUG)
        return logger
    # notify 
    def __notify(self,event,data={}):
        self.logger.info('MINITOUCH %s %s'%(event,data))
        self.handlers.notifyHandler({'event':event,'data':data})

    def __getResourceInfo(self,deviceInfo):
        return {
            'bin':{
                'src':'mtp/vendor/minitouch/%s/minitouch%s'%(deviceInfo.abi,deviceInfo.bin),
                'dest': '/data/local/tmp/minitouch',
                'comm':'minitouch',
                'mode':'' #0755 对应新版adb。。。待查
            }
        }

    # check minitouch resource is installed 
    def __isInstalledMinitouchResource(self):
        output=self.device.shell('ls "%s"'%self.resourceInfo['bin']['dest']).strip()
        return True if "No such file or directory" not in output else False

    # install minitouch resource 
    def installMinitouchResource(self,replace=False):
        if replace or not self.__isInstalledMinitouchResource():
            res=self.device.push(self.resourceInfo['bin']['src'],self.resourceInfo['bin']['dest'])
            if res:
                self.logger.debug('install minitouch resource')
            else:
                raise MinitouchError('minitouch install failed')

    # check minitouch service is started
    def __isStartedMinitouch(self):
        output=self.device.shell('ps |grep %s |grep -v grep'%self.resourceInfo['bin']['comm']).strip()
        if not output:
            return None
        output = output.split('\n')
        if len(output)>1:
            pids=[o.split()[1] for o in output]
            self.logger.warning('get multi minitouch pid%s'%pids)
            return pids
        else:
            return output[0].split()[1]

    # kill minitouch service
    def __killminitouch(self,pid=None):
        pid = pid if pid else self.__isStartedMinitouch()
        if pid:
            if type(pid)==list:
                for subpid in pid:                    
                    self.device.shell('kill -9 %s'%subpid)
                    self.logger.debug('kill minitouch service: %s'%subpid)
            else:
                self.device.shell('kill -9 %s'%pid)
                self.logger.debug('kill minitouch service: %s'%pid)

    # start minitouch service
    def __startMinitouch(self):
        if not self.__isInstalledMinitouchResource():
            raise MinitouchError('minitouch can not found')
        if self.__minitouchProcess:
            self.__minitouchProcess.kill()
        # if self.__isStartedMinitouch():
        self.__killminitouch()
        self.__minitouchProcess=self.device.shell('exec %s'%self.resourceInfo['bin']['dest'],nowait=True)
        if self.__minitouchProcess.poll() is not None:
            raise MinitouchError('start minitouch failed')

    # adb forward
    def _adbForward(self,localPort):
        self.device.forward('tcp:%s'%localPort,'localabstract:minitouch')
        time.sleep(0.7)
        self.logger.debug('add adb forward %s'%localPort)

    # remove forward socket connection
    def _removeAdbForward(self,localPort):
        self.device.forward_remove('tcp:%s'%localPort)
        self.logger.debug('remove adb forward %s'%localPort) 

    # connect minitouch
    def __connectService(self):
        localPort = self.localPort or 1313
        self._adbForward(localPort)

        _s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        _s.settimeout(0.05)
        time.sleep(0.2)
        _s.connect(('localhost',localPort))
        data=b''
        # make sure the recv data is completed
        for i in range(10):
            try:
                data+=_s.recv(64)
            except:
                break
        assert data,'minitouch recv data is empty'
        infos=data.decode('utf-8').split('\n')
        # version=infos[0].split(' ')[1]
        max_contacts=float(infos[1].split(' ')[1])
        self.max_x=int(infos[1].split(' ')[2])
        self.max_y=int(infos[1].split(' ')[3])
        self.max_pressure=int(infos[1].split(' ')[4])
        self.__pid=int(infos[2].split(' ')[1])
        self.logger.debug('start minitouch service::%s'%(self.__pid))

        def __send():
            _isError=False
            self.sendStatus=stfutil.STARTED
            self.logger.debug('(send thread): STARTED')
            try:
                while self.runningStatus!=stfutil.STOPPING:
                    try:
                        data=self.touchQueue.get(timeout=0.01)
                        _s.send(data)
                    except queue.Empty:
                        if self.__minitouchProcess.poll() is None:
                            continue
                        else:
                            raise MinitouchError('minitouch service is dead')  
            except Exception as e:
                if not self.runningStatus==stfutil.STOPPING:
                    _isError=True
                    if self.__minitouchProcess.poll() is None:
                        self.__minitouchProcess.kill()
                        self.logger.error('(send thread): ERROR %s, kill minitouch service myself'%str(e).strip())
                    else:
                        self.logger.debug('%s'%self.__minitouchProcess.stdout.read())
                        self.logger.error('(send thread): ERROR %s, minitouch service already dead'%str(e).strip())
            finally:
                _s.close()
                self._removeAdbForward(localPort)
                self.logger.debug('(send thread): STOPPED')
                self.sendStatus=stfutil.STOPPED
                if _isError:
                    self.__stopMinitouch()
        t=threading.Thread(target=__send)
        t.setDaemon(True)
        t.start()

    # stop minitouch service
    def __stopMinitouch(self,pid=None):
        # if self.__isStartedMinitouch():
        self.__killminitouch(pid)
        self.__pid=None
        for i in range(20):
            if self.sendStatus==stfutil.STOPPED and self.runningStatus!=stfutil.STOPPED : 
                self.runningStatus=stfutil.STOPPED           
                self.__notify('STOPPED')
                break
            else:
                time.sleep(0.05)
        else:
            self.logger.warning("stop minitouch timeout")

    # loop
    def _ensureState(self):
        if self.desiredState.isEmpty():
            return
        if self.runningStatus==stfutil.STARTING or self.runningStatus==stfutil.STOPPING:
            self.logger.debug('WAIT')
            return 
        elif self.runningStatus==stfutil.STOPPED:
            if self.desiredState.get()=='START':
                try:
                    self.runningStatus=stfutil.STARTING
                    self.__startMinitouch()
                    self.__connectService()
                    self.runningStatus=stfutil.STARTED
                    self.__notify('STARTED')
                except Exception as e:
                    if self.runningStatus!=stfutil.STOPPED:
                        self.logger.error('minicap start failed: %s'%str(e))
                        self.runningStatus=stfutil.STOPPING
                        self.__stopMinitouch(self.__pid)
                finally:
                    self._ensureState()
            else:
                self.logger.warning('get STOP command but service is stopped')
        elif self.runningStatus==stfutil.STARTED:
            if self.desiredState.get()=='STOP':
                try:
                    self.runningStatus=stfutil.STOPPING
                    self.__stopMinitouch(self.__pid)
                finally:
                    self._ensureState()
            else:
                self.logger.warning('get START command but service is started')
                # socketio.emit('system','start fail',self.namespace)

    def start(self):
        self.logger.info('MINITOUCH STARTING')
        self.desiredState.push('START')
        self._ensureState()
    def stop(self):
        self.logger.info('MINITOUCH STOPPING')
        self.desiredState.push('STOP')
        self._ensureState()
    def restart(self):
        self.stop()
        self.start()

    def gestureStart(self,seq):
        self.actionStatus=True
    def gestureStop(self,seq):
        self.actionStatus=False
    def touchDown(self,point):
        socketData='d %s %s %s %s\n'%(point['contact'],round(point['x']*self.max_x),round(point['y']*self.max_y),round((point['pressure'] or 0.5)*self.max_pressure))
        if self.actionStatus:
            self.touchQueue.put(socketData.encode('ascii'))
    def touchMove(self,point):
        socketData='m %s %s %s %s\n'%(point['contact'],round(point['x']*self.max_x),round(point['y']*self.max_y),round((point['pressure'] or 0.5)*self.max_pressure))
        if self.actionStatus:
            self.touchQueue.put(socketData.encode('ascii'))
    def touchUp(self,point):
        socketData='u %s\n'%point['contact']
        if self.actionStatus:
            self.touchQueue.put(socketData.encode('ascii'))
    def touchCommit(self,data):
        if self.actionStatus:
            self.touchQueue.put('c\n'.encode('ascii'))
    def touchReset(self,data):
        if self.actionStatus:
            self.touchQueue.put('r\n'.encode('ascii'))

if __name__=='__main__':
    import sys
    sys.path.append('../')
    from adbkit.adbkit import Adbkit
    serial='bc766a71'
    device=Adbkit().getDevice(serial)
    m=Minitouch(device)
    m.installMinitouchResource()
    m.start()
    time.sleep(10)



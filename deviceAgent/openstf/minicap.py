import struct
import traceback
import logging
from . import stfutil
from .error import *
import queue
import time
import threading
import socket
import queue
import numpy as np
import aircv as ac
import cv2,json
import multiprocessing
import eventlet



def alpha_blend(lhs_img, rhs_img, alpha):
    # Convert uint8 to float
    #lhs_img = lhs_img.astype(float)
    #rhs_img = rhs_img.astype(float)                
    final_img = cv2.addWeighted(lhs_img, alpha, rhs_img, 1.0-alpha, 0.0)    
    return final_img

class Minicap():
    def __init__(self,device,handlers,localPort,logger=None):
        self.device=device
        self.handlers=handlers
        self.localPort=localPort
        self.logger=logger if logger else self.__getlogger()

        self.deviceInfo=device.deviceInfo
        self.resourceInfo=self.__getResourceInfo(self.deviceInfo)
        self.desiredState=stfutil.StateQueue()
        self.frameConfig=None
        self.__minicapProcess=None
        self.__pid=None
        self.__runningStatus=stfutil.STOPPED
        self.recvStatus=stfutil.STOPPED
        self.processStatus=stfutil.STOPPED

        self.diffStatus=stfutil.STOPPED

        self.restartFlag=False
        self.timeout=None

        self.screen=None
        self.screenShot=None

        self.diffQ=queue.Queue()

        self.diffTurn=False
    def getScreenShot(self):
        if not self.screen:
            raise MinicapError('current screen not found')
        self.screenShot=self.screen
        return self.screenShot
        # filename='/data/local/tmp/minicap_%s.jpg'%random.randint(1,100)
        # if self.frameConfig:
        #     output=self.device.shell('LD_LIBRARY_PATH=/data/local/tmp/ exec %s -P %s -s > %s'%(self.resourceInfo['bin']['dest'],self.frameConfig,filename))
        #     self.device.pull(filename,a.jpg)
        #     self.device.shell('rm -f %s'%filename)
        #     self.logger.info('screenshot: %s'%output)
    def save(self):
        print ('save')
        # arr = np.fromstring(self.imgData, np.uint8)
        # img = cv2.imdecode(arr,cv2.IMREAD_COLOR)
        self.screenShot=self.screen
    @staticmethod
    def diff_pixel(lhs_pixel, rhs_pixel,diffColor,offset=12):
        if diffColor:
            if abs(lhs_pixel[0]-rhs_pixel[0])<=offset and abs(lhs_pixel[1] - rhs_pixel[1])<=offset and abs(lhs_pixel[2]-rhs_pixel[2])<=offset:
                return True
            else:
                return False
        else:
            difference=lhs_pixel-rhs_pixel if lhs_pixel>rhs_pixel else rhs_pixel-lhs_pixel
            if difference<=offset :
                return True
            else:
                # print (lhs_pixel,rhs_pixel)
                return False

    def diffScreen(self,method='pixel',position=None,diffColor=False,debug=False,resize=0.3):
        st0=time.time()
        if not self.screenShot or not self.screen:
            raise MinicapError('no found jpg')
        if not position:
            if not self.frameConfig:
                raise MinicapError('no found frameconfig')
            x,y=0,0
            x2=x+self.frameConfig.realWidth
            y2=y+self.frameConfig.realHeight
        else:
            position=json.loads(position)
            x,y=int(position['x']),int(position['y'])
            x2,y2=x+int(position['width']),y+int(position['height'])

        mode=cv2.IMREAD_COLOR if method!='pixel' or diffColor else cv2.IMREAD_GRAYSCALE
        currentScreen=cv2.imdecode(np.fromstring(self.screen, np.uint8),mode)
        screenShot=cv2.imdecode(np.fromstring(self.screenShot, np.uint8),mode)
        if resize:
            currentScreen=cv2.resize(currentScreen,None,fx=resize,fy=resize,interpolation=cv2.INTER_AREA)
            screenShot=cv2.resize(screenShot,None,fx=resize,fy=resize,interpolation=cv2.INTER_AREA)
            x,y,x2,y2=int(x*resize),int(y*resize),int(x2*resize),int(y2*resize)
        if position:
            screenShot=screenShot[y:y2,x:x2]
            
        if method=='pixel':
            _diffFlag=True
            currentScreen=currentScreen[y:y2,x:x2]
            diff_blend_img = cv2.absdiff(currentScreen,screenShot)
            differenceArr=np.where(diff_blend_img>10)
            difference=np.sum(differenceArr)
            if difference>0:
                _diffFlag=False
            else:
                _diffFlag=True
            print ('finish',time.time()-st0)
            if debug:
                diff_blend_img = alpha_blend(currentScreen, diff_blend_img, 0.40)
                cv2.imwrite('a.jpg', diff_blend_img)
                cv2.imwrite('b.jpg', currentScreen)
                cv2.imwrite('c.jpg', screenShot)
            return _diffFlag
        else:
            ret=ac.find_template(currentScreen,screenShot)
            print ('finish2',time.time()-st0)
            if not ret:
                return False
            else:
                print (ret)
                rectangle=ret['rectangle']
                confidence=ret['confidence']
                if debug:
                    cv2.imwrite('b.jpg', currentScreen)
                    diff_blend_img=cv2.rectangle(currentScreen, rectangle[0],rectangle[-1], (0,255,0), 5)
                    cv2.imwrite('a.jpg', diff_blend_img)
                    cv2.imwrite('c.jpg', screenShot)
                if confidence<0.85:
                    return False
                else:
                    return True 

    def autoDiff(self,name,position,method,baseline=None,timeout=15):
        print ('autoDiff')
        baseline=self.screenShot
        baseTime=time.time()
        timeout=baseTime+timeout
        if self.diffStatus==stfutil.STOPPED:
            self.logger.info('start diff2 thread')
            p=threading.Thread(target=self.autoDiff2)
            p.setDaemon(True)
            p.start()

        self.diffQ.put({'act':0,'name':name,'baseline':baseline,"baseTime":baseTime,'timeout':timeout,'method':method,'position':position})
        stamptemp=time.time()
        self.diffQ.put({'time':stamptemp,'data':self.screen,'act':1})
        print ('put start',stamptemp,time.time())

    def autoDiff2(self,resize=0.3):
        self.diffStatus=stfutil.STARTED
        _diffMap2={}
        print ('init'*200)
        def _difff(screen,screenshot_np,position,method):
            _isMatch=None
            if method=='pixel':
                screen_np=cv2.imdecode(np.fromstring(screen, np.uint8),cv2.IMREAD_GRAYSCALE)
                if resize:
                    screen_np=cv2.resize(screen_np,None,fx=resize,fy=resize,interpolation=cv2.INTER_AREA)
                screen_np=screen_np[y:y2,x:x2]
                diff_blend_img = cv2.absdiff(screen_np,screenshot_np)
                differenceArr=np.where(diff_blend_img>10)
                difference=np.sum(differenceArr)
                if difference>0:
                    # print (difference)
                    _isMatch= False
                else:
                    _isMatch= True
                return _isMatch
            else:
                screen_np=cv2.imdecode(np.fromstring(screen, np.uint8),cv2.IMREAD_COLOR)
                if resize:
                    screen_np=cv2.resize(screen_np,None,fx=resize,fy=resize,interpolation=cv2.INTER_AREA)
                ret=ac.find_template(screen_np,screenshot_np)
                if not ret:
                    return False
                else:
                    print (ret)
                    confidence=ret['confidence']
                    if confidence<0.9:
                        return False
                    else:

                        return True            


        while True:
            try:

                datas=self.diffQ.get(timeout=0.01)
                if not datas:
                    print ('fuck you')
                # print (_diffMap2.keys(),'checkbefore')

                if datas['act']==0:
                    print ('get start')
                    self.diffTurn=True
                    name=datas['name']
                    baseline,baseTime,method,position=datas['baseline'],datas['baseTime'],datas['method'],datas['position']
                    mode=cv2.IMREAD_COLOR if method!='pixel' else cv2.IMREAD_GRAYSCALE
                    baseline=cv2.imdecode(np.fromstring(baseline, np.uint8),mode)
                    position=json.loads(position)
                    x,y=int(position['x']),int(position['y'])
                    x2,y2=x+int(position['width']),y+int(position['height'])
                    if resize:
                        baseline=cv2.resize(baseline,None,fx=resize,fy=resize,interpolation=cv2.INTER_AREA)
                        x,y,x2,y2=int(x*resize),int(y*resize),int(x2*resize),int(y2*resize)
                    baseline=baseline[y:y2,x:x2]
                    _diffMap2[datas['timeout']]={'name':name,'baseline':baseline,"baseTime":baseTime,'method':method,'position':{'x':x,'y':y,'x2':x2,'y2':y2}}
                elif datas['act']==1:
                    if not _diffMap2:
                        print ('no map close turn')
                        self.diffTurn=False
                        continue
                    screenTime=datas['time']
                    timeoutList=list(_diffMap2.keys())

                    for timeout in timeoutList:
                        baseTime=_diffMap2[timeout]['baseTime']
                        if screenTime>timeout:
                            print ('fff2')
                            self.__diffResponse({'res':False,'time':time.time()-baseTime})
                            _diffMap2.pop(timeout)
                            continue
                        screen=datas['data']
                        baseline=_diffMap2[timeout]['baseline']
                        position=_diffMap2[timeout]['position']
                        method=_diffMap2[timeout]['method']
                        ret=_difff(screen,baseline,position,method)
                        # print ('ret',ret)
                        if ret:
                            print ('fff3')
                            self.__diffResponse({'res':True,'time':screenTime-baseTime})
                            _diffMap2.pop(timeout)
                        else:
                            pass
                            # print ('ignore')
            except queue.Empty:

                if not _diffMap2:
                    # self.diffTurn=False
                    continue
                timeoutList=list(_diffMap2.keys())
                for timeout in timeoutList:
                    baseTime=_diffMap2[timeout]['baseTime']
                    if time.time()>timeout:
                        print ('fff')
                        self.__diffResponse({'res':False,'time':time.time()-baseTime,'exe':1})
                        _diffMap2.pop(timeout)
                # time.sleep(0.01)
                # continue

        self.diffStatus=stfutil.STOPPED

    def diff(self,name,position,method,baseline=None,timeout=5):
        print (position,'autodiff')
        baseline=self.screenShot
        baseTime=time.time()
        _timeout=timeout
        if self.diffStatus==stfutil.STOPPED:
            self.logger.info('start diff2 thread')
            p=threading.Thread(target=self.diff2)
            p.setDaemon(True)
            p.start() 
        def _diff():
            print ('screenShot put thread start')
            _cacheImg=b''
            timeout=time.time()+_timeout
            self.diffQ.put([baseTime,time.time(),baseline,position,method,name,'start'])
            while time.time()<timeout:
                # timestamp=time.time()
                timestamp=time.time()
                self.diffQ.put([timestamp,self.screen,name,'data'])
                # print (timestamp)
                time.sleep(0.001)
                # if  len(_cacheImg)!=len(self.screen):
                    # timestamp=time.time()
                    # self.diffQ.put([timestamp,self.screen,name,'data'])
                    # _cacheImg=self.screen
                    # print ('put',timestamp)
                # else:
                #     time.sleep(0.001)

            self.diffQ.put([baseTime,time.time(),name,'stop'])
            self.logger.info('qsize:%s'%self.diffQ.qsize())
        t=threading.Thread(target=_diff)
        t.setDaemon(True)
        t.start()
        
    def diff2(self,resize=0.3):
        _diffMap={}
        self.diffStatus=stfutil.STARTED
        _cache=b''
        def _diffImg(screen,screenshot_np,position,method):
            _isMatch=True

            x,y,x2,y2=position['x'],position['y'],position['x2'],position['y2']
            if method=='pixel':
                screen_np=cv2.imdecode(np.fromstring(self.screen, np.uint8),cv2.IMREAD_GRAYSCALE)
                if resize:
                    screen_np=cv2.resize(screen_np,None,fx=resize,fy=resize,interpolation=cv2.INTER_AREA)
                    x,y,x2,y2=int(x*resize),int(y*resize),int(x2*resize),int(y2*resize)
                # h,w=screen_np.shape

                screen_np=screen_np[y:y2,x:x2]
                screenshot_np=screenshot_np[y:y2,x:x2]
                diff_blend_img = cv2.absdiff(screen_np,screenshot_np)
                differenceArr=np.where(diff_blend_img>10)
                difference=np.sum(differenceArr)
                if difference>0:
                    # print (difference)
                    _isMatch= False
                else:
                    _isMatch= True

                # for yp in range(y,y2):
                #     for xp in range(x,x2):
                #         if self.diff_pixel(screen_np[yp,xp],screenshot_np[yp,xp],False):
                #             continue
                #         else:
                #             _isMatch=False
                #             break
                #     if not _isMatch:
                #         break
                # else:
                # print ('isMatch',_isMatch)


                return _isMatch
            else:
                screen_np=cv2.imdecode(np.fromstring(self.screen, np.uint8),cv2.IMREAD_COLOR)
                if resize:
                    screen_np=cv2.resize(screen_np,None,fx=resize,fy=resize,interpolation=cv2.INTER_AREA)
                    x,y,x2,y2=int(x*resize),int(y*resize),int(x2*resize),int(y2*resize)
                screenshot_np=screenshot_np[y:y2,x:x2]
                ret=ac.find_template(screen_np,screenshot_np)
                if not ret:
                    return False
                else:
                    print (ret)
                    confidence=ret['confidence']
                    if confidence<0.9:
                        return False
                    else:

                        return True


        while True:
            datas=self.diffQ.get()
            # continue
            if datas[-1]=='start':
                name=datas[-2]
                method=datas[4]
                if method=='pixel':
                    img=cv2.imdecode(np.fromstring(datas[2], np.uint8),cv2.IMREAD_GRAYSCALE)
                else:
                    img=cv2.imdecode(np.fromstring(datas[2], np.uint8),cv2.IMREAD_COLOR)
                if resize:
                    h,w=img.shape[0],img.shape[1]
                    img=cv2.resize(img,None,fx=resize,fy=resize,interpolation=cv2.INTER_AREA)                        
                _diffMap[name]={'baseline':img,'baseTime':datas[0],'act2':'data'}
                position=datas[3]
                position=json.loads(position)
                x,y=int(position['x']),int(position['y'])
                x2,y2=x+int(position['width']),y+int(position['height'])  
                _diffMap[name]['position']={'x':x,'y':y,'x2':x2,'y2':y2}  
                _diffMap[name]['method']=method
                print ('get start',self.diffQ.qsize())
                continue
            elif datas[-1]=='stop':
                name=datas[-2]
                # print ('get stop',n,n2)
                if not  _diffMap[name].get('result'):
                    baseTime=_diffMap[name]['baseTime']
                    self.__diffResponse({'res':False,'time':datas[1]-baseTime})
                    # print ('[diff timeout]',datas[1],datas[1]-baseTime)
                _diffMap.pop(datas[-2])
                continue
            else:
                name=datas[-2]
                if _diffMap[name].get('result'):
                    continue
                else:
                    currentImg=datas[1]

                    name=datas[-2]
                    res=_diffImg(currentImg,_diffMap[name].get('baseline'),_diffMap[name]['position'],_diffMap[name]['method'])
                    if res:
                        baseTime=_diffMap[name]['baseTime']
                        _diffMap[name]['result']=res
                        self.__diffResponse({'res':True,'time':datas[0]-baseTime})





        self.diffStatus=stfutil.STOPPED

    @property
    def getScreenShot2(self):
        # from cv2 import imdecode,CV_LOAD_IMAGE_COLOR
        from numpy import fromstring,uint8
        import cv2
        # import numpy as np
        if self.imgData:
            return self.imgData
            # try:
            #     # print (self.imgData)
            #     # print (np.uint8)
            #     arr = fromstring(self.imgData, dtype=uint8)
            #     # print ('a')
            #     img = cv2.imdecode(arr,cv2.IMREAD_COLOR)
            #     cv2.imshow("img_decode", img) 
            #     # print (arr)
            #     # if self.frameConfig.rotation/90 == 1:
            #     #     return cv2.flip(cv2.transpose(img), 0) # counter-clockwise
            #     # if self.frameConfig.rotation/90 == 3:
            #     #     return cv2.flip(cv2.transpose(img), 1) # clockwise
            #     return img
            # except Exception as e:
            #     print (str(e))
            #     return None
                
        else:
            return None

    @property
    def displayInfo(self):
        output=self.device.shell('LD_LIBRARY_PATH=/data/local/tmp/ /data/local/tmp/minicap -i').strip()
        try:
            displayInfo=eval(output.replace('true','True'))
            self.frameConfig=stfutil.FrameConfig(displayInfo['width'],displayInfo['height'],displayInfo['rotation'])
            return displayInfo
        except Exception as e:
            return None

    @property
    def status(self):
        return self.__runningStatus

    def __diffResponse(self,data):
        self.logger.info('MINICAP %s %s'%('diffResponse',data))
        self.handlers.notifyHandler({'event':'diffResponse','data':data})
    # status notify
    def __notify(self,event,data={}):
        self.logger.info('MINICAP %s %s'%(event,data))
        self.handlers.notifyHandler({'event':event,'data':data})

    def __getlogger(self):
        logger=logging.getLogger('[minicap:%s]'%self.device.serial)
        if not logger.handlers:
            formatter=logging.Formatter('%(asctime)s-%(filename)s:%(lineno)s-%(levelname)s---#%(name)s:%(message)s')
            stream_handler=logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
            logger.setLevel(logging.DEBUG)
        return logger

    def __getResourceInfo(self,deviceInfo):
        return {
            'bin':{
                'src':'mtp/vendor/minicap/bin/%s/minicap%s'%(deviceInfo.abi,deviceInfo.bin),
                'dest':'/data/local/tmp/minicap',
                'comm':'minicap',
                'mode':'' #0755 对应新版adb。。。待查
            },
            'lib':{
                'src':'mtp/vendor/minicap/shared/android-%s/%s/minicap.so'%(deviceInfo.sdk,deviceInfo.abi),
                'dest':'/data/local/tmp/minicap.so',
                'mode':''  #0755 对应新版adb。。。待查
            }
        }

    # check minicap resource is installed
    def __isInstalledMinicapResource(self):
        output=self.device.shell('ls "%s"'%self.resourceInfo['bin']['dest']).strip()
        return True if "No such file or directory" not in output else False

    # install minicap resource 
    def installMinicapResource(self,replace=False):
        if replace or not self.__isInstalledMinicapResource():
            res=self.device.push(self.resourceInfo['bin']['src'],self.resourceInfo['bin']['dest'])
            res2=self.device.push(self.resourceInfo['lib']['src'],self.resourceInfo['lib']['dest'])
            if res==True and res2==True:
                self.logger.debug('install minicap resource')
            else:
                raise MinicapError('minicap install failed')

    # check minicap service is started
    def __isStartedMinicap(self):
        output=self.device.shell('ps |grep %s |grep -v grep'%self.resourceInfo['bin']['comm']).strip()
        if not output:
            return None
        output = output.split('\n')
        if len(output)>1:
            pids=[o.split()[1] for o in output]
            self.logger.warning('get multi minicap pid%s'%pids)
            return pids
        else:
            return output[0].split()[1]

    # kill minicap service
    def __killminicap(self,pid=None):
        pid = pid if pid else self.__isStartedMinicap()
        if pid:
            if type(pid)==list:
                for subpid in pid:                    
                    self.device.shell('kill -9 %s'%subpid)
                    self.logger.debug('kill minicap service: %s'%subpid)
            else:
                self.device.shell('kill -9 %s'%pid)
                self.logger.debug('kill minicap service: %s'%pid)

    # start minicap service
    def __startMinicap(self):
        if not self.restartFlag:
            if not self.__isInstalledMinicapResource():
                raise MinicapError('minicap can not found')
            if self.__minicapProcess:
                self.__minicapProcess.kill()
            if not self.frameConfig:
                self.logger.debug('init displayInfo')
                output=self.device.shell('LD_LIBRARY_PATH=/data/local/tmp/ /data/local/tmp/minicap -i').strip()
                try:
                    displayInfo=eval(output.replace('true','True'))
                    self.frameConfig=stfutil.FrameConfig(int(displayInfo['width']),int(displayInfo['height']),displayInfo['rotation'])
                except Exception as e:
                    raise e
            self.__killminicap()
        self.__minicapProcess=self.device.shell('LD_LIBRARY_PATH=/data/local/tmp/ exec %s -P %s'%(self.resourceInfo['bin']['dest'],self.frameConfig),nowait=True)

    # adb forward socket connection
    def _adbForward(self,localPort):
        self.device.forward('tcp:%s'%localPort,'localabstract:minicap')
        self.logger.debug('add adb forward %s'%localPort)

    # remove forward socket connection
    def _removeAdbForward(self,localPort):
        self.device.forward_remove('tcp:%s'%localPort)
        self.logger.debug('remove adb forward %s'%localPort)        

    # connect minicap 
    def __connectMinicap(self):
        localPort = self.localPort or 1313
        _dataQ=queue.Queue()
        self._adbForward(localPort)

        # 当一些特殊情况下，例如横屏状态下锁屏，连接socket会得到空字符
        for i in range(10):
            _s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            _s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            time.sleep(0.08)
            _s.connect(('localhost',localPort))
            _banner=_s.recv(24)
            if _banner:break
            time.sleep(0.05)
        else:
            raise MinicapError('get empty socket data')
        self.__pid=struct.unpack('<BBIIIIIBB',_banner)[2]
        assert self.__pid,'minicap service pid not found'
        self.logger.debug('start minicap service: %s'%self.__pid)

        # recv data from socket
        def __recvdata():
            _isError=False
            self.recvStatus=stfutil.STARTED
            self.logger.debug('(recvdata thread): STARTED')
            try:
                timeout=self.timeout if self.timeout else 3600*240
                maxTime=time.time()+timeout
                while time.time()<maxTime:
                    data=_s.recv(4096)
                    if data:
                        # print (time.time(),_dataQ.qsize())
                        _dataQ.put(data)
                    else:
                        raise MinicapError('(recvdata thread): get empty socket data')
                else:
                    self.__notify('timeout :%s'%timeout)
                    raise MinicapError('(recvdata thread): minicap time out %ss'%timeout)
            except Exception as e:
                if not self.__runningStatus==stfutil.STOPPING:
                    _isError=True
                    if self.__minicapProcess.poll() is None:
                        self.__minicapProcess.kill()
                        self.logger.error('(recvdata thread): ERROR %s, kill minicap service myself'%str(e).strip())
                    else:
                        self.logger.debug('%s'%self.__minicapProcess.stdout.read())
                        self.logger.error('(recvdata thread): ERROR %s, minicap service dead'%str(e).strip())
            finally:
                self.logger.debug('(recvdata thread): STOPPED')
                self._removeAdbForward(localPort)
                self.recvStatus=stfutil.STOPPED
                _s.close()
            if _isError:
                self.__stopMinicap()

        t=threading.Thread(target=__recvdata)
        t.setDaemon(True)
        t.start()

        # get img from queue
        def __processdata():
            self.processStatus=stfutil.STARTED 
            self.logger.debug('(processdata thread): STARTED')
            readFrameBytes,frameBodyLength,frameBodyLengthStr,frameBody=0,0,b'',b''

            # parse img data
            def _getOneImageInfo(stream):
                nonlocal readFrameBytes,frameBodyLength,frameBodyLengthStr,frameBody
                for i,v in enumerate(stream):
                    if readFrameBytes<4:
                        frameBodyLengthStr+=stream[i:i+1]
                        if readFrameBytes==3:
                            frameBodyLength,=struct.unpack('<I',frameBodyLengthStr)
                        readFrameBytes+=1
                    else:
                        if len(stream)-i>=frameBodyLength:
                            frameBody+=bytes(stream[i:i+frameBodyLength])
                            self.handlers.dataHandler(frameBody)
                            if self.diffTurn:
                                stamptemp=time.time()
                                self.diffQ.put({'time':stamptemp,'data':frameBody,'act':1})
                            #     prin ('put',stamptemp,_dataQ.qsize(),time.time())
                            # print ('recv data',time.time())
                            self.screen=frameBody
                            temp=frameBodyLength
                            frameBody,frameBodyLengthStr,readFrameBytes,frameBodyLength=b'',b'',0,0
                            if i+temp<len(stream):
                                _getOneImageInfo(stream[i+temp:])
                        else:
                            frameBody+=bytes(stream[i:len(stream)])
                            readFrameBytes+=len(stream)-i
                            frameBodyLength-=len(stream)-i
                        break

            while self.recvStatus==stfutil.STARTED:
                try:
                    data=_dataQ.get(timeout=0.01)
                    _getOneImageInfo(data)
                except queue.Empty:
                    if self.__minicapProcess and self.__minicapProcess.poll() is None:
                        # time.sleep(0.1)
                        continue
                    else:
                        if not self.__runningStatus==stfutil.STOPPING:
                            self.logger.error('(processdata thread): ERROR minicap service already dead')
                        break
                except Exception as e:
                    traceback.print_exc()
                    self.logger.error('(processdata thread): ERROR processdata unKnown error %s'%e)
                    # break
            else:
                self.logger.debug('(processdata thread): ERROR recvdata thread already break')
            self.logger.debug('(processdata thread): STOPPED')
            self.processStatus=stfutil.STOPPED

        t=threading.Thread(target=__processdata)
        t.setDaemon(True)
        t.start()

    def __stopMinicap(self,pid=None):
        self.__killminicap(pid)
        self.__minicapProcess=None
        self.__pid=None
        for i in range(50):
            if self.processStatus==stfutil.STOPPED and self.recvStatus==stfutil.STOPPED and self.__runningStatus!=stfutil.STOPPED:          
                self.__runningStatus=stfutil.STOPPED
                self.__notify('STOPPED')
                break
            else:
                time.sleep(0.001)
        else:
            self.logger.warning("stop minicap timeout")

    def _ensureState(self):
        if self.desiredState.isEmpty():
            return
        if self.__runningStatus==stfutil.STARTING or self.__runningStatus==stfutil.STOPPING:
            self.logger.debug('WAIT')
            return 
        elif self.__runningStatus==stfutil.STOPPED:
            if self.desiredState.get()=='START':
                try:
                    self.__runningStatus=stfutil.STARTING
                    self.__startMinicap()
                    self.__connectMinicap()

                    self.__runningStatus=stfutil.STARTED
                    self.__notify('STARTED')
                except Exception as e:
                    if self.__runningStatus!=stfutil.STOPPED:
                        self.logger.error('minicap start failed: %s'%str(e))
                        self.__runningStatus=stfutil.STOPPING
                        self.__stopMinicap(self.__pid)
                finally:
                    self._ensureState()
            else:
                self.logger.warning('get STOP command but service is stopped')
        elif self.__runningStatus==stfutil.STARTED:
            if self.desiredState.get()=='STOP':
                try:
                    self.__runningStatus=stfutil.STOPPING
                    self.__stopMinicap(self.__pid)
                finally:
                    self._ensureState()
            else:
                self.logger.warning('get START command but service is started')


    def start(self):
        self.logger.info('MINICAP STARTING')
        self.desiredState.push('START')
        self._ensureState()

    def stop(self):
        self.logger.info('MINICAP STOPPTING')
        self.desiredState.push('STOP')
        self._ensureState()

    def restart(self):
        self.restartFlag=True
        st=time.time()
        self.stop()
        self.start()
        self.restartFlag=False
        print (time.time()-st,'total time')

    def updateRotation(self,rotation):
        if self.__runningStatus==stfutil.STOPPED:
            return
        if self.frameConfig.rotation==rotation:
            self.logger.debug('Keeping %d as current frame producer rotation'%rotation)
            return
        else:
            self.logger.debug('Setting frame producer rotation to %d'%rotation)
            self.frameConfig.rotation=rotation
            self.restart() #restart

    def updateConfig(self,width,height):
        if self.__runningStatus==stfutil.STOPPED:
            return
        if self.frameConfig.virtualWidth==width and self.frameConfig.virtualHeight==height:
            self.logger.debug('Keeping %dx%d as current frame producer projection'%(width,height))
            return
        else:
            self.logger.debug('Setting frame producer projection to %dx%d'%(width,height))
            self.frameConfig.virtualWidth=width
            self.frameConfig.virtualHeight=height
            self.restart() #restart

if __name__=='__main__':
    import time
    from adbkit import Adbkit
    serial='bc766a71'
    device=Adbkit().getDevice(serial)
    def fff(x):
        print ('getImg1')
    m=Minicap(device,fff)
    # print (m.isStartedMinicap())
    # m.killminicap()

    st=time.time()
    m.start()
    # m.connectMinicap(fff)
    time.sleep(30)
    print (time.time()-st)





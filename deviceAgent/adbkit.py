import os
import re
import sys
# from error import *
import time
import subprocess
# from error import AdbError
from collections import namedtuple

# from eventlet.green import subprocess
# import eventlet
# eventlet.monkey_patch()


# def run_cmd(cmd):
#     p=subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#     # return p.communicate()[0].replace('\r\n', '\n')
#     return p

class CmdKit():
    # wait 阻塞等待响应
    def run_sysCmd(self,cmd,**kwargs):
        p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if kwargs.pop('nowait',None):
            return p
        else:
            return p.communicate(timeout=kwargs.pop('timeout', 10))[0].decode('utf-8').replace('\r\n', '\n')

    # # no wait
    # def run_sysCmd_nowait(self,cmd):
    #     p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #     return p

class Adbkit(CmdKit):
    def __init__(self):
        super(Adbkit,self).__init__()

    def run_adbCmd(self,cmd,**kwargs):  
        cmd='adb %s'%(cmd)          # need add adb path
        return self.run_sysCmd(cmd,**kwargs)

    # def run_adbCmd_nowait(self,cmd):
    #     cmd='adb %s'%(cmd) 
    #     return self.run_sysCmd(cmd)

    def getPackageName(self,apkpath):
        output=self.run_sysCmd('aapt d badging %s |grep package'%apkpath)
        try:
            pattern = re.compile(r"package:\sname='(.+?)'")
            packageName=pattern.match(output).group(1)
        except:
            packageName=''
        finally:
            return packageName

    def getMainActicity(self,apkpath):
        output=self.run_sysCmd('aapt d badging %s |grep launchable-activity'%apkpath)
        try:
            pattern = re.compile(r"launchable-activity:\sname='(.+?)'")
            activity=pattern.match(output).group(1)
        except:
            activity=''
        finally:
            return activity    
    
    def getDevices(self):
        output=self.run_adbCmd('devices')
        return dict(re.findall('([^\s]+)\t(\w+)', output))

    def getAvailableDevices(self):
        devices=self.getDevices()
        availableDevices={}
        if devices:
            for k,v in devices.items():
                if v=='device':
                    availableDevices[k]=v
        return availableDevices

    def killAdbServer(self):
        output=self.run_adbCmd('kill-server')
        return output


    def startAdbServer(self):
        output=self.run_adbCmd('start-server')
        return output
    def getDevice(self,serial=None):
        devices=self.getDevices()
        if serial:
            if serial in devices.keys():
                return DeviceKit(self,serial)
            else:
                raise AdbError('Device %s not found.'%serial)
        else:

            if len(devices.keys())==1:
                return DeviceKit(self,list(devices.keys())[0])
            elif len(devices.keys())<1:
                raise AdbError('No availiable device.')
            else:
                raise AdbError('More than one device, Please set device serial.')

    def install(self,apkpath):
        if  self._run_deviceAdbCmd('install -rt %s'%apkpath).find('Success')>=0:
            return True
        else:
            return False


class DeviceKit():
    def __init__(self,adbkit,serial):
        # super(DeviceKit,self).__init__(serial)
        self.serial=serial
        self._adb=adbkit


    def _run_deviceAdbCmd(self,cmd,**kwargs):
        cmd='-s %s %s'%(self.serial,cmd)
        return self._adb.run_adbCmd(cmd,**kwargs)

    def forward(self,local,remote,**kwargs):
        cmd='-s %s forward %s %s'%(self.serial,local,remote)
        return self._adb.run_adbCmd(cmd,**kwargs)

    def forward_remove(self,local,**kwargs):
        cmd='-s %s forward --remove %s'%(self.serial,local)
        return self._adb.run_adbCmd(cmd,**kwargs)        

    def shell(self,cmd,**kwargs):
        cmd='shell %s'%cmd
        return self._run_deviceAdbCmd(cmd,**kwargs)


    def __getInfo(self):
        return self.shell("getprop")

    def __getInfoWithType(self,output,infoType):
        try:
            pattern=re.compile(r"[\s\S]*\[%s\]:\s\[(.+?)\]"%(infoType))
            res=pattern.match(output).group(1)
        except:
            res=""
        finally:
            return res

    @property
    def displayInfo(self):
        output=self.shell("LD_LIBRARY_PATH=/data/local/tmp/ /data/local/tmp/minicap -i")
        print (output)

    @property
    def screenSize(self):
        display=namedtuple('display', ['width', 'height'])
        output=self.shell("dumpsys window | grep -Eo 'init=\d+x\d+' | head -1 | cut -d= -f 2")
        output=output.strip().split('x') if output else []
        return display(output[0],output[1])

    @property
    def deviceInfo(self):
        info=namedtuple('info', ['serial', 'platform','manufacturer','operator','model','version','abi','sdk','bin','product','size'])
        output=self.__getInfo()
        manufacturer = self.__getInfoWithType(output,'ro.product.manufacturer').strip()
        operator=self.__getInfoWithType(output,'gsm.sim.operator.alpha').strip() or self.__getInfoWithType(output,'gsm.operator.alpha').strip()
        model=self.__getInfoWithType(output,"ro.product.model").strip()
        version=self.__getInfoWithType(output,"ro.build.version.release").strip()
        abi=self.__getInfoWithType(output,'ro.product.cpu.abi').strip()
        sdk=self.__getInfoWithType(output,'ro.build.version.sdk').strip()
        pie='' if sdk and int(sdk)>=16 else '-nopie'
        product=self.__getInfoWithType(output,'ro.product.name').strip()
        size='%sx%s'%(self.screenSize.width,self.screenSize.height)
        return info(self.serial,'Android',manufacturer,operator,model,version,abi,sdk,pie,product,size)

    def install(self,apkpath):
        output=self._run_deviceAdbCmd('install -rt %s'%apkpath)
        print (output)
        if output.find('Success')>=0:
            return True
        else:
            return False

    def uninstall(self,packageName):
        if self._run_deviceAdbCmd('uninstall %s'%packageName).find('Success')>=0:
            return True
        else:
            return False

    def push(self,localFile,remoteFile):
        output=self._run_deviceAdbCmd('push %s %s'%(localFile,remoteFile))
        print (output)
        if output.find('adb: error')>=0 or output.find('100%')<0:
            return False
        else:
            return True

    def pull(self,remoteFile,localFile):
        output=self._run_deviceAdbCmd('pull %s %s'%(remoteFile,localFile))
        print (output)
        if output.find('adb: error')>=0 or output.find('100%')<0:
            return False
        else:
            return True

    def getApkPath(self,packageName):
        output=self.shell('pm path %s'%(packageName))
        try:
            pattern = re.compile(r"package:(.+?)\n")
            path=pattern.match(output).group(1)
        except:
            path=''
        finally:
            return path




if __name__=='__main__':
    import time
    # test1('dadas')
    # print (Adbkit.startAdbServer())
    adb=Adbkit()
    d=adb.getDevice('bc766a71')
    o=d.shell("am startservice --user 0 \
    -a jp.co.cyberagent.stf.ACTION_START \
    -n jp.co.cyberagent.stf/.Service",nowait=False)
    print (o,)
    # print (a.getMainActicity('/Users/xz/Downloads/GT_2.2.6.5.apk2'))
    # d=a.getDevice('WEYDU17522001170')
    # info(serial='bc766a71', platform='Android', manufacturer='Hisense', operator='', model='Hisense E81', version='5.1.1', abi='arm64-v8a', sdk='22', bin='', product='E81', size='800x1280')
    # d=a.getDevice('WEYDU17522001170')
    # st=time.time()
    # path=d.getApkPath('com.tencent.wstt.gt')
    # print (path)
    # print (time.time()-st)
    # # print (d.shell('ls'))
    # # res=d.pull('/sdcard/gt.apk','/Users/xz/Downloads/GT_2.2.6.5.apk1')

    # st=time.time()
    # print (d.deviceInfo)
    # print (time.time()-st)
    # print (res)
    # print (a._call_adbCmd('-s','WEYDU17522001170','shell','ls'))
    # import distutils.spawn
    # print (dir(distutils))
    # print (distutils.spawn.find_executable("adb"))
    # print (type(run_cmd(['adb devices'])))
    # print (getDevices())
    # print (list('sd'))

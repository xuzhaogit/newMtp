import os
import re
import sys
from error import *
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

def getlogcat(serial):
    command="adb -s %s logcat"%serial
    p=subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        print (line)
def getDisplayInfo(serial):
    r=call_adb2("-s %s shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -i"%serial)
    try:
        d=eval(''.join(r[1]).replace('true','True'))
        return d
    except:
        return None
def launchApp(serial,package,activity):
    res=call_system('adb -s %s shell am start -n %s/%s'%(serial,package,activity))
    if res[0]==0 and res[1]:
        return res[1][0]
    else:
        return None     

def call_system(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    results=[]
    for line in p.stdout.readlines():  
        results.append(line.strip().decode('utf-8'))
        # print (results)
    retval = p.wait()
    return (retval,results)
def call_adb2(command):
    command_text = 'adb %s' % command
    # print (command_text)
    p = subprocess.Popen(command_text, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    results=[]
    for line in p.stdout.readlines():  
        results.append(line.strip().decode('utf-8'))
        # print (results)
    retval = p.wait()
    return (retval,results)
def call_adb_nowait(command):
    command_text = 'adb %s' % command
    p = subprocess.Popen(command_text, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print (p)
    return True
def exe_shell(serial,command):
    # print (command)
    res=call_adb_nowait("-s %s shell %s"%(serial,command))
    time.sleep(0.7)
    return res
def exe_shell2(serial,command):
    res=call_adb2("-s %s shell %s"%(serial,command))
def forward(serial,port,commn):
    res=call_adb2("-s %s forward tcp:%s localabstract:%s"%(serial,port,commn))
def forward_tcp(serial,port1,port2):
    res=call_adb_nowait("-s %s forward tcp:%s tcp:%s"%(serial,port1,port2))
    # print ("-s %s forward tcp:%s tcp:%s"%(serial,port1,port2))

def get_apk_path(serial,pkgname):
    res=call_adb2("-s %s shell pm path %s"%(serial,pkgname))
    # print (res)
    if res[0]==0 and res[1]:
        return res[1][0].split(':')[-1]
    else:
        return None
def install(serial,pkg):
    res=call_adb2("-s %s install -r %s"%(serial,pkg))
    return res
def uninstall(serial,packageName):
    res=call_adb2("-s %s uninstall %s"%(serial,packageName))
    return res
def install2(serial,localpkg):
    res=call_adb2("-s %s shell pm install -r %s"%(serial,localpkg))
    return res
def push(serial,src,dest,mode='0755'):
    res=call_adb2("-s %s push %s %s  %s"%(serial,src,dest,mode))
    return res
def rm(serial,dest,mode=''):
    res=call_adb2("-s %s shell rm %s %s"%(serial,mode,dest))
    return res
def mkdir(serial,targetdir):
    res=call_adb2("-s %s shell 'mkdir %s 2>/dev/null'"%(serial,targetdir))
    return res
def exists(serial,target):
    res=call_adb2("-s %s shell ls %s"%(serial,target))
    return res
def checkPid(serial,commn):
    res=call_adb2("-s %s shell ps %s"%(serial,commn))
    if len(res[1])<2:
        return None
    else:
        pids=[]
        for result in res[1][1:]:
            pid=result.split(' ')[5]
            pids.append(pid)
        return pids
def kill(serial,commn,mode=15):
    res=call_adb2("-s %s shell ps %s"%(serial,commn))
    if len(res[1])<2:
        return None
    else:
        pids=[]
        for result in res[1][1:]:
            pid=result.split(' ')[5]
            pids.append(pid)
            call_adb2("-s %s shell kill -%s %s"%(serial,mode,pid))
        return pids
def killPid(serial,pid,mode=15):
    call_adb2("-s %s shell kill -%s %s"%(serial,mode,pid))
def getSize(serial):
    res=call_adb2("-s %s shell dumpsys window | grep -Eo 'init=\d+x\d+' | head -1 | cut -d= -f 2"%serial)
    if res[1]:
        return res[1][0]
    else:
        w=call_adb2("-s %s shell dumpsys window | grep -Eo 'DisplayWidth=\d+' | head -1 | cut -d= -f 2"%serial)
        h=call_adb2("-s %s shell dumpsys window | grep -Eo 'DisplayHeight=\d+' | head -1 | cut -d= -f 2"%serial)
        return '%sx%s'%(w,h)
def check_services_Version(serial,apkpath,agentname):
    res=call_adb2("-s %s shell export CLASSPATH='%s'\;exec app_process /system/bin %s --version"%(serial,apkpath,agentname))
    if res[0]==0 and res[1]:
        return res[1][0]
    else:
        return None

def check_minicap():
    width = None
    height = None
    for i in subprocess.Popen("adb shell 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -i'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.readlines():
        i=i.decode()
        print (i)
        if 'secure' in i and 'true' in i:
            print('pushsdk:success')
        elif 'width' in i:
            width = i.strip().split(':')[1].strip().split(',')[0]
        elif 'height' in i:
            height = i.strip().split(':')[1].strip().split(',')[0]

    if width is not None:
        return width, height
    return width, height
if __name__=='__main__':
    pass
    # import distutils.spawn
    # print (dir(distutils))
    # print (distutils.spawn.find_executable("adb"))
    # print (os.environ)
    # print (check_minicap())
    # import platform
    # print (platform.system())
    # abi=get_abi('fa3fb4067d52')
    # print ('abi:',abi)
    # abi_fail=get_abi('fa3fb4067d521')
    # print ('abi_fail:',abi_fail)  
    # sdk=get_sdk('fa3fb4067d52')
    # print ('sdk:',sdk)
    # st=time.time()
    # infos=get_deviceInfo('fa3fb4067d52')
    # print (time.time()-st)
    # print (infos)
    # # res=kill('fa3fb4067d52','minicap')
    # print (res)
    # size=getSize('fa3fb4067d52')
    # print (size)
    # mkdir('fa3fb4067d52','/data/local/tmp/minicap-devel')
    # res=push('BY8HCQIZQSVS9PYS','/Users/xz/MTP/app/vendor/minitouch/arm64-v8a/minitouch','/data/local/tmp/minitouch','')
    # res2=rm('fa3fb4067d52','/data/local/tmp/minicap.so')
    # print (res2)
    # res3=get_apk_path('fa3fb4067d52','jp.co.cyberagent.stf')
    # print (res3)
    # check_services_Version('fa3fb4067d52','/data/app/jp.co.cyberagent.stf-2/base.apk','jp.co.cyberagent.stf.Agent')
    # kill('fa3fb4067d52','minicap')
    # res=exe_shell('fa3fb4067d52','LD_LIBRARY_PATH=%s exec %s %s'%('/data/local/tmp/','/data/local/tmp/minicap',"-P 720x1280@720x1280/0"))
    # res=exe_shell('fa3fb4067d52','exec %s'%'/data/local/tmp/minitouch')
    # print (res)
    # a=forward('fa3fb4067d52',1111,'minitouch')
    # print (a)
    # print (res)
    # d=get_devices()
    # # print (d)
    # res=getpackage('/tmp/uploadforder/20160530-xiaomi-release1473241450139.apk')
    # p=res.split("name='")[1].split("'")[0]
    # res=getActivity('/tmp/uploadforder/20160530-xiaomi-release1473241450139.apk')
    # a= res.split("name='")[1].split("'")[0]
    # # st=time.time()
    # # res2=install('fa3fb4067d52','/tmp/uploadforder/20160530-baidu-release.apk')
    # # print (res2[1][2])
    # print (p,a)
    # # print (time.time()-st)
    # res=launchApp(p,a)
    # print (res)
    # call_adb_nowait('devices')
    # res=getlogcat('fa3fb4067d52')
    # print (getDisplayInfo('fa3fb4067d52'))
    # res3=exists('fa3fb4067d52','/data/local/tmp/minicap-devel/testa.py')

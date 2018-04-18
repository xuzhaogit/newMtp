from .minicap import Minicap
from .minitouch import Minitouch
from .stfservice import STFService
from ..adbkit import adbkit
from queue import  Queue
from .. import socketio
import hashlib,time
from . error import STFKitError

# http://mqc.aliyun.com/remote_device.htm?f=%2F%2Fremotemqc.aliyun.com%2F%3Ftimestamp%3D1520561315262%26key%3DMTkyLjE2OC44LjEwNDo3MTAw%26sign%3D48b2e33856e8fac8d26acb7c03b47c76%26serialId%3D4df7b830050d30fb%26from%3Dmqc%26_tb_token_%3DA308wE5jlqn0FsJnaPezv3%23!%2Fsigcontrol%2F4df7b830050d30fb%2Fxuzhao_taobao%2F200%2F48b2e33856e8fac8d26acb7c03b47c76%2F22228%2F192.168.8.112

def stfManager(cls):  
    _instances = {}
    _minicap_q=Queue(50)
    _minitouch_q=Queue(50)
    _stfservices_q=Queue(50)
    for port in range(1300,1350):
        _minicap_q.put(port)
        _minitouch_q.put(port-100)
    for port in range(1100,1190,2):
        _stfservices_q.put(port)

    def bind(namespace,sid,ports):
        pass


    def _unbind(namespace):
        stf=_instances[namespace].get('cls')
        stf.minicap.stop()
        minicapLocalPort,minitouchLocalPort,stfserviceLocalport=_instances[namespace].get('ports')
        _minicap_q.put(minicapLocalPort)
        _minitouch_q.put(minitouchLocalPort)
        _stfservices_q.put(stfserviceLocalport)
        _instances.pop(namespace)


    def _getNameSpace(serial):
        m=hashlib.md5()   
        m.update(('%s%s'%(serial,time.time())).encode())  
        return  m.hexdigest()

    def _singleton(sid,**kwargs):
        for k in list(_instances.keys()):
            sids=_instances[k]['sids']
            if sids and sid in sids:
                if len(sids)==1:
                    _unbind(k)
                else:
                    _instances[k]['sids'].remove(sid)
            elif sids:
                pass
            else:
                _unbind(k)

        if kwargs.get('serial'):
            kwargs['ports']=(_minicap_q.get(),_minitouch_q.get(),_stfservices_q.get())
            kwargs['namespace']=_getNameSpace(kwargs['serial'])
            stf=cls(**kwargs)
            _instances[kwargs['namespace']] = {'cls':stf,'serial':serial,'ports':kwargs['ports'],'timeout':time.time()+60}
            return stf
        elif kwargs.get('namespace'):
            pass
        else:
            return None






        if not kwargs.get('serial'):
            namespace=kwargs.pop('namespace',None)
            if not namespace:raise STFKitError('namespace must be provide')
            if not  namespace in _instances:
                print (_instances)
                raise STFKitError('namespace %s not found '%(namespace))
            if kwargs.pop('kill',None):
                stfkit=_instances.get(serial)
                stfkit.minicap.stop()
                stfkit.minitouch.stop()
                stfkit.stfservice.stop()
                return None
            else:
                return _instances[namespace]
        else:
            kwargs['ports']=(_minicap_q.get(),_minitouch_q.get(),_stfservices_q.get())
            namespace=getNameSpace(kwargs['serial'])
            kwargs['namespace']=namespace
            _instances[namespace] = cls(**kwargs)
            return _instances[namespace]   
    return _singleton

@stfManager
class STFProvider():
    def __init__(self,**kwargs):
        self.device=adbkit.Adbkit().getDevice(kwargs.pop("serial"))
        self.namespace=kwargs.pop("namespace")
        self.ports=kwargs.pop('ports',None)
        minicapLocalPort,minitouchLocalPort,stfserviceLocalport=self.ports if self.ports else (None,None,None)
        class Handlers():
            notifyHandler=lambda data: socketio.emit('notify',data,namespace='/%s'%self.namespace)
            dataHandler=lambda data: socketio.emit('imgdata',data,namespace='/screen%s'%self.namespace)
            rotaionChangeHandler=lambda rotation:self.minicap.updateRotation(rotation)
        kwargs['handlers']=Handlers

        self.minicap=Minicap(self.device,localPort=minicapLocalPort,**kwargs)
        self.minitouch=Minitouch(self.device,localPort=minitouchLocalPort,**kwargs)
        self.stfservice=STFService(self.device,localPort=stfserviceLocalport,**kwargs)


    def initNotify(self):
        print ('initNotify',self.minicap.displayInfo)
        socketio.emit('initNotify',{'type':'initNotify','serial':self.device.serial,'deviceInfo':self.minicap.deviceInfo._asdict(),'displayInfo':self.minicap.displayInfo},namespace='/%s'%self.namespace)

    def startAll(self):
        self.minicap.start()
        self.minitouch.start()
        self.stfservice.start()

    def stopAll(self):
        self.minicap.stop()
        self.minitouch.stop()
        self.stfservice.stop()

    def installAll(self,replace=False):
        self.minicap.installMinicapResource(replace=True)
        self.minitouch.installMinitouchResource(replace=True)
        self.stfservice.installSTFserviceResource(replace=True)

    def getStatus(self):
        socketio.emit('statusNotify',{'type':'initNotify','serial':self.device.serial,'deviceInfo':self.minicap.deviceInfo._asdict(),'displayInfo':self.minicap.displayInfo},namespace='/%s'%self.namespace)

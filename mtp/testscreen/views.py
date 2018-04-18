from flask import render_template,redirect,url_for,request,jsonify,Response
from . import testscreen
from .. import socketio
# from ..openstf import minicap,minitouch
from ..adbkit import adbkit
from ..openstf import stfkit
 # monkey patch for minicap
import eventlet
# import cv2
import base64
import time,random
eventlet.monkey_patch()

# serial='bc766a71'
# device=adbkit.Adbkit().getDevice(serial)
# cap=minicap.Minicap(device,lambda data:socketio.emit('imgdata',data,namespace='/screen'))
# touch=minitouch.Minitouch(device)

# http://192.168.150.8:7889/testscreen/deviceview?serial=bc766a71


# socketio.emit('system','xzxzxz',namespace='/screen')


@testscreen.route('/devicelist')
def deviceList():
    return render_template('testscreen/deviceList.html')


@testscreen.route('/haha')
def haha():
    return render_template('testscreen/haha.html')


@testscreen.route('/deviceview')
def deviceview():
    serial=request.args.get('serial')
    namespace=stfkit.STFKit(serial=serial).namespace
    stfkit.STFKit(namespace=namespace).minitouch.start()
    stfkit.STFKit(namespace=namespace).stfservice.start()
    return redirect(url_for('.device',namespace=namespace))
    # return render_template('testscreen/deviceView.html')


@testscreen.route('/screenShot')
def screenShot():
    print ('screenShot')
    namespace=request.args.get('namespace')
    screenShot=stfkit.STFKit(namespace=namespace).minicap.getScreenShot()
    return base64.b64encode(screenShot)


@testscreen.route('/diff',methods=['POST'])
def diff():
    print ('diff',time.time())
    namespace=request.form.get('namespace')
    position=request.form.get('position')
    name=request.form.get('name')
    method=request.form.get('method')
    res=stfkit.STFKit(namespace=namespace).minicap.autoDiff('%s%s'%(name,random.randint(1,100)),position,method)
    return jsonify(result=res)

@testscreen.route('/diffScreen',methods=['POST'])
def diffScreen():
    print ('match start',time.time())
    namespace=request.form.get('namespace')
    debug=request.form.get('debug')
    position=request.form.get('position')
    res=stfkit.STFKit(namespace=namespace).minicap.diffScreen(position=position,debug=debug)
    return jsonify(result=res)


@testscreen.route('/matchScreen',methods=['POST'])
def matchScreen():
    print ('match start',time.time())
    namespace=request.form.get('namespace')
    position=request.form.get('position')
    debug=request.form.get('debug')
    res=stfkit.STFKit(namespace=namespace).minicap.diffScreen(method='match',position=position,debug=debug)
    return jsonify(result=res)




@testscreen.route('/device')
def device():
    return render_template('testscreen/deviceView.html')




@socketio.on('diff',namespace='/action')
def diffevent(json):
    namespace=json['namespace']
    position=json['position']
    name=json['name']
    method=json['method']
    # data=json['data']
    print ('get diff event',json)
    stfkit.STFKit(namespace=namespace).minicap.autoDiff('%s%s'%(name,random.randint(1,100)),position,method)
    # for namespace in namespaces:
    #     evalStr="stfkit.STFKit(namespace='%s').minitouch.%s(%s)"%(namespace,action,data)
    #     eval(evalStr)



@socketio.on('control',namespace='/action')
def control(json):
    print ('get control',json)
    namespace=json.get('namespace')
    action=json.get('action')
    t=json.get('type')
    data=json.get('data')
    if t=='stfkit':
        actionStr="stfkit.STFKit(namespace='%s').%s()"%(namespace,action)
    else:
        actionStr="stfkit.STFKit(namespace='%s').%s.%s()"%(namespace,t,action)
    eval(actionStr)


@socketio.on('touchEvent',namespace='/action')
def event(json):
    namespaces=json['namespaces']
    action=json['event']
    data=json['data']
    for namespace in namespaces:
        evalStr="stfkit.STFKit(namespace='%s').minitouch.%s(%s)"%(namespace,action,data)
        eval(evalStr)


@socketio.on('fff',namespace='/action')
def event(json):
    namespace=json['namespace']
    data=json['data']
    # for namespace in namespaces:
    evalStr="stfkit.STFKit(namespace='%s').minicap.updateRotation(%s)"%(namespace,data)
    eval(evalStr)


@socketio.on('serviceEvent',namespace='/action')
def event(json):
    namespaces=json['namespaces']
    action=json['event']
    data=json['data']
    for namespace in namespaces:
        evalStr="stfkit.STFKit(namespace='%s').stfservice.%s(%s)"%(namespace,action,data)
        eval(evalStr)

# @socketio.on('startMinitouch',namespace='/action')
# def startMinitouch(json):
#     print ('get touch start')
#     stfkit.STFKit(json['serial']).stfservice.start()

# @socketio.on('stopMinitouch',namespace='/action')
# def stopMinitouch(json):
#     print ('get touch stop')
#     stfkit.STFKit(json['serial']).stfservice.stop()

# @socketio.on('restartMinitouch',namespace='/action')
# def stopMinitouch(json):
#     print ('get touch restart')
#     stfkit.STFKit(json['serial']).stfservice.restart()
# @socketio.on('wake',namespace='/action')
# def stopMinitouch(json):
#     print ('get touch restart')
#     stfkit.STFKit(json['serial']).stfservice.wake()

# #keyPress
# @socketio.on('keyPress',namespace='/action')
# def keyPressHandler(json):
#     a=touch.sendServices(json['key'],'keyPress',json['data'])
# @socketio.on('keyUp',namespace='/action')
# def keyUpHandler(json):
#     a=touch.sendServices(json['key'],'keyUp',json['data'])
# @socketio.on('keyDown',namespace='/action')
# def keyDownHandler(json):
#     a=touch.sendServices(json['key'],'keyDown',json['data'])
# @socketio.on('type',namespace='/action')
# def typeHandler(json):
#     print (json)
#     a=touch.sendServices(json['key'],'type',json['data'])


# @socketio.on('wake',namespace='/action')
# def wakeHandler(json):
#     a=touch.sendServices(json['key'],'wake',json['data'])
# @socketio.on('rotate',namespace='/action')
# def rotateHandler(json):
#     a=touch.sendServices(json['key'],'rotate',json['data'])
# @socketio.on('getProperties',namespace='/action')
# def getPropertiesHandler(json):
#     a=touch.sendServices(json['key'],'getProperties',json['data'])
# @socketio.on('GetBrowsersRequest',namespace='/action')
# def GetBrowsersRequestHandler(json):
#     a=touch.sendServices(json['key'],'GetBrowsersRequest',json['data'])
# @socketio.on('setlockStatue',namespace='/action')
# def setlockStatueHandler(json):
#     a=touch.sendServices(json['key'],'setlockStatue',json['data'])

# class m():
#     @classmethod
#     def sendTouchs(cls,keys,action,data):
#         for serial in keys:
#             cls.sendTouch(serial,action,data)
#     @classmethod
#     def sendTouch(cls,serial,action,data):
#         r=stfkit.STFKit(serial).minitouch
#         if r:
#             eval('r.%s(data)'%action)
#             return 1
#         else:
#             return 0
# touch
# @socketio.on('gestureStart',namespace='/action')
# def gestureStartHandler(json):
#     namespaces=json['namespace']
#     action=json['event']
#     data=json['data']
#     for namespace in namespaces:
#         eval("stfkit.STFKit(namespace='%s').%s()"%(namespace,action))

#     if json['key']:
#         m.sendTouchs(json['key'],'gestureStart',json['data'])
# @socketio.on('gestureStop',namespace='/action')
# def gestureStopHandler(json):
#     m.sendTouchs(json['key'],'gestureStop',json['data'])
# @socketio.on('touchDown',namespace='/action')
# def touchDownHandler(json):
#     m.sendTouchs(json['key'],'touchDown',json['data'])
# @socketio.on('touchUp',namespace='/action')
# def touchUpHandler(json):
#     m.sendTouchs(json['key'],'touchUp',json['data'])
# @socketio.on('touchMove',namespace='/action')
# def touchMoveHandler(json):
#     m.sendTouchs(json['key'],'touchMove',json['data'])
# @socketio.on('touchCommit',namespace='/action')
# def touchCommitHandler(json):
#     m.sendTouchs(json['key'],'touchCommit',json['data'])
# @socketio.on('touchReset',namespace='/action')
# def touchResetHandler(json):
#     m.sendTouchs(json['key'],'touchReset',json['data'])
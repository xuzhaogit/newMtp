#!/usr/bin/env python
# from gevent import monkey
# monkey.patch_all()
from mtp import create_app,socketio
from flask_script import Manager



app=create_app('development')
manager=Manager(app)



@manager.command
def run():
    socketio.run(app,host='127.0.0.1',port=7889,debug=False)
    #app.run(host='192.168.160.212',port=7889,debug=False)

if __name__=='__main__':
    manager.run()

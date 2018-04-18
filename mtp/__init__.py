from flask import Flask
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO
from flask_redis import FlaskRedis
from config import config
from redis import StrictRedis

import time




class DecodedRedis(StrictRedis):
    @classmethod
    def from_url(cls, url, db=None, **kwargs):
        kwargs['decode_responses'] = True
        return StrictRedis.from_url(url, db, **kwargs)
bootstrap=Bootstrap()
socketio=SocketIO()

redis = FlaskRedis.from_custom_provider(DecodedRedis)

def create_app(config_name):
    app=Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    socketio.init_app(app)
    redis.init_app(app)


    from .testscreen import testscreen as testscreen_blueprint
    app.register_blueprint(testscreen_blueprint,url_prefix='/testscreen')

    from .providerHandle import ProviderHandler
    p=ProviderHandler(config[config_name])
    p.daemon=True
    p.start()
    return app
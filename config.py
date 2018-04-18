class Config():
    MQ_HOST = '10.2.1.67'
    MQ_PORT = 5672
    MQ_USER = 'admin'
    MQ_PWD = '123456'
    
    TEMPLATES_AUTO_RELOAD=True
    @staticmethod
    def init_app(app):
        pass



class DevConfig(Config):
    # BOOTSTRAP_SERVE_LOCAL=True
    REDIS_URL="redis://:@10.2.1.67/:6379/0"
    @classmethod
    def init_app(cls,app):
        Config.init_app(app)



config={'development':DevConfig}
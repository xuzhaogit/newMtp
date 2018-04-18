from config import Config
import pika


class RmqConnection():
    def getConnection(self):
        _credentials = pika.PlainCredentials(Config.MQ_USER,Config.MQ_PWD)
        connection = pika.BlockingConnection(pika.ConnectionParameters(Config.MQ_HOST,Config.MQ_PORT,'/',_credentials,heartbeat=60))
        return connection

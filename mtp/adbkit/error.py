class AdbError(Exception):
    def __init__(self,info=''):
        self.info=info
    def __str__(self):
        return 'AdbError:%s'%self.info
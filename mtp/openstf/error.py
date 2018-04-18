class STFserviceError(Exception):
    def __init__(self,info=''):
        self.info=info
    def __str__(self):
        return 'STFserviceError:%s'%self.info

class PbDecodeError(STFserviceError):
    pass


class MinicapError(Exception):
    def __init__(self,info=''):
        self.info=info
    def __str__(self):
        return 'MinicapError:%s'%self.info

class MinitouchError(Exception):
    def __init__(self,info=''):
        self.info=info
    def __str__(self):
        return 'MinitouchError:%s'%self.info


class STFKitError(Exception):
    def __init__(self,info=''):
        self.info=info
    def __str__(self):
        return 'STFKitError:%s'%self.info
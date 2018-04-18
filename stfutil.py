STARTED=3
STARTING=2
STOPING=4
STOPED=1

class StateQueue():
    def __init__(self):
        self.queue=[]
    def isEmpty(self):
        return len(self.queue)==0
    def push(self,data):
        for i,v in enumerate(self.queue):
            if v==data:
                self.queue=self.queue[:i+1]
                break
        else:
            self.queue.append(data)
    def get(self):
        if not self.isEmpty():
            return self.queue.pop(0)
        else:
            return None

class FrameConfig():
    def __init__(self,width,height,rotation):
        self.realWidth = width
        self.realHeight= height
        self.virtualWidth= width
        self.virtualHeight = height
        self.rotation=rotation
    def __str__(self):
        return '%sx%s@%sx%s/%d'%(self.realWidth,self.realHeight,self.virtualWidth,self.virtualHeight,self.rotation)

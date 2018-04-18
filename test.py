d={'a':1,'b':2,'c':4,'d':5}
print (d)
l=[1,2,3,4,1,2]



class Student():
    def __init__(self,name):
        self.name=name
    # def _
    def study(self):
        print (self)
        # pass
    @classmethod
    def func(cls):
        print (cls)


class Xs(Student):
    pass




st1=Student('zhangsan')
st2=Student('lisi')
# print (st1.name,st2.name,'asdda',123)
st1.func()
Student.func()
# print ('adsdad')
import threading,time

class abc(threading.Thread):
    def run(self):
        print ('abc')
        time.sleep(1)

t=abc()
t.start()
# t.start()
from struct import pack



class StreamHandler():
    def __init__(self):
        self._length,self._lengthIndex,self._temp=0,0,b''
        self._readingLength=True
        self.chunk=b''
    def delimitedStream(self,chunk):
        self.chunk+=chunk
        while (len(self.chunk)):
            if self._readingLength:
                b=self.chunk[0]
                self._length+=(b & 0x7f) << (7 * self._lengthIndex)
                if (b & (1<<7)):
                    self._lengthIndex += 1
                    self._readingLength = True
                else:
                    self._lengthIndex=0
                    self._readingLength=False
                self.chunk=self.chunk[1:]
            else:
                if self._length<=len(self.chunk):
                    self._temp+=self.chunk[:self._length]
                    self.chunk=self.chunk[self._length:]
                    self._length=0
                    self._readingLength = True
                else:
                    print ('break')
                    break
        return self._temp 


def delimitedStream(chunk):
    _length,_lengthIndex,_temp=0,0,b''
    _readingLength=True
    while (len(chunk)):
        if _readingLength:
            b=chunk[0]
            _length+=(b & 0x7f) << (7 * _lengthIndex)
            if (b & (1<<7)):
                _lengthIndex += 1
                _readingLength = True
            else:
                _lengthIndex=0
                _readingLength=False
            chunk=chunk[1:]
        else:
            if _length<=len(chunk):
                _temp+=chunk[:_length]
                chunk=chunk[_length:]
                _length=0
                _readingLength = True
            else:
                print ('break')
                break
    return _temp

def delimitingStream(chunk):
    _length=len(chunk)
    _temp=b''
    _b=[]
    while (_length > 0x7f):
        _b.append((1<<7)+(_length & 0x7f))
        _length>>=7
    _b.append(_length)
    _temp+=pack('<%sB'%len(_b),*_b)
    _temp+=chunk
    return _temp

if __name__=='__main__':
    from wire_pb2 import *
    n=StreamHandler()
    # test
    bbb=b"\xc1\x01\x10\x12\x1a\xbc\x01\x08\x00\x125\n\t\xe6\xb5\x8f\xe8\xa7\x88\xe5\x99\xa8\x12$com.android.browser/.BrowserActivity\x18\x00 \x01\x12;\n\x0c\xe6\x89\x8b\xe6\x9c\xba\xe7\x99\xbe\xe5\xba\xa6\x12'com.baidu.searchbox/.BoxBrowserActivity\x18\x00 \x00\x12D\n\x0c\xe6\x89\x8b\xe6\x9c\xba\xe6\xb7\x98\xe5\xae\x9d\x120com.taobao.taobao/com.taobao.tao.BrowserActivity\x18\x00 \x00"
    # bbb=b'\x04full\x12\x04good\x1a\x03usb d(d1\x00\x00\x00\x00\x00\x00@@9\x98n\x12\x83\xc0\xca\x10'
    bbb=b"+\x10\x0e\x1a'\n\x04full\x12\x04good\x1a\x03usb d(d1\x00\x00\x00\x00\x00\x00<@9\xcd\xcc\xcc\xcc\xcc\xcc\x10@\x12\x10\x0f\x1a\x0e\x08\x01\x12\x04WIFI\x1a\x00 \x00(\x00\x06\x10\x11\x1a\x02\x08\x00\x06\x10\r\x1a\x02\x08\x00"
    sss=delimitedStream(bbb)

    envelop=Envelope()
    envelop.ParseFromString(sss)
    print (envelop.type,envelop.message)
    # print (sss)


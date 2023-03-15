import exception
from exception import CodeNgu
import json
import time
import gzip
import os
import re
                    
class VectorStore(object):
    def __init__(self, name = None):
        self.list = []
        self.current = None
        self.name = name
        self.file = None

    def isInSegment(self):
        return self.current != None

    def addPoint(self, x, y)->None:
        if self.current == None:
            raise CodeNgu
        self.current.append((float(x),float(y)))

    def endSegment(self)->None:
        if self.current == None:
            raise CodeNgu
        if len(self.current) > 1:
            self.list.append(self.current)
        self.current = None

    def beginSegment(self, x, y)->None:
        if self.current != None:
            raise CodeNgu
        self.current = [(float(x),float(y))]

    def __repr__(self):
        return json.dumps(self.__dict__)

class VectorStoreFile(VectorStore):
    def __init__(self, fileName, path = None, temp = True):
        super().__init__()
        if path == None:
            path = os.getcwd()+'/'
        self.path = path
        self.fileName = fileName
        self.lastUpdate = None
        if not temp:
            self._load()
            self.lastUpdate = time.time()

    def _fullpath(self):
        if self.path == '/':
            return '/' + self.fileName

        if self.path == None:
            raise BadCode

        return self.path + '/' + self.fileName

    def saveAs(self, name = None, path = None):
        if name != None:
            self.fileName = name
        if path != None:
            self.path = path
        self._save()

    def _save(self):
        fd = gzip.open(self._fullpath(), mode = 'wb')
        assert not self.isInSegment()
        for segs in self.list:
            for seg in segs:
                s = "%s,%s|"%seg
                fd.write(s.encode())
            s ='\n'
            fd.write(s.encode())
        fd.close()
        self.lastUpdate = time.time()

    def _load(self):
        tmp = []
        try:
            fd = gzip.open(self._fullpath())
            for line in fd.readlines():
                line = line.decode().strip()
                segstrs = line.split("|")
                seg = []
                for segstr in segstrs:
                    xx = segstr.split(",")
                    if len(xx) != 2:
                        continue
                    seg.append((float(xx[0]), float(xx[1])))
                tmp.append(seg)
            fd.close()
            self.list = tmp
            self.lastUpdate = time.time()
        except gzip.BadGzipFile:
            raise FileSai

    def check(self):
        if self.lastUpdate == None:
            return "Temp"
        try:
            fd = os.open(self._fullpath(), os.O_RDONLY)
            stat = os.fstat(fd)
            os.close(fd)
        except os:
            return "Deleted"
        if stat.st_mtime > self.lastUpdate:
            return "Changed"
        return "Ok"

if __name__ == '__main__':
    vec = VectorStore()
    print(vec)
    vec.beginSegment(0,1)
    print(vec)
    vec.endSegment()
    print(vec)
    try:
        vec.addPoint(1,1)
    except:
        print("OK")
    print(vec)
    vec.beginSegment(0,0)
    vec.addPoint(1,1)
    vec.endSegment()
    print(vec)
    vec.beginSegment(0,0)
    vec.addPoint(1,1)
    vec.endSegment()
    print(vec)  

    print("Test2")
    vec1 = VectorStoreFile('a.dat')
    vec1.list = vec.list
    print(vec1)
    vec1._save()
    print("Test2load")
    vec1._load()
    print(vec1)
    print(vec1.check())

        

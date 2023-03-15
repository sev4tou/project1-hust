import cairo
import vector_store
from vector_store import VectorStore, VectorStoreFile
import threading

class VectorStoreManage(object):
    def __init__(self):
        self.list = []

    def openFile(self, name, path):
        ret = VectorStoreFile(name, path, False)
        self.list.append(ret)
        return ret
    
    def newTemp(self):
        i = ''
        while True:
            found = False
            for store in self.list:
                if store.fileName == 'new%s'%i:
                    found = True
                    break;
            if not found:
                ret = VectorStoreFile('new%s'%i)
                self.list.append(ret)
                return ret

            if i == '':
                i = 1
            else:
                i=i+1

class LogicFrame(object):
    def __init__(self, w=1000, h=1000, store = None):
        self.manager = VectorStoreManage()
        self.width = w
        self.height = h
        self.x, self.y, self.z = 0, 0, 1
        if store == None:
            store = self.manager.newTemp()
        self.store = store
        self.surface = None
        self.cairo = None
        self.lock = threading.Lock()
        self.redost = []

    def openStore(self, name, path):
        self.lock.acquire()
        try:
            store = self.manager.openFile(name, path)
            return len(self.manager.list) - 1
        finally:
            self.lock.release()
 
    def newStore(self):
        self.lock.acquire()
        try:
            store = self.manager.newTemp()
            return len(self.manager.list) - 1
        finally:
            self.lock.release()

    def switch(self, idd):
        self.lock.acquire()
        try:
            if idd < len(self.manager.list):
                self.store = self.manager.list[idd]
                self.repaint()
        finally:
            self.lock.release()

    def move(self, dx, dy):
        self.lock.acquire()
        try:
            self.x = dx*self.z + self.x
            self.y = dy*self.z + self.y
            self.repaint()
        finally:
            self.lock.release()
        
 
    def undo(self):
        self.lock.acquire()
        try:
            if not self.store.isInSegment():
                if len(self.store.list) != 0:
                    self.redost.append(self.store.list[-1])
                    self.store.list.pop()
                    self.repaint()
        finally:
            self.lock.release()

    def redo(self):
        self.lock.acquire()
        try:
            if not self.store.isInSegment():
                if len(self.redost) != 0:
                    seg = self.redost[-1]
                    self.cairo.set_source_rgb(1,1,1)
                    for x,y in seg:
                        self.cairo.line_to(x,y)
                    self.cairo.stroke()
                    self.store.list.append(seg)
                    self.redost.pop()
        finally:
            self.lock.release()

    def checkSurface(self):
        if self.surface == None:
            self.surface = cairo.ImageSurface(cairo.Format.A8, self.width, self.height)
            self.cairo = cairo.Context(self.surface)
            surface = self.surface

    def reTransform(self, x, y):
        return (x-self.x) / self.z,(y-self.y) / self.z

    def repaint(self):
        self.checkSurface()
        self.cairo.set_source_rgb(0,0,0)
        self.cairo.set_operator(cairo.OPERATOR_CLEAR)
        self.cairo.paint()
        self.cairo.set_operator(cairo.OPERATOR_ADD)
        self.cairo.set_source_rgb(1,1,1)
        for seg in self.store.list:
            for i,(x,y) in enumerate(seg):
                x,y = self.reTransform(x,y)
                if i != 0:
                    self.cairo.line_to(x,y)
                self.cairo.move_to(x,y)
        self.cairo.stroke()

    def setWidthHeight(self, x, y):
        self.lock.acquire()
        try:
            ox, oy = self.width, self.height
            if x != None:
                self.width = x
            if y != None:
                self.height = y
            if ox != self.width or oy != self.height:
                if self.surface != None:
                    self.cairo = None
                    self.surface.finish()
                self.surface = None
                self.repaint()
        finally:
            self.lock.release()

    def setxy(self, x, y):
        self.lock.acquire()
        try:
            ox, oy = self.x, self.y
            if x != None:
                self.x = x
            if y != None:
                self.y = y
            if ox != self.x or oy != self.y:   
                self.repaint()
        finally:
            self.lock.release()

    def setZoom(self, z):
        self.lock.acquire()
        try:
            if z != None and z != self.z:
                self.z = 1/z
                self.repaint()
        finally:
            self.lock.release()


    def addPoint(self, x, y):
        self.lock.acquire()
        try:
            px = self.x + (x * self.z)
            py = self.y + (y * self.z)

            self.cairo.set_source_rgb(1,1,1)
            self.cairo.line_to(x,y)
            self.cairo.stroke()
            self.cairo.move_to(x,y)
            self.store.addPoint(px, py)
        finally:
            self.lock.release()

    def beginSegment(self, x, y):
        self.lock.acquire()
        try:
            px = self.x + (x * self.z)
            py = self.y + (y * self.z)
             
            self.store.beginSegment(px,py)
            self.cairo.move_to(x, y)
            self.redost.clear()
        finally:
            self.lock.release()

    def endSegment(self):
        self.lock.acquire()
        try:
            self.store.endSegment()
        finally:
            self.lock.release()
             
if __name__ == '__main__':
    logic = LogicFrame()
    logic.setxy(10,10)
    logic.beginSegment(20,20)
    logic.addPoint(10,10)
    logic.endSegment()
    print(logic.store)

import numpy as np
import cv2
import pytesseract

class Test:
    def testImg(src : memoryview, wid, hei, lang = 'vie'):
        wid = int(len(src)/hei)
        data = np.ndarray(shape=(hei,wid), dtype=np.uint8, buffer=src)
        img = cv2.cvtColor(data,cv2.COLOR_GRAY2BGR)
        cv2.imwrite('test.png', img)
        return pytesseract.image_to_string(img, lang=lang, config='--psm 1')

import cv2 as cv
from typing import Dict
import numpy as np
ImageStore =Dict[str,np.ndarray]
class ImageDetector:
    def __init__(self):
        self.imageStore:ImageStore ={}
    def load_image(self, name:str,image_path:str):
        img=cv.imread(image_path,0)
        self.imageStore[name]=img
        return True
    def isImagePresent(self,name:str,frame:np.ndarray,threshold=0.9):
        frame=cv.cvtColor(frame,cv.COLOR_BGR2GRAY)
        imageToDetect=self.imageStore[name]

        result=cv.matchTemplate(frame,imageToDetect,cv.TM_CCOEFF_NORMED)
        min_val,max_val,min_loc,max_loc= cv.minMaxLoc(result)
        if(max_val>=threshold):
            return True
        return False
    def detectKO(self,name:str,frame:np.ndarray,threshold=0.9):
        frame=cv.cvtColor(frame,cv.COLOR_BGR2GRAY)
        frame=frame[110:300,60:580]
        cv.imshow("ASDasd",frame)
        cv.waitKey(0)
        edges=cv.Canny(frame,80,180)
        imageToDetect=self.imageStore[name]

        result=cv.matchTemplate(edges,imageToDetect,cv.TM_CCOEFF_NORMED)
        min_val,max_val,min_loc,max_loc= cv.minMaxLoc(result)
        print(max_val)
        if(max_val>=threshold):
            return True
        return False
    def countMatchingImages(self,name:str,frame:np.ndarray):
        frame=cv.cvtColor(frame,cv.COLOR_BGR2GRAY)
        imageToDetect=self.imageStore[name]
        h, w = imageToDetect.shape
        result=cv.matchTemplate(frame,imageToDetect,cv.TM_CCOEFF_NORMED)
        threshold = 0.8
        locations = np.where(result >= threshold)
        points = list(zip(*locations[::-1]))
        final_points = []
        for pt in points:
            if not final_points:
                final_points.append(pt)
                continue
            unique=True
            for (x,y) in final_points:
                difx=abs(pt[0]-x)
                diffy=abs(pt[1]-y)
                if(not(difx>w or diffy>h)):
                    unique=False
                    break
            if(unique):
                final_points.append(pt)
        return len(final_points)



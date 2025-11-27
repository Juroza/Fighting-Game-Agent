from windows_capture import WindowsCapture, Frame, InternalCaptureControl
import threading
import cv2 as cv
import numpy as np

class WindowCaptureWindows:
    def __init__(self,title,on_frame_callback,on_closed_callback):
        self.game_capture= WindowsCapture(window_name=title,cursor_capture=False)
        self.current_frame=None
        self.frameID=0
        self.lock=threading.Lock()
        self.on_frame_callback=on_frame_callback
        self.on_closed_callback=on_closed_callback
        self.stop_capture=False
        @self.game_capture.event
        def on_frame_arrived(frame: Frame, ctrl: InternalCaptureControl):
            if(frame is not None):
                bgr = frame.convert_to_bgr().frame_buffer
                h=bgr.shape[0]
                bgr_crop=bgr[51:h,]
                with self.lock:
                    self.current_frame=bgr_crop
                    self.frameID+=1
                if self.on_frame_callback is not None:
                    self.on_frame_callback(bgr_crop)#
            if(self.stop_capture):
                ctrl.stop()
                    
        @self.game_capture.event
        def on_closed():
            print("[Capture] Closed")
            if self.on_closed_callback is not None:
                    self.on_closed_callback()
        threading.Thread(target=self.game_capture.start,daemon=True).start()
    def set_on_frame_callback(self,func):
        self.on_frame_callback=func
    def set_on_closed_callback(self,func):
        self.on_closed_callback=func
    def preprocess_frame(self,frame:np.ndarray):
        gray= cv.cvtColor(frame,cv.COLOR_BGR2GRAY)
        shrink= cv.resize(gray, (84,84),interpolation=cv.INTER_AREA)
        normalise=shrink.astype(float)/255.0
        final= np.expand_dims(normalise,axis=0)
        return final

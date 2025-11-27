import os
from collections import deque
from dataclasses import dataclass
import threading
import subprocess, shlex, time
import vgamepad as vg
from .WindowCaptureWindows import WindowCaptureWindows
from pathlib import Path
import numpy as np
import win32gui
import win32process
import win32con,win32api
from .InputHandlerWindows import InputHandlerWindows,COMMANDS
from .ImageDetector import ImageDetector
from typing import Literal,List,get_args
from testDetectKO import is_ko_screen
import cv2 as cv
import ctypes
from ctypes import wintypes
import time
import time
import win32con
import os
import ctypes
import win32api
import re
@dataclass
class FrameData:
    frame:np.ndarray
    action:np.ndarray

os.makedirs("BC_DATASET", exist_ok=True)
def get_hwnds_for_pid(pid):
    hwnds = []

    def callback(hwnd, hwnds):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        if win32gui.IsWindow(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True

    win32gui.EnumWindows(callback, hwnds)
    return hwnds


def set_window_title_by_pid(pid, new_title):
    hwnds = get_hwnds_for_pid(pid)
    print(f"NEW PID {pid}")

    if not hwnds:
        print(f"No windows found for PID {pid}")
        return False

    for hwnd in hwnds:
        win32gui.SetWindowText(hwnd, new_title)

    return True
def get_window_title(pid):
    hwnds = get_hwnds_for_pid(pid)

    if not hwnds:
        print(f"No windows found for PID {pid}")
        raise Exception

    for hwnd in hwnds:
        return win32gui.GetWindowText(hwnd)

P1_HEALTH_REGION = (0.024, 0.09, 0.416, 0.005) 
#[  0 251  16] GREEN
#[  0 195 255] RED
# [  0 251 255] yellow
#APP_PID = wincap.get_pid() 
P2_HEALTH_REGION = (0.563, 0.09, 0.416, 0.005) 
P1_COMBO_REGION =  (0.14, 0.213, 0.14, 0.07) 
P2_COMBO_REGION =  (0.72, 0.213, 0.14, 0.07) 


P1_WIN_REGION = (0.35, 0.135, 0.10, 0.05) 
P2_WIN_REGION = (0.56, 0.135, 0.10, 0.05) 
WIN_ICONS= ["VICTORY_ICON", "SUPERWIN_ICON", "GUARDWIN_ICON","PERFECT_ICON"]
PERFECT_REWARD=50
WIN_REWARD=20
GUARDWIN_REWARD=30
SUPERWIN_REWARD=20
COMBO_REWARD=30
#[  0 251  16] GREEN
#[  0 195 255] RED
# [  0 251 255] yellow
HEALTH_COLORS=[(0 ,251 , 16),( 0, 195 ,255),(0, 251, 255)]
IMAGES = {
    "BOOT_SCREEN": r"images\booting.jpg",
    "START_SCREEN": r"images\sf3-logo.jpg",
    "CHAR_SELECT": r"images\1p-icon.jpg",
    "WINNER_SCREEN": r"images\winner.jpg",
    "OPPONENT_SELECT": r"images\oppen.png",
    "IN_GAME":r"images\99.png",
    "VICTORY_ICON": r"images\victoryIcon.png",
    "SUPERWIN_ICON": r"images\superWin.jpg",
    "GUARDWIN_ICON": r"images\gwa.jpg",
    "PERFECT_ICON":r"images\perfect.png",
    "COMBO_ICON":r"images\comboIcon.jpg"
}

time.sleep(3)
imageDetector= ImageDetector()
for image_name,path in IMAGES.items():
    if not imageDetector.load_image(image_name,path):
        print(f"Error loading {image_name}")
screens=("BOOT_SCREEN","START_SCREEN","CHAR_SELECT","OPPONENT_SELECT","IN_GAME")
SCREENSTYPE=Literal["BOOT_SCREEN","START_SCREEN","CHAR_SELECT","OPPONENT_SELECT","IN_GAME"]

def get_regionOfInterest(frame,region):
    H, W = frame.shape[:2]
    x = int(region[0]*W) 
    y = int(region[1]*H)
    w = int(region[2]*W)
    h = int(region[3]*H)
    return frame[y:y+h, x:x+w], (x,y,w,h)
class GameEnvironment:
    RETROARCH = r"C:\Users\jamai\Apps\retroarch.exe"
    CORE      = os.path.expanduser(r"C:\Users\jamai\Apps\cores\fbneo_libretro.dll")
    ROM       =  r"C:\Users\jamai\Documents\roms\fcade\sfiii3nr1.zip"
    pid=None
    window_capture=None
    p1Wins={"VICTORY_ICON":0,"SUPERWIN_ICON":0,"GUARDWIN_ICON":0,"PERFECT_ICON":0}
    p2Wins={"VICTORY_ICON":0,"SUPERWIN_ICON":0,"GUARDWIN_ICON":0,"PERFECT_ICON":0}
    p1WinsTotal=0
    p2WinsTotal=0
    inputHandler= InputHandlerWindows()
    
    
    start_time = time.time()
    x = 1 # displays the frame rate every 1 second
    counter = 500
    shotCount=0
    idx=0
    recordss:list[str]=[]
    def __init__(self, id,char:str):
        self.instance_id = id
        self.process = None
        self.stack_size = 4
        self.frame_stack = deque(maxlen=4)  
        self.player1_health=100
        self.player2_health=100
        self.player1win=0
        self.player2win=0
        self.controller=vg.VX360Gamepad()
        self.on_frame_arrived=None
        self.on_closed=None
        self.screen_state: SCREENSTYPE=None
        self.ROUND_OVER=False
        self.skipping_to_game= threading.Event()
        self.continuing_to_game= threading.Event()
        self.playing_game=threading.Event()
        self.behaviourCloningRecord:list[FrameData]= []
        self.totalBehaviourCloningRecord:list[FrameData]=[]
        self.p1Char=char
        time.sleep(2)
    def startInstance(self):
        self.window_title=f"RetroArch_{self.instance_id}"
        self.cfg_path = f"retroarch_instance_{self.instance_id}.cfg"
        print(f"MY CONTROLLER IS {self.controller.get_index()}")


        with open(self.cfg_path, "w") as f:
            f.write(
f"""video_fullscreen = "false"
video_windowed_fullscreen = "false"
pause_nonactive = "false"
input_driver = "sdl2"
input_autodetect_enable = "true"
input_max_users = "1"
input_player1_joypad_index = "{self.instance_id}"
video_window_title = "RetroArch_{self.instance_id}"
video_max_swapchain_images = "2"
video_frame_delay = "0"
video_swap_interval = "1"
audio_driver = "xaudio"
audio_enable = "true"
audio_mute_enable = "false"
audio_sync = "true"
audio_latency = "64"
""")

        cmd = f'"{self.RETROARCH}" -L "{self.CORE}" "{self.ROM}" --appendconfig "{self.cfg_path}"'
        self.proc = subprocess.Popen(shlex.split(cmd))
        print(f"Launched RetroArch instance {self.instance_id}, pid={self.proc.pid}")
        self.pid=self.proc.pid
        self.hwnds=get_hwnds_for_pid(self.pid)
        print(f"PID {self.pid}")
        time.sleep(2)
        #set_window_title_by_pid(self.pid,self.window_title)
        time.sleep(1)
        found=False
        while not found:
            try:
                if(get_window_title(self.pid)==self.window_title):
                    found=True  
                else:
                    set_window_title_by_pid(self.pid,self.window_title)
            except:
                set_window_title_by_pid(self.pid,self.window_title)
                time.sleep(2)
        self.window_capture=WindowCaptureWindows(self.window_title,self.on_frame_arrived,self.on_closed)
    def get_current_screen(self,frame:np.ndarray)->SCREENSTYPE:
        for screen in screens:
            if imageDetector.isImagePresent(screen,frame):
                return screen
        return "UNKNOWN_SCREEN"
    def closeInstance(self):
        self.window_capture.stop_capture=True
        self.proc.terminate()
    def fpsMeasure(self):
        def imp(frame):
            self.counter+=1
            if (time.time() - self.start_time) > self.x :
                print((f"FPS: { self.counter / (time.time() - self.start_time)}"))
                self.counter = 0
                self.start_time = time.time()
        self.window_capture.set_on_frame_callback(imp)
    def record(self):
        def imp(frame):
            #self.counter+=1
           #cv.imwrite(f"screenshots/{self.counter}.png",frame)
           self.countWins(frame)
        self.window_capture.set_on_frame_callback(imp)
    def recordFrameAndAction(self,frame:np.ndarray,action: np.ndarray):
        a= FrameData(frame=frame,action=action)
        self.behaviourCloningRecord.append(a)
    def pauseGame(self):
        self.inputHandler.tap('START',self.controller)
    def unpauseGame(self):
        self.inputHandler.tap('START',self.controller) 
    def saveRoundForBC(self,data:list[FrameData]):
        root=Path("BC_DATASET")
        continuingID=0
        for file in root.glob(f"{self.p1Char}*.npz"):
            name=re.split(r'-|\.', file.name)
            id=int(name[2])
            continuingID=max(continuingID,id)
        continuingID+=1
        print(continuingID)
        self.pauseGame()
        np.savez(f"{root}/{self.p1Char}-ROUND-{continuingID}.npz",
                frames=np.stack([framedata.frame for framedata in data],axis=0),
                actions=np.stack([framedata.action for framedata in data],axis=0)
                )
        self.unpauseGame()
        print("saved!") 
    def saveTotalRecordBC(self):
        print("SAVING")
        for record in self.totalBehaviourCloningRecord:
            self.saveRoundForBC(record)

        print("saveing done")
    def storeToTotalRecordBC(self):
        self.totalBehaviourCloningRecord.append(self.behaviourCloningRecord)
        self.behaviourCloningRecord=[]
    def getBCAction(self):
        return np.array(self.inputHandler.get_action_vector()[:10])
    def getHealth(self,frame:np.ndarray,player):
        if(player==1):
            strip=get_regionOfInterest(frame,P1_HEALTH_REGION)[0]
            strip= strip[0:1,:,:].copy()
            colour_health=strip[0][strip.shape[1]-1]
            colour_health=(colour_health[0],colour_health[1],colour_health[2])
            if(colour_health not in HEALTH_COLORS):
                return 0
            count=0
            for x in reversed(range(strip.shape[1])):
                pixel=strip[0,x]
                pixel_colour=(pixel[0],pixel[1],pixel[2])
                if(pixel_colour==colour_health):
                    count+=1
            return count/strip.shape[1]
        if(player==2):
            strip=get_regionOfInterest(frame,P2_HEALTH_REGION)[0]
            strip= strip[0:1,:,:].copy()
            colour_health=strip[0][0]
            colour_health=(colour_health[0],colour_health[1],colour_health[2])
            if(colour_health not in HEALTH_COLORS):
                return 0
            count=0
            for x in range(strip.shape[1]):
                pixel=strip[0,x]
                pixel_colour=(pixel[0],pixel[1],pixel[2])
                if(pixel_colour==colour_health):
                    count+=1
            return count/strip.shape[1]
    def readHealth(self):


        def imp(frame):
            p1_health=get_regionOfInterest(frame,P1_HEALTH_REGION)[0]
            p1_health_val=self.getHealth(p1_health,1)
            p2_health=get_regionOfInterest(frame,P2_HEALTH_REGION)[0]

            p2_health_val=self.getHealth(p2_health,2)
            cv.setWindowTitle("P1_HEALTH", f"P1 Health: {p1_health_val:.10f}")
            cv.setWindowTitle("P2_HEALTH", f"P2 Health: {p2_health_val:.10f}")
 
            
        self.window_capture.set_on_frame_callback(imp)
    def countWins(self,frame):
        self.p1WinsTotal=0
        self.p2WinsTotal=0
        p1_win_roi=get_regionOfInterest(frame,P1_WIN_REGION)[0]
        p2_win_roi=get_regionOfInterest(frame,P2_WIN_REGION)[0]
        for name,val in self.p1Wins.items(): 
            count=imageDetector.countMatchingImages(name,p1_win_roi)
            self.p1Wins[name]=count  
            self.p1WinsTotal+=count
        for name,val in self.p2Wins.items(): 
            count=imageDetector.countMatchingImages(name,p2_win_roi)
            self.p2Wins[name]=count 
            self.p2WinsTotal+=count     

                

    def skipToGame(self):
        self.skipping_to_game.clear()
        def imp(frame):
            print(f"here {self.get_current_screen(frame)}")
            match self.get_current_screen(frame):
                case "IN_GAME":
                    self.screen_state="IN_GAME"
                    self.window_capture.set_on_frame_callback(None)
                    self.skipping_to_game.set()
                    return
                case "BOOT_SCREEN" :
                    self.screen_state="BOOT_SCREEN"
                    self.inputHandler.tap('SELECT',self.controller)
                case "START_SCREEN":
                    self.screen_state="START_SCREEN"
                    self.inputHandler.tap('START',self.controller)
                case "CHAR_SELECT":
                    if(self.screen_state=="CHAR_SELECT"):
                        return
                    self.screen_state='CHAR_SELECT'
                    self.inputHandler.tap('DOWN',self.controller)
                    self.inputHandler.tap('LP',self.controller)
                    time.sleep(0.8)
                    self.inputHandler.tap('LP',self.controller)
                   
                case "OPPONENT_SELECT":
                    self.screen_state="OPPONENT_SELECT"
                    self.inputHandler.tap('DOWN',self.controller)
                    time.sleep(0.8)
                    self.inputHandler.tap('LP',self.controller)
                case "UNKNOWN_SCREEN":
                    self.counter+=1
                    self.inputHandler.tap('SELECT',self.controller)
                


        self.window_capture.set_on_frame_callback(imp)
        self.skipping_to_game.wait()






        



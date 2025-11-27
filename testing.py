import threading
from lib.GameEnvironment import GameEnvironment, FrameData
from model import Model
import vgamepad as vg
import time
import cv2 as cv
import argparse
import torch
import os
from pathlib import Path
import torch
from torch import optim
import numpy as np
import re
from testDetectKO import is_ko_screen
def get_args():
    parser = argparse.ArgumentParser(description="Test FG Agent")
    parser.add_argument("--char", type=str, default="RYU", help="Character to test (e.g., RYU, KEN, AKUMA)")
    parser.add_argument("--model", type=str, default=None, help="Load previous model")
    args = parser.parse_args()
    return args

def loadModel(path,device):
    data=torch.load(path,map_location=device)
    model=Model(1,10,256).to(device)
    model.load_state_dict(state_dict=data["model"])
    return model
def test(model:Model,device):
    playing_thread=threading.Event()
    continuing_to_game=threading.Event()
    stop_playing=threading.Event()
    gameEnv1=GameEnvironment(id=0,char="")
    gameEnv1.startInstance()
    gameEnv1.skipToGame()
    def stopRecording():
        playing_thread.set()
        continuing_to_game.set()
        stop_playing.set()
    gameEnv1.window_capture.set_on_closed_callback(stopRecording)
    def playingGame():
       playing_thread.clear()
       hidden_state,cell_state=model.init_hidden(1,device)
       def imp(frame): 
           if(is_ko_screen(frame)):
               gameEnv1.window_capture.set_on_frame_callback(None)
               playing_thread.set()
                          

               
           frame=torch.tensor(gameEnv1.window_capture.preprocess_frame(frame),device=device,dtype=torch.float32).unsqueeze(0)
           with torch.no_grad():
               actions_per_batch,log_prob_per_batch,state_value,(newh,newc)= model.act(frame,hidden_state,cell_state)
            
           action=actions_per_batch.squeeze(0).cpu().numpy().astype(int).tolist()
           action=action+[0,0]
           gameEnv1.inputHandler.execute_action(gameEnv1.controller,action)    

       print("Hello Wold")
       gameEnv1.window_capture.set_on_frame_callback(imp)
       playing_thread.wait()
    def continueGame():
        continuing_to_game.clear()
        print("savign round")
        gameEnv1.storeToTotalRecordBC()
        print("IN game again 3453")
        def imp(frame):
          gameEnv1.countWins(frame)
          if(gameEnv1.p2WinsTotal==2):
                gameEnv1.closeInstance()
          if(gameEnv1.get_current_screen(frame)=="IN_GAME"):
                gameEnv1.screen_state="IN_GAME"
                print("IN game again")
                gameEnv1.window_capture.set_on_frame_callback(None)
                continuing_to_game.set()
                return
          print("continue continue")
          gameEnv1.inputHandler.tap('DOWN',gameEnv1.controller)
          gameEnv1.inputHandler.tap('LP',gameEnv1.controller)
        gameEnv1.window_capture.set_on_frame_callback(imp)
        continuing_to_game.wait()
    while not stop_playing.is_set():
        if stop_playing.is_set():
            break
        playingGame()
        if stop_playing.is_set():
            break
        continueGame()

if __name__=="__main__":
    args= get_args()
    if torch.backends.mps.is_available():
        device=torch.device("mps")
    elif torch.cuda.is_available():
        device=torch.device("cuda")
    else:
        device=torch.device("cpu")
    if(args.model!=None):
        print("LPOADING")
        model=loadModel(args.model,device)
    else:
        print("Fresh")
        model=Model(1,10,256).to(device)
    test(model,device)

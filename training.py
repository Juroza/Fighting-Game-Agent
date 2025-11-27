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
def get_args():
    parser = argparse.ArgumentParser(description="Train FG Agent")
    parser.add_argument("--char", type=str, default="RYU", help="Character to train (e.g., RYU, KEN, AKUMA)")
    parser.add_argument("--model", type=str, default=None, help="Load previous model")
    parser.add_argument("--mode",type=str, default="TRAIN", help="TRAIN OR BC")
    args = parser.parse_args()
    return args

from testDetectKO import is_ko_screen
def loadRoundForBC(path):
        data=np.load(path)
        frames=data["frames"]
        actions=data["actions"]
        roundData=[]
        for f,a in zip(frames,actions):
            fd=FrameData(frame=f,action=a)
            roundData.append(fd)
        return roundData
def importRoundDataForChar(p1Char)->list[list[FrameData]]:
        root=Path("BC_DATASET")
        continuingID=0
        paths=[]
        for file in root.glob(f"{p1Char}*.npz"):
            paths.append(file)
        allData=[]
        for path in paths:
    
            data=loadRoundForBC(path)
            allData.append(data)
        return allData

class Options:
    lr = 1e-4
    gamma = 0.99
    tau = 1.0
    beta = 0.01
    epsilon = 0.2
    num_local_steps = 256
    num_epochs = 4
    max_episodes = 2
    epochs=40
    save_interval = 1
    save_path = r"C:\Users\jamai\Documents\Dev\FG agent\saved_models"
    model_path= None
    char= None
def BC(opt:Options):
     record_playing_thread=threading.Event()
     continuing_to_game=threading.Event()
     stop_playing=threading.Event()
     gameEnv1=GameEnvironment(id=0,char=opt.char)
     gameEnv1.startInstance()
     gameEnv1.skipToGame()
     def stopRecording():
        record_playing_thread.set()
        continuing_to_game.set()
        stop_playing.set()
     gameEnv1.window_capture.set_on_closed_callback(stopRecording)
     def recordPlaying():
       record_playing_thread.clear()
       def imp(frame): 
           # print("fef")
            
           # cv.imshow("capture",gameEnv1.window_capture.preprocess_frame(frame).squeeze())
           if(is_ko_screen(frame)):
                gameEnv1.window_capture.set_on_frame_callback(None)
                record_playing_thread.set()
           else:
                gameEnv1.recordFrameAndAction(gameEnv1.window_capture.preprocess_frame(frame),gameEnv1.getBCAction())
       print("Hello Wold")
       gameEnv1.window_capture.set_on_frame_callback(imp)
       record_playing_thread.wait()

     def continueGame():
        continuing_to_game.clear()
        print("savign round")
        gameEnv1.storeToTotalRecordBC()
        print("IN game again 3453")
        def imp(frame):
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
        recordPlaying()
        if stop_playing.is_set():
            break
        continueGame()
     gameEnv1.saveTotalRecordBC()
     print("FINISHED")
def saveModel(path,model:Model):
    data={
        "model":model.state_dict(),
        "optimiser": model.optimiser.state_dict(),
        "step_count":model.steps,
    }
    torch.save(data,path)
def loadModel(path,opt:Options,device):
    data=torch.load(path,map_location=device)
    model=Model(1,10,256).to(device)
    model.load_state_dict(state_dict=data["model"])
    model.setOptimiser(opt)
    model.optimiser.load_state_dict(state_dict=data["optimiser"])
    model.steps=data["step_count"]
    return model
def trainOnBCDataset(model:Model,opt:Options,device):
    model.train()
    model.setOptimiser(opt)
    loss_function= torch.nn.BCEWithLogitsLoss()  
    BCDataset= importRoundDataForChar(opt.char)
    for epoch in range(opt.epochs):
        total_loss=0
        for round in BCDataset:
            hidden_state,cell_state=model.init_hidden(1,device)
            round_loss=0
            for data in round:
                frame=torch.tensor(data.frame,device=device,dtype=torch.float32).unsqueeze(0)
                action=torch.tensor(data.action,device=device,dtype=torch.float32).unsqueeze(0)
                
                logits,_,(hidden_state,cell_state)=model(frame,hidden_state,cell_state)
                loss= loss_function(logits,action)
                round_loss+=loss
            model.optimiser.zero_grad()
            round_loss.backward()
            model.optimiser.step()
            model.steps+=1
            total_loss+=round_loss.item()
        print(f"Loss for run {epoch}={total_loss}")
    root=Path("saved_models")
    continuingID=0
    for file in root.glob(f"{opt.char}*.agent"):
        name=re.split(r'-|\.', file.name)
        id=int(name[1])
        continuingID=max(continuingID,id)
    continuingID+=1
    saveModel(f"saved_models/{opt.char}-{continuingID}.agent",model)

    
        
    
    
     
def train(model:Model,opt:Options):
     pass
if __name__ == "__main__":
    opt = Options()
    opt2= get_args()
    print(f"Training character {opt2.char}")
    opt.char=opt2.char
    opt.model=opt2.model
    os.makedirs(opt.save_path, exist_ok=True)
    if torch.backends.mps.is_available():
        device=torch.device("mps")
    elif torch.cuda.is_available():
        device=torch.device("cuda")
    else:
        device=torch.device("cpu")
    if(opt.model!=None):
        print("LPOADING")
        model=loadModel(opt.model,opt,device)
    else:
        model=Model(1,10,256).to(device)
        model.setOptimiser(opt)
    if(opt2.mode=="BC"):
       # BC(opt)
        trainOnBCDataset(model,opt,device)
    else:     
        train(model,opt)

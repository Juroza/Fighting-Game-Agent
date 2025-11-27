from typing import Literal
import vgamepad as vg
import win32api
import win32con
import time
COMMANDS = {
    "NEUTRAL": [0,0,0,0, 0,0,0, 0,0,0, 0,0],

    "UP":      [1,0,0,0, 0,0,0, 0,0,0, 0,0],
    "DOWN":    [0,1,0,0, 0,0,0, 0,0,0, 0,0],
    "LEFT":    [0,0,1,0, 0,0,0, 0,0,0, 0,0],

    "DOWN_RIGHT": [0,1,0,1, 0,0,0, 0,0,0, 0,0],
    "DOWN_LEFT":  [0,1,1,0, 0,0,0, 0,0,0, 0,0],
    "UP_RIGHT":   [1,0,0,1, 0,0,0, 0,0,0, 0,0],
    "UP_LEFT":    [1,0,1,0, 0,0,0, 0,0,0, 0,0],

    "LP": [0,0,0,0, 1,0,0, 0,0,0, 0,0],
    "MP": [0,0,0,0, 0,1,0, 0,0,0, 0,0],
    "HP": [0,0,0,0, 0,0,1, 0,0,0, 0,0],

    "LK": [0,0,0,0, 0,0,0, 1,0,0, 0,0],
    "MK": [0,0,0,0, 0,0,0, 0,1,0, 0,0],
    "HK": [0,0,0,0, 0,0,0, 0,0,1, 0,0],

    "SELECT": [0,0,0,0, 0,0,0, 0,0,0, 1,0],
    "START":  [0,0,0,0, 0,0,0, 0,0,0, 0,1],
    "RELEASE": [0,0,0,0, 0,0,0, 0,0,0, 0,0]
}
COMMANDTYPE=Literal[ "NEUTRAL",

    "UP",
    "DOWN",
    "LEFT",

    "DOWN_RIGHT",
    "DOWN_LEFT",
    "UP_RIGHT",
    "UP_LEFT",

    "LP",
    "MP",
    "HP",

    "LK",
    "MK",
    "HK",

    "SELECT",
    "START",
    "RELEASE"]
class InputHandlerWindows:
    def execute_action(self,controller:vg.VX360Gamepad,action:list[int]):
        if action[0]: 
            controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        else:
            controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
            

        if action[1]: 
            controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
        else:
            controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)

        if action[2]:
            controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        else:
            controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)

        if action[3]: 
            controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        else:
            controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)

        if action[4]: controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)   
        else:      controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)

        if action[5]: controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)   
        else:      controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)

        if action[6]: controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)  
        else:      controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)

        if action[7]: controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)   
        else:      controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)

        if action[8]: controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)   
        else:      controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

        if action[9]: controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)  
        else:      controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

        if action[10]: 
            controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)

        else:
            controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
        if action[11]: controller.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START)  #
        else:      controller.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START)


        controller.update()


    def get_action_vector(self):
        return [
            int(win32api.GetAsyncKeyState(ord('W')) != 0),
            int(win32api.GetAsyncKeyState(ord('S')) != 0),
            int(win32api.GetAsyncKeyState(ord('A')) != 0),
            int(win32api.GetAsyncKeyState(ord('D')) != 0),
            int(win32api.GetAsyncKeyState(ord('U')) != 0),
            int(win32api.GetAsyncKeyState(ord('I')) != 0),
            int(win32api.GetAsyncKeyState(ord('O')) != 0),
            int(win32api.GetAsyncKeyState(ord('J')) != 0),
            int(win32api.GetAsyncKeyState(ord('K')) != 0),
            int(win32api.GetAsyncKeyState(ord('L')) != 0),
            int(win32api.GetAsyncKeyState(win32con.VK_RSHIFT) != 0),
            int(win32api.GetAsyncKeyState(win32con.VK_RETURN) != 0),
        ]
    def tap(self,action:COMMANDTYPE,controller:vg.VX360Gamepad):
        
        self.execute_action(controller,COMMANDS[action])
        time.sleep(0.1)
        self.execute_action(controller,COMMANDS["RELEASE"])